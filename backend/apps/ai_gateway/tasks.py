# [추가] FastAPI 호출 + 결과 저장을 Celery worker로 분리

from celery import shared_task
from django.utils import timezone
from requests import RequestException

from apps.reviews.models import Review
from .models import ReviewSimilarityResult, AIAnalysisTask
from .services import FastAPIClient


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
    retry_kwargs={"max_retries": 3}
)
def analyze_review_similarity_task(self, review_id: int, requested_by_id: int | None = None):
    """
    [역할]
    기준 리뷰 1개를 기준으로 같은 상품의 다른 리뷰들과 유사도 분석 후
    결과를 DB에 저장하는 Celery 비동기 작업

    [전체 흐름]
    1. task_id로 AIAnalysisTask 상태 레코드 조회
    2. 작업 상태를 STARTED로 변경
    3. 기준 리뷰 조회
    4. 같은 상품의 비교 후보 리뷰 조회
    5. 후보 리뷰들을 FastAPI로 하나씩 비교
    6. 기준 점수 이상인 결과만 ReviewSimilarityResult에 저장
    7. 상위 결과를 정렬해서 반환
    8. 작업 성공/실패 상태를 AIAnalysisTask에 저장
    """

    # [상수]
    # 현재 사용하는 모델명과 유사도 기준값
    MODEL_NAME = "upskyy/e5-small-korean"
    SIMILARITY_THRESHOLD = 0.45

    # [1] 현재 Celery task_id로 작업 상태 레코드 조회
    task_status = AIAnalysisTask.objects.get(task_id=self.request.id)

    # [2] 작업 시작 상태로 변경
    task_status.status = AIAnalysisTask.STATUS_STARTED
    task_status.started_at = timezone.now()
    task_status.error_message = ""
    task_status.save(update_fields=["status", "started_at", "error_message"])

    try:
        # [3] 기준이 되는 리뷰 1개 조회
        source_review = Review.objects.select_related("user", "product").get(
            id=review_id,
            is_public=True,
        )

        # [예외 처리]
        # 기준 리뷰 내용이 비어 있으면 작업 실패 처리 대상
        if not source_review.content.strip():
            raise ValueError("분석할 리뷰 내용이 없습니다.")

        # [4] 같은 상품의 다른 리뷰들을 비교 후보로 조회
        candidate_reviews = (
            Review.objects
            .select_related("user")
            .filter(
                product=source_review.product,
                is_public=True,
            )
            .exclude(id=source_review.id)
            .order_by("-created_at")[:20]
        )

        # [5] 비교 후보 개수 기록
        task_status.candidate_count = candidate_reviews.count()
        task_status.save(update_fields=["candidate_count"])

        # [6] 최종 결과를 담을 리스트
        results = []

        # [7] 후보 리뷰들을 하나씩 순회하며 FastAPI 유사도 분석 수행
        for candidate in candidate_reviews:

            # [건너뛰기]
            # 후보 리뷰 내용이 비어 있으면 분석하지 않음
            if not candidate.content.strip():
                continue

            # [FastAPI 호출]
            # 기준 리뷰와 후보 리뷰의 유사도 계산
            similarity_result = FastAPIClient.get_similarity(
                source_review.content,
                candidate.content,
            )

            # [점수 추출]
            score = round(similarity_result["similarity"], 4)

            # [필터링]
            # 기준 점수 미만이면 결과에서 제외
            if score < SIMILARITY_THRESHOLD:
                continue

            # [라벨 생성]
            similarity_label = get_similarity_label(score)

            # [8] 최종 유사도 결과를 DB에 저장 또는 갱신
            saved_result, _ = ReviewSimilarityResult.objects.update_or_create(
                source_review=source_review,
                compared_review=candidate,
                model_name=MODEL_NAME,
                defaults={
                    "product": source_review.product,
                    "requested_by_id": requested_by_id,
                    "similarity_score": score,
                    "similarity_label": similarity_label,
                    "similarity_threshold": SIMILARITY_THRESHOLD,
                    "source_review_snapshot": source_review.content,
                    "compared_review_snapshot": candidate.content,
                    "compared_username_snapshot": candidate.user.username,
                }
            )

            # [9] 프론트에 반환할 결과 형태로 리스트에 추가
            results.append({
                "analysis_id": saved_result.id,
                "review_id": candidate.id,
                "username": candidate.user.username,
                "content": candidate.content,
                "score": score,
                "label": similarity_label,
                "created_at": candidate.created_at.strftime("%Y-%m-%d %H:%M"),
            })

        # [10] 점수 높은 순으로 정렬
        results.sort(key=lambda x: x["score"], reverse=True)

        # [11] 상위 3개만 선택
        top_results = results[:3]

        # [12] 작업 성공 상태 저장
        task_status.status = AIAnalysisTask.STATUS_SUCCESS
        task_status.result_count = len(top_results)
        task_status.finished_at = timezone.now()
        task_status.save(update_fields=["status", "result_count", "finished_at"])

        # [13] 최종 결과 반환
        return {
            "source_review": {
                "review_id": source_review.id,
                "username": source_review.user.username,
                "content": source_review.content,
            },
            "similar_reviews": top_results,
            "candidate_count": candidate_reviews.count(),
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "model_name": MODEL_NAME,
            "task_id": self.request.id,
            "status": "SUCCESS",
        }

    except Exception as e:
        # [실패 처리]
        # 작업 실패 시 상태, 에러 메시지, 종료 시각 저장
        task_status.status = AIAnalysisTask.STATUS_FAILURE
        task_status.error_message = str(e)
        task_status.finished_at = timezone.now()
        task_status.save(update_fields=["status", "error_message", "finished_at"])

        # [예외 다시 발생]
        # Celery가 실패로 인식하도록 예외를 다시 올림
        raise