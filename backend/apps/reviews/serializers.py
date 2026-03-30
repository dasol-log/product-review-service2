from rest_framework import serializers
from .models import Review, ReviewImage, ReviewAI


# 📌 ReviewImage (리뷰 이미지) Serializer
# → Review와 1:N 관계 (리뷰 하나에 이미지 여러 개)
class ReviewImageSerializer(serializers.ModelSerializer):
    """
    리뷰 이미지 출력용 Serializer

    역할:
    - ReviewImage 모델 → JSON 변환
    - ReviewSerializer 내부에서 nested로 사용됨 (읽기 전용)
    """

    class Meta:
        model = ReviewImage
        fields = [
            "id",
            "image",
            "created_at",
        ]


# 📌 ReviewAI (AI 분석 결과) Serializer
# → Review와 1:1 관계
class ReviewAISerializer(serializers.ModelSerializer):
    """
    리뷰 AI 분석 결과 Serializer

    역할:
    - AI 감정 분석 결과를 JSON으로 변환
    - ReviewSerializer에서 nested로 포함됨 (읽기 전용)
    """

    class Meta:
        model = ReviewAI
        fields = [
            "sentiment",
            "confidence",
            "keywords",
        ]


# 📌 Review 메인 Serializer
class ReviewSerializer(serializers.ModelSerializer):
    """
    Review CRUD + 관계 데이터 Serializer

    역할:
    1️⃣ 입력 검증
        - user, product, content, rating 등의 데이터 검증
        - create/update 시 request.data 검증 수행

    2️⃣ 출력 변환
        - Review 데이터를 JSON으로 변환

    3️⃣ 관계 데이터 포함 (Nested Serializer)
        - images (1:N) → 리뷰 이미지 목록 포함
        - ai_result (1:1) → AI 분석 결과 포함
    """

    # ReviewImage 연결 (related_name="images")
    # → Review.objects.get(...).images 로 접근 가능
    # → many=True: 여러 개 이미지
    # → read_only=True: 생성/수정은 여기서 안함 (출력만)
    images = ReviewImageSerializer(
        many=True,
        read_only=True
    )

    # ReviewAI 연결 (related_name="ai_result")
    # → 1:1 관계
    # → read_only=True: AI 결과는 별도 로직에서 생성
    ai_result = ReviewAISerializer(
        read_only=True
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "user",         # FK (입력 검증 대상)
            "product",      # FK (입력 검증 대상)
            "content",      # 입력 데이터
            "rating",       # 입력 데이터
            "is_public",
            "images",       # nested (출력 전용)
            "ai_result",    # nested (출력 전용)
            "created_at",
            "updated_at",
        ]