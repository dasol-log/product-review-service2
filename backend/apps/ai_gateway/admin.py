# AI 추론 결과를 Django admin에서 확인하기 위한 파일

from django.contrib import admin
from .models import ReviewSimilarityResult


@admin.register(ReviewSimilarityResult)
class ReviewSimilarityResultAdmin(admin.ModelAdmin):
    # 목록에서 주요 필드 확인
    list_display = (
        "id",
        "product",
        "source_review",
        "compared_review",
        "similarity_score",
        "similarity_label",
        "model_name",
        "analyzed_at",
    )

    # 검색 기능
    search_fields = (
        "product__name",
        "source_review__content",
        "compared_review__content",
        "compared_username_snapshot",
        "model_name",
    )

    # 필터
    list_filter = (
        "model_name",
        "similarity_label",
        "analyzed_at",
    )

    # 정렬
    ordering = ("-analyzed_at",)