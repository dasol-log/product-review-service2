from requests import RequestException


from django.shortcuts import get_object_or_404   
# [추가] review_id로 기준 리뷰 1개를 안전하게 조회하기 위해 추가

from apps.reviews.models import Review          
# [추가] DB에서 리뷰를 조회하기 위해 추가

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import EmbeddingRequestSerializer, SimilarityRequestSerializer
from .services import FastAPIClient


class EmbeddingAPIView(APIView):
    def post(self, request):
        serializer = EmbeddingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        texts = serializer.validated_data["texts"]

        try:
            # 현재 구조 유지: 한 문장씩 보내서 리스트로 반환
            embeddings = [FastAPIClient.get_embedding(text) for text in texts]
            return Response({"embeddings": embeddings}, status=status.HTTP_200_OK)
        except RequestException as e:
            return Response(
                {"detail": f"FastAPI 호출 실패: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class SimilarityAPIView(APIView):
    def post(self, request):
        serializer = SimilarityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text1 = serializer.validated_data["text1"]
        text2 = serializer.validated_data["text2"]

        try:
            result = FastAPIClient.get_similarity(text1, text2)
            return Response(result, status=status.HTTP_200_OK)
        except RequestException as e:
            return Response(
                {"detail": f"FastAPI 호출 실패: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class ReviewAnalyzeAPIView(APIView):
    """
    [기능]
    특정 리뷰 1개를 기준으로
    같은 상품의 다른 리뷰들과 유사도를 비교하는 API

    GET /ai/reviews/<review_id>/analyze/

    [이전 코드]
    - 사용자가 text1, text2를 직접 입력해서 비교
    - 결과는 {"similarity": 점수} 정도의 단순 응답

    [현재 코드]
    - review_id만 받음
    - Django가 DB에서 기준 리뷰와 후보 리뷰들을 조회
    - FastAPI로 여러 리뷰를 반복 비교
    - 점수 기준(threshold) 이상만 남김
    - 화면에서 바로 쓸 수 있는 형태로 반환
    """
    permission_classes = [AllowAny]

    # 이전 코드에는 없었고,
    # 너무 낮은 유사도 결과는 화면에 안 보여주기 위한 기준값
    SIMILARITY_THRESHOLD = 0.45

    def get(self, request, review_id):
        # [흐름 1] 기준 리뷰 1개 조회
        source_review = get_object_or_404(
            Review.objects.select_related("user", "product"),
            id=review_id,
            is_public=True,
        )
        # [흐름 2] 같은 상품의 다른 리뷰들을 비교 후보로 조회
        candidate_reviews = (
            Review.objects
            .select_related("user")
            .filter(
                product=source_review.product,
                is_public=True
            )
            .exclude(id=source_review.id)
            .order_by("-created_at")[:20]
        )
        # [흐름 3] 기준 리뷰 내용 검사
        if not source_review.content.strip():
            return Response(
                {"detail": "분석할 리뷰 내용이 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []

        try:
            # [흐름 4] 후보 리뷰들을 하나씩 FastAPI에 보내 유사도 비교
            for candidate in candidate_reviews:
                if not candidate.content.strip():
                    continue

                similarity_result = FastAPIClient.get_similarity(
                    source_review.content,
                    candidate.content
                )

                # [현재 코드에서 분리]
                # 이전 코드에서는 결과를 바로 append 했다면,
                # 지금은 먼저 score 변수로 꺼내서 threshold 비교에 사용
                score = round(similarity_result["similarity"], 4)

                # [흐름 5] threshold 기준 적용
                if score >= self.SIMILARITY_THRESHOLD:
                    results.append({
                        "review_id": candidate.id,
                        "username": candidate.user.username,
                        "content": candidate.content,
                        "score": score,
                        "created_at": candidate.created_at.strftime("%Y-%m-%d %H:%M"),
                    })

        except RequestException as e:
            # [유지] FastAPI 호출 실패 시 502 반환
            return Response(
                {"detail": f"FastAPI 호출 실패: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        # [흐름 6] 점수 높은 순으로 정렬
        results.sort(key=lambda x: x["score"], reverse=True)

        # [흐름 7] 상위 3개만 최종 선택
        top_results = results[:3]

        # [흐름 8] 프론트에서 바로 쓸 수 있는 JSON 구조로 반환
        return Response(
            {
                "source_review": {
                    "review_id": source_review.id,
                    "username": source_review.user.username,
                    "content": source_review.content,
                },

                # [유지] threshold 적용 + 정렬 후 Top 3 결과
                "similar_reviews": top_results,

                # [현재 코드에서 추가]
                # 프론트에서 "비교할 리뷰가 몇 개 있었는지" 안내 문구에 활용 가능
                "candidate_count": candidate_reviews.count(),

                # [현재 코드에서 추가]
                # 프론트/디버깅 시 현재 기준값 확인용
                "similarity_threshold": self.SIMILARITY_THRESHOLD,
            },
            status=status.HTTP_200_OK
        )