# [역할] Celery 비동기 작업 등록용
import json
import logging

# [역할] 결과를 Redis Pub/Sub으로 WebSocket에 전달
import redis

# [역할] 기준 리뷰 / 후보 리뷰 조회용
from apps.reviews.models import Review
from celery import shared_task

# [역할] 작업 시작/종료 시간 저장용
from django.utils import timezone

# [핵심] pgvector 거리 계산 함수
# DB 안에서 embedding 간 코사인 거리 계산할 때 사용
from pgvector.django import CosineDistance

# [역할] FastAPI 요청 실패 시 재시도 처리용
from requests import RequestException

# [역할]
# - AIAnalysisTask: 작업 상태 저장
# - ReviewEmbedding: 리뷰별 벡터 저장
# - ReviewSimilarityResult: 유사도 결과 저장
from .models import AIAnalysisTask, ReviewEmbedding, ReviewSimilarityResult

# [역할] FastAPI 임베딩 API 호출용
from .services import FastAPIClient

# logger 생성 (파일 상단에 1번만)
logger = logging.getLogger(__name__)


# [보조 함수]
# 유사도 점수를 사람이 보기 쉬운 문구로 바꿔줌
def get_similarity_label(score: float) -> str:
    if score > 0.7:
        return "매우 비슷"
    if score > 0.5:
        return "비슷"
    if score > 0.3:
        return "약간 비슷"
    return "관련 있음"


