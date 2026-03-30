# DRF ViewSet (CRUD API 묶음)
from rest_framework.viewsets import ViewSet

# JSON 응답 반환
from rest_framework.response import Response

# 객체 없을 경우 404 자동 반환
from django.shortcuts import get_object_or_404

# Review 모델 (DB 테이블)
from .models import Review

# Review 데이터를 JSON으로 변환하는 Serializer
from .serializers import ReviewSerializer


class ReviewViewSet(ViewSet):
    """
    Review CRUD API

    - list     : 리뷰 목록 조회 (GET /reviews/)
    - retrieve : 리뷰 상세 조회 (GET /reviews/{id}/)
    - create   : 리뷰 생성 (POST /reviews/)
    - update   : 리뷰 수정 (PUT /reviews/{id}/)
    - destroy  : 리뷰 삭제 (DELETE /reviews/{id}/)
    """

    def list(self, request):
        """
        리뷰 목록 조회 API

        흐름:
        1. DB에서 모든 리뷰 조회
        2. Serializer로 변환
        3. Response 반환
        """

        # 1️⃣ 모든 리뷰 조회
        reviews = Review.objects.all().order_by("-id")

        # 2️⃣ 여러 개 데이터 → many=True
        serializer = ReviewSerializer(reviews, many=True)

        # 3️⃣ JSON 응답 반환
        return Response(serializer.data)


    def retrieve(self, request, pk=None):
        """
        리뷰 상세 조회 API

        흐름:
        4. pk로 리뷰 조회
        5. 없으면 404
        6. Serializer 변환
        7. Response 반환
        """

        # 1️⃣ 특정 리뷰 조회
        review = get_object_or_404(Review, pk=pk)

        # 2️⃣ 단일 객체 변환
        serializer = ReviewSerializer(review)

        # 3️⃣ JSON 응답 반환
        return Response(serializer.data)


    def create(self, request):
        """
        리뷰 생성 API

        흐름:
        8. 요청 데이터 받기
        9. Serializer 검증
        10. 유효하면 DB 저장
        11. 결과 반환
        """

        # 1️⃣ 요청 데이터 → Serializer
        serializer = ReviewSerializer(data=request.data)

        # 2️⃣ 유효성 검사
        if serializer.is_valid():

            # 3️⃣ DB 저장
            serializer.save()

            # 4️⃣ 생성된 데이터 반환
            return Response(serializer.data)

        # ❌ 검증 실패
        return Response(serializer.errors)


    def update(self, request, pk=None):
        """
        리뷰 수정 API

        흐름:
        12. 기존 리뷰 조회
        13. 요청 데이터로 덮어쓰기
        14. 검증 후 저장
        15. 수정된 데이터 반환
        """

        # 1️⃣ 수정 대상 조회
        review = get_object_or_404(Review, pk=pk)

        # 2️⃣ 기존 객체 + 요청 데이터 전달
        serializer = ReviewSerializer(review, data=request.data)

        # 3️⃣ 유효성 검사
        if serializer.is_valid():

            # 4️⃣ 업데이트 저장
            serializer.save()

            return Response(serializer.data, status=201)

        # ❌ 검증 실패
        return Response(serializer.errors)


    def destroy(self, request, pk=None):
        """
        리뷰 삭제 API

        흐름:
        16. 삭제 대상 조회
        17. DB에서 삭제
        18. 응답 반환
        """

        # 1️⃣ 삭제 대상 조회
        review = get_object_or_404(Review, pk=pk)

        # 2️⃣ 삭제
        review.delete()

        # 3️⃣ 삭제 완료 응답
        return Response({"message": "deleted"})