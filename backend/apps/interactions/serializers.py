from rest_framework import serializers
from .models import (
    ReviewLike,
    ReviewBookmark,
    ReviewComment,
    ReviewReport,
)


# 좋아요 Serializer
class ReviewLikeSerializer(serializers.ModelSerializer):
    """
    리뷰 좋아요 Serializer

    역할:
    1. 입력 검증
        - user, review 값이 정상인지 검증
        - 중복 좋아요는 모델(unique_together)에서 제한

    2. 출력 변환
        - 좋아요 데이터를 JSON으로 변환
    """

    class Meta:
        model = ReviewLike
        fields = [
            "id",
            "user",       # FK (입력 검증 대상)
            "review",     # FK (입력 검증 대상)
            "created_at",
        ]


# 북마크 Serializer
class ReviewBookmarkSerializer(serializers.ModelSerializer):
    """
    리뷰 북마크 Serializer

    역할:
    - user와 review 관계 데이터 검증
    - 북마크 데이터 JSON 변환
    """

    class Meta:
        model = ReviewBookmark
        fields = [
            "id",
            "user",
            "review",
            "created_at",
        ]


# 댓글 Serializer
class ReviewCommentSerializer(serializers.ModelSerializer):
    """
    리뷰 댓글 Serializer

    역할:
    1. 입력 검증
        - user, review, content 검증
        - 댓글 내용(content) 필수값

    2. 출력 변환
        - 댓글 데이터를 JSON으로 반환
    """

    class Meta:
        model = ReviewComment
        fields = [
            "id",
            "user",
            "review",
            "content",   # 입력 데이터 (검증 대상)
            "created_at",
        ]


# 신고 Serializer
class ReviewReportSerializer(serializers.ModelSerializer):
    """
    리뷰 신고 Serializer

    역할:
    1. 입력 검증
        - user, review, reason 검증
        - 신고 사유(reason) 필수값

    2. 출력 변환
        - 신고 데이터를 JSON으로 반환
    """

    class Meta:
        model = ReviewReport
        fields = [
            "id",
            "user",
            "review",
            "reason",   # 입력 데이터 (검증 대상)
            "created_at",
        ]