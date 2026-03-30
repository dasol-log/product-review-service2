# DRF ViewSet
# → list, create 같은 API 기능을 클래스 단위로 묶어서 관리
from rest_framework.viewsets import ViewSet

# API 응답을 JSON 형태로 반환
from rest_framework.response import Response

# 현재 코드에서는 사용하지 않음
# retrieve, update, destroy를 만들 때 주로 사용
from django.shortcuts import get_object_or_404

# 리뷰 상호작용 관련 모델
from .models import (
    ReviewLike,
    ReviewBookmark,
    ReviewComment,
    ReviewReport,
)

# 각 모델을 JSON으로 변환하고 입력값을 검증하는 Serializer
from .serializers import (
    ReviewLikeSerializer,
    ReviewBookmarkSerializer,
    ReviewCommentSerializer,
    ReviewReportSerializer,
)


class ReviewLikeViewSet(ViewSet):
    """
    리뷰 좋아요 API

    기능:
    - list   : 전체 좋아요 목록 조회
    - create : 좋아요 생성
    """

    def list(self, request):
        """
        좋아요 목록 조회 API

        흐름:
        1. DB에서 모든 좋아요 조회
        2. Serializer로 JSON 변환
        3. Response 반환
        """

        # 1️⃣ 전체 좋아요 데이터 조회
        likes = ReviewLike.objects.all()

        # 2️⃣ 여러 개 데이터이므로 many=True
        serializer = ReviewLikeSerializer(likes, many=True)

        # 3️⃣ JSON 응답 반환
        return Response(serializer.data)

    def create(self, request):
        """
        좋아요 생성 API

        흐름:
        4. 요청 데이터 받기
        5. Serializer로 검증
        6. 유효하면 DB 저장
        7. 결과 반환
        """

        # 1️⃣ 요청 데이터를 Serializer에 전달
        serializer = ReviewLikeSerializer(data=request.data)

        # 2️⃣ 유효성 검사
        if serializer.is_valid():

            # 3️⃣ DB 저장
            serializer.save()

            # 4️⃣ 저장된 데이터 반환
            return Response(serializer.data)

        # ❌ 검증 실패 시 에러 반환
        return Response(serializer.errors)


class ReviewBookmarkViewSet(ViewSet):
    """
    리뷰 북마크 API

    기능:
    - list   : 전체 북마크 목록 조회
    - create : 북마크 생성
    """

    def list(self, request):
        """
        북마크 목록 조회 API

        흐름:
        1. DB에서 모든 북마크 조회
        2. Serializer로 JSON 변환
        3. Response 반환
        """

        # 1️⃣ 전체 북마크 조회
        bookmarks = ReviewBookmark.objects.all()

        # 2️⃣ 여러 개 데이터 직렬화
        serializer = ReviewBookmarkSerializer(bookmarks, many=True)

        # 3️⃣ JSON 응답 반환
        return Response(serializer.data)

    def create(self, request):
        """
        북마크 생성 API

        흐름:
        4. 요청 데이터 받기
        5. Serializer 검증
        6. 유효하면 저장
        7. 결과 반환
        """

        # 1️⃣ 요청 데이터 전달
        serializer = ReviewBookmarkSerializer(data=request.data)

        # 2️⃣ 유효성 검사
        if serializer.is_valid():

            # 3️⃣ 저장
            serializer.save()

            # 4️⃣ 결과 반환
            return Response(serializer.data)

        # ❌ 검증 실패
        return Response(serializer.errors)


class ReviewCommentViewSet(ViewSet):
    """
    리뷰 댓글 API

    기능:
    - list   : 전체 댓글 목록 조회
    - create : 댓글 생성
    """

    def list(self, request):
        """
        댓글 목록 조회 API

        흐름:
        1. DB에서 모든 댓글 조회
        2. Serializer 변환
        3. Response 반환
        """

        # 1️⃣ 전체 댓글 조회
        comments = ReviewComment.objects.all()

        # 2️⃣ JSON 변환
        serializer = ReviewCommentSerializer(comments, many=True)

        # 3️⃣ 응답 반환
        return Response(serializer.data)

    def create(self, request):
        """
        댓글 생성 API

        흐름:
        4. 요청 데이터 받기
        5. Serializer 검증
        6. 유효하면 저장
        7. 결과 반환
        """

        # 1️⃣ 요청 데이터 전달
        serializer = ReviewCommentSerializer(data=request.data)

        # 2️⃣ 유효성 검사
        if serializer.is_valid():

            # 3️⃣ 저장
            serializer.save()

            # 4️⃣ 저장 결과 반환
            return Response(serializer.data)

        # ❌ 검증 실패
        return Response(serializer.errors)


class ReviewReportViewSet(ViewSet):
    """
    리뷰 신고 API

    기능:
    - list   : 전체 신고 목록 조회
    - create : 신고 생성
    """

    def list(self, request):
        """
        신고 목록 조회 API

        흐름:
        1. DB에서 모든 신고 조회
        2. Serializer 변환
        3. Response 반환
        """

        # 1️⃣ 전체 신고 목록 조회
        reports = ReviewReport.objects.all()

        # 2️⃣ JSON 변환
        serializer = ReviewReportSerializer(reports, many=True)

        # 3️⃣ 응답 반환
        return Response(serializer.data)

    def create(self, request):
        """
        신고 생성 API

        흐름:
        4. 요청 데이터 받기
        5. Serializer 검증
        6. 유효하면 저장
        7. 결과 반환
        """

        # 1️⃣ 요청 데이터 전달
        serializer = ReviewReportSerializer(data=request.data)

        # 2️⃣ 유효성 검사
        if serializer.is_valid():

            # 3️⃣ 저장
            serializer.save()

            # 4️⃣ 결과 반환
            return Response(serializer.data)

        # ❌ 검증 실패
        return Response(serializer.errors)