@shared_task(
    bind=True,
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def analyze_review_similarity_task(
    self, review_id: int, requested_by_id: int | None = None
):
    """
    [전체 역할]
    1. 기준 리뷰 조회
    2. 기준 리뷰 임베딩 생성 후 DB 저장
    3. 후보 리뷰 임베딩이 없으면 생성 후 DB 저장
    4. pgvector로 DB 내부 유사도 검색
    5. 결과 저장
    6. Redis publish로 WebSocket 클라이언트에게 알림
    """

    MODEL_NAME = "upskyy/e5-small-korean"
    SIMILARITY_THRESHOLD = 0.45

    # task 시작 로그
    logger.info(f"[START] Task 시작 | task_id={self.request.id} review_id={review_id}")

    # Redis 연결 객체 생성
    # Docker Compose에서 서비스명이 redis 라면 host='redis' 사용
    redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

    # [역할] 현재 Task 상태를 DB에 기록
    task_status = AIAnalysisTask.objects.get(task_id=self.request.id)
    task_status.status = AIAnalysisTask.STATUS_STARTED
    task_status.started_at = timezone.now()
    task_status.error_message = ""
    task_status.save(update_fields=["status", "started_at", "error_message"])

    try:
        # 1) 기준 리뷰 조회
        source_review = Review.objects.select_related("user", "product").get(
            id=review_id,
            is_public=True,
        )

        # source 리뷰 로그
        logger.info(f"[SOURCE] 기준 리뷰 조회 완료 | review_id={source_review.id}")

        # [예외 처리]
        # 기준 리뷰 내용이 비어 있으면 작업 실패 처리 대상
        if not source_review.content or not source_review.content.strip():
            raise ValueError("분석할 리뷰 내용이 없습니다.")

        # 2) 기준 리뷰 임베딩 생성 후 DB 저장
        # [핵심]
        # FastAPI에 텍스트를 보내서 384차원 벡터를 받아옴
        source_embedding = FastAPIClient.get_embedding(source_review.content)

        # [핵심]
        # ReviewEmbedding 테이블에 기준 리뷰 벡터 저장
        # 이미 있으면 update, 없으면 create
        ReviewEmbedding.objects.update_or_create(
            review=source_review,
            defaults={"embedding": source_embedding},
        )
        logger.info(
            f"[EMBED] 기준 리뷰 임베딩 저장 완료 | review_id={source_review.id}"
        )

        # 3) 같은 상품의 다른 리뷰들 조회
        candidate_reviews = (
            Review.objects.select_related("user")
            .filter(
                product=source_review.product,
                is_public=True,
            )
            .exclude(id=source_review.id)
            .order_by("-created_at")[:20]
        )

        candidate_count = candidate_reviews.count()

        # 후보 개수 로그
        logger.info(f"[CANDIDATES] 후보 리뷰 개수={candidate_count}")

        task_status.candidate_count = candidate_count
        task_status.save(update_fields=["candidate_count"])

        # 4) 후보 리뷰 임베딩 생성 및 저장
        # [중요]
        # 여기서의 for문은 "비교"를 위한 for문이 아니라
        # "아직 벡터가 없는 후보 리뷰들에 대해 임베딩을 생성/저장"하기 위한 for문
        for candidate in candidate_reviews:

            # [예외 처리] 빈 본문은 건너뜀
            if not candidate.content or not candidate.content.strip():
                continue

            # [역할] 이미 임베딩이 있으면 재생성하지 않음 (캐싱 효과)
            exists = ReviewEmbedding.objects.filter(review=candidate).exists()
            if exists:
                continue

            # [역할] FastAPI에서 후보 리뷰 임베딩 생성
            candidate_embedding = FastAPIClient.get_embedding(candidate.content)

            # [역할] 후보 리뷰 벡터를 DB에 저장
            ReviewEmbedding.objects.create(
                review=candidate,
                embedding=candidate_embedding,
            )
            logger.info(f"[EMBED] 후보 리뷰 임베딩 생성 | candidate_id={candidate.id}")

        # 5) pgvector로 유사 리뷰 검색
        # [핵심]
        # 이제부터는 Python에서 하나씩 비교하는 것이 아니라
        # DB가 embedding 컬럼끼리 코사인 거리를 계산함
        similar_embedding_rows = (
            ReviewEmbedding.objects.select_related("review", "review__user")
            .exclude(review_id=source_review.id)
            .filter(review__product=source_review.product)
            # [핵심] DB 내부에서 벡터 거리 계산
            .annotate(distance=CosineDistance("embedding", source_embedding))
            # [핵심] 거리 작은 순 = 더 비슷한 순
            .order_by("distance")[:3]
        )

        results = []

        # 6) 검색 결과를 점수화하고 결과 테이블에 저장
        for item in similar_embedding_rows:
            compared_review = item.review

            # [역할]
            # 코사인 거리(distance)를 유사도 점수(score)로 변환
            # distance가 작을수록 비슷하므로 1 - distance 사용
            score = round(float(1 - item.distance), 4)

            # [필터링]
            # 기준 점수 미만이면 결과에서 제외
            if score < SIMILARITY_THRESHOLD:
                continue

            # [라벨 생성]
            similarity_label = get_similarity_label(score)

            # 유사도 결과 저장
            # 이미 있으면 갱신, 없으면 생성
            saved_result, _ = ReviewSimilarityResult.objects.update_or_create(
                source_review=source_review,
                compared_review=compared_review,
                model_name=MODEL_NAME,
                defaults={
                    "product": source_review.product,
                    "requested_by_id": requested_by_id,
                    "similarity_score": score,
                    "similarity_label": similarity_label,
                    "similarity_threshold": SIMILARITY_THRESHOLD,
                    "source_review_snapshot": source_review.content,
                    "compared_review_snapshot": compared_review.content,
                    "compared_username_snapshot": compared_review.user.username,
                },
            )

            logger.info(
                f"[SAVE] 유사도 저장 | compared_review_id={compared_review.id} score={score}"
            )
            results.append(
                {
                    "analysis_id": saved_result.id,
                    "review_id": compared_review.id,
                    "username": compared_review.user.username,
                    "content": compared_review.content,
                    "score": score,
                    "label": similarity_label,
                    "created_at": compared_review.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        # 점수 높은 순으로 정렬
        results.sort(key=lambda x: x["score"], reverse=True)

        # 상위 3개만 선택
        top_results = results[:3]

        # 7) Task 완료 상태 저장
        task_status.status = AIAnalysisTask.STATUS_SUCCESS
        task_status.result_count = len(top_results)
        task_status.finished_at = timezone.now()
        task_status.save(update_fields=["status", "result_count", "finished_at"])

        logger.info(
            f"[SUCCESS] Task 완료 | 결과 수={len(top_results)} task_id={self.request.id}"
        )

        # 8) 프론트로 보낼 응답 데이터 구성
        response_data = {
            "source_review": {
                "review_id": source_review.id,
                "username": source_review.user.username,
                "content": source_review.content,
            },
            "similar_reviews": top_results,
            "candidate_count": candidate_count,
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "model_name": MODEL_NAME,
            "task_id": self.request.id,
            "status": "SUCCESS",
        }

        # 9) Redis Pub/Sub으로 결과 전송
        # [역할]
        # WebSocket 서버가 이 채널을 구독하고 있다가
        # 프론트 화면에 실시간 전달할 수 있음
        logger.info(f"[REDIS] 결과 publish | channel=task_result_{self.request.id}")
        redis_client.publish(
            f"task_result_{self.request.id}",
            json.dumps(response_data, ensure_ascii=False),
        )

        return response_data

    except Exception as e:
        # 10) 실패 처리
        logger.exception(
            f"[ERROR] Task 실패 | task_id={self.request.id} error={str(e)}"
        )

        task_status.status = AIAnalysisTask.STATUS_FAILURE
        task_status.error_message = str(e)
        task_status.finished_at = timezone.now()
        task_status.save(update_fields=["status", "error_message", "finished_at"])

        error_data = {
            "task_id": self.request.id,
            "status": "FAILURE",
            "error": str(e),
        }

        # 실패 신호도 Redis publish
        redis_client.publish(
            f"task_result_{self.request.id}",
            json.dumps(error_data, ensure_ascii=False),
        )

        raise
