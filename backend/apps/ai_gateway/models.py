# [추가] AI 추론 결과를 DRF DB에 저장하기 위한 모델 파일

from django.conf import settings
from django.db import models


class ReviewSimilarityResult(models.Model):
    """
    [추가]
    특정 기준 리뷰(source_review)와 비교 리뷰(compared_review)의
    유사도 결과를 저장하는 모델
    """

    # 어떤 상품 안에서 비교했는지 저장
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="ai_similarity_results",
    )

    # 기준이 되는 리뷰
    source_review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        related_name="source_similarity_results",
    )

    # 비교 대상 리뷰
    compared_review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        related_name="compared_similarity_results",
    )

    # 버튼을 누른 사용자 (비로그인 사용자일 수 있으므로 null 허용)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_similarity_results",
    )

    # FastAPI 모델 이름 저장
    model_name = models.CharField(
        max_length=100,
        default="upskyy/e5-small-korean",
    )

    # 유사도 점수
    similarity_score = models.FloatField()

    # 프론트에서 쓰는 해석 문구도 같이 저장
    similarity_label = models.CharField(max_length=30)

    # 기준 점수(threshold) 저장
    similarity_threshold = models.FloatField(default=0.45)

    # 당시의 텍스트 스냅샷 저장
    source_review_snapshot = models.TextField()
    compared_review_snapshot = models.TextField()

    # 비교 리뷰 작성자명을 스냅샷으로 저장
    compared_username_snapshot = models.CharField(max_length=150, blank=True)

    # 추론 시각
    analyzed_at = models.DateTimeField(auto_now=True)

    # 최초 생성 시각
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 같은 기준 리뷰 + 비교 리뷰 + 모델 이름 조합은 1개만 유지
        constraints = [
            models.UniqueConstraint(
                fields=["source_review", "compared_review", "model_name"],
                name="unique_review_similarity_result",
            )
        ]
        ordering = ["-similarity_score", "-analyzed_at"]

	# 관리/디버깅용 표시
    def __str__(self):
        return (
            f"[{self.model_name}] "
            f"source={self.source_review_id} "
            f"vs compared={self.compared_review_id} "
            f"score={self.similarity_score:.4f}"
        )