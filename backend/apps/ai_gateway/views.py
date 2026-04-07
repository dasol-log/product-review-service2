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
    [추가]
    특정 리뷰를 기준으로 같은 상품의 다른 리뷰들과 유사도 비교
    GET /ai/reviews/<review_id>/analyze/

    [이전 코드와 차이]
    - 이전 SimilarityAPIView:
      사용자가 text1, text2를 직접 보내면 그 두 문장을 비교했음
    - 현재 ReviewAnalyzeAPIView:
      review_id만 받으면 Django가 DB에서 리뷰를 조회해서
      같은 상품의 다른 리뷰들과 자동으로 비교함
    """
    permission_classes = [AllowAny]  # [추가] 로그인하지 않아도 분석 결과 조회 가능하도록 설정

    def get(self, request, review_id):  # [변경] post()가 아니라 get() 사용 / text1, text2 직접 안 받음
        source_review = get_object_or_404(
            Review.objects.select_related("user", "product"),
            id=review_id,
            is_public=True,
        )
        # [추가]
        # review_id에 해당하는 기준 리뷰 1개를 DB에서 조회
        # 이전 코드와 달리 사용자가 문장을 직접 보내지 않고,
        # Django가 리뷰 본문을 DB에서 직접 가져옴

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
        # [추가]
        # 같은 상품의 다른 리뷰들을 비교 후보로 조회
        # - 같은 product만 가져옴
        # - 자기 자신 리뷰는 제외
        # - 최신순 정렬
        # - 최대 20개까지만 비교

        if not source_review.content.strip():
            return Response(
                {"detail": "분석할 리뷰 내용이 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # [추가]
        # 기준 리뷰 본문이 비어 있으면 FastAPI에 보낼 수 없으므로 여기서 미리 차단

        results = []
        # [추가]
        # 비교 결과를 모아둘 리스트

        try:
            for candidate in candidate_reviews:
                if not candidate.content.strip():
                    continue
                # [추가]
                # 비교 대상 리뷰 본문이 비어 있으면 건너뜀

                similarity_result = FastAPIClient.get_similarity(
                    source_review.content,
                    candidate.content
                )
                # [유지 + 사용방식 변경]
                # FastAPIClient.get_similarity() 자체는 기존과 같지만,
                # 이전에는 사용자가 보낸 text1, text2를 비교했다면
                # 지금은 DB에서 조회한 리뷰 본문끼리 비교함

                results.append({
                    "review_id": candidate.id,
                    "username": candidate.user.username,
                    "content": candidate.content,
                    "score": round(similarity_result["similarity"], 4),
                    "created_at": candidate.created_at.strftime("%Y-%m-%d %H:%M"),
                })
                # [추가]
                # FastAPI 결과를 프론트에서 바로 출력하기 쉽게 가공해서 저장
                # 이전 SimilarityAPIView는 result 자체를 거의그대로 반환했지만,
                # 여기서는 리뷰 정보 + 점수를 함께 묶어서 반환용 데이터로 만듦

        except RequestException as e:
            return Response(
                {"detail": f"FastAPI 호출 실패: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        # [유지]
        # FastAPI 서버 호출 실패 시 에러 응답 반환

        results.sort(key=lambda x: x["score"], reverse=True)
        # [추가]
        # 유사도 점수가 높은 순으로 정렬

        top_results = results[:3]
        # [추가]
        # 상위 3개만 추출해서 반환

        return Response(
            {
                "source_review": {
                    "review_id": source_review.id,
                    "username": source_review.user.username,
                    "content": source_review.content,
                },
                "similar_reviews": top_results,
            },
            status=status.HTTP_200_OK
        )
        # [변경]
        # 이전 SimilarityAPIView는 {"similarity": 점수} 
        # 정도의 단순 결과를 반환했지만
        
        # 현재는
        # - 기준 리뷰 정보(source_review)
        # - 비슷한 리뷰 목록(similar_reviews)
        # 을 함께 반환하여 화면에서 바로 출력할 수 있게 바뀜