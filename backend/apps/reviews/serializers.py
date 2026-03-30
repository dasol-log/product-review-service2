from rest_framework import serializers

from .models import Review, ReviewImage, ReviewAI


class ReviewImageSerializer(serializers.ModelSerializer):
    """
    리뷰 이미지 Serializer
    """

    class Meta:
        model = ReviewImage
        fields = [
            "id",
            "image",
            "created_at",
        ]


class ReviewAISerializer(serializers.ModelSerializer):
    """
    리뷰 AI 분석 결과 Serializer
    """

    class Meta:
        model = ReviewAI
        fields = [
            "sentiment",
            "confidence",
            "keywords",
        ]
        
        
class ReviewSerializer(serializers.ModelSerializer):
    """
    리뷰 Serializer
    """

    images = ReviewImageSerializer(
        many=True,
        read_only=True
    )

    ai_result = ReviewAISerializer(
        read_only=True
    )

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "product",
            "content",
            "rating",
            "is_public",
            "images",
            "ai_result",
            "uploaded_images",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "images",
            "ai_result",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """
        리뷰 생성 + 이미지 저장 처리
        """

        uploaded_images = validated_data.pop("uploaded_images", [])
        review = Review.objects.create(**validated_data)

        for image_file in uploaded_images:
            ReviewImage.objects.create(
                review=review,
                image=image_file
            )

        return review