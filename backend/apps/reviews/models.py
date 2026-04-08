from apps.core.models import SoftDeleteModel
from apps.products.models import Product
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# [추가] 공통 Soft Delete 추상 모델 import


User = settings.AUTH_USER_MODEL


class Review(SoftDeleteModel):  # [수정] models.Model → SoftDeleteModel 상속으로 변경
    """
    제품 리뷰 모델
    - 리뷰 본문, 평점, 공개 여부 저장
    - Soft Delete 적용 대상
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # [수정] 사용자 삭제 시 리뷰까지 지우지 않고 user만 null 처리
        null=True,  # [추가] SET_NULL 사용을 위해 필요
        blank=True,  # [추가] 관리자/폼에서 비워둘 수 있게 허용
        related_name="reviews",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # [수정] 상품 삭제 시 리뷰가 있으면 삭제 막음
        related_name="reviews",
    )

    content = models.TextField()

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        # user가 삭제되어 null일 수도 있으므로 안전하게 처리
        username = self.user.username if self.user else "탈퇴한 사용자"
        return f"{self.product} - {username}"


class ReviewImage(models.Model):
    """
    리뷰 이미지
    """

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,  # 리뷰가 완전 삭제(hard delete)되면 이미지도 함께 삭제
        related_name="images",
    )

    image = models.ImageField(upload_to="reviews/")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewImage(review_id={self.review_id})"


class ReviewAI(models.Model):
    """
    리뷰 AI 분석 결과
    """

    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,  # 리뷰가 완전 삭제(hard delete)되면 AI 결과도 함께 삭제
        related_name="ai_result",
    )

    sentiment = models.CharField(max_length=50)

    confidence = models.FloatField()

    keywords = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewAI(review_id={self.review_id})"
