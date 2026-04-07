from django.conf import settings
from django.db import models


class ReviewSimilarityResult(models.Model):
    """
    [유지]
    AI 유사도 분석 결과 저장 모델 (최종 결과 데이터)
    """

    # 어떤 상품 기준으로 분석했는지 연결
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
    

class AIAnalysisTask(models.Model):
    """
    [추가]
    Celery 비동기 작업 상태를 DB에서 추적하기 위한 모델
    """
    # [상태 값 정의]
    STATUS_PENDING = "PENDING"     # 작업 대기중
    STATUS_STARTED = "STARTED"     # 작업 진행중
    STATUS_SUCCESS = "SUCCESS"     # 작업 완료
    STATUS_FAILURE = "FAILURE"     # 작업 실패

    STATUS_CHOICES = [
        (STATUS_PENDING, "대기중"),
        (STATUS_STARTED, "진행중"),
        (STATUS_SUCCESS, "완료"),
        (STATUS_FAILURE, "실패"),
    ]

    # [어떤 리뷰를 분석했는지]
    source_review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        related_name="ai_analysis_tasks",
    )

    # [누가 요청했는지]
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_analysis_tasks",
    )
    # 어떤 사용자가 분석 요청했는지 (로그 추적용)

    
    # [Celery 연결 키]
    task_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )
    # Celery 작업 고유 ID (이걸로 작업 상태 추적)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    model_name = models.CharField(
        max_length=100,
        default="upskyy/e5-small-korean",
    )

    # [유사도 기준값]
    similarity_threshold = models.FloatField(default=0.45)

    # [분석 통계]
    candidate_count = models.PositiveIntegerField(default=0)

    # 비교 대상 리뷰 개수
    result_count = models.PositiveIntegerField(default=0)

    # [에러 정보]
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    # [관리자 표시용]
    def __str__(self):
        return f"{self.task_id} - {self.status}"
    # admin / 로그에서 "task_id - 상태" 형태로 표시