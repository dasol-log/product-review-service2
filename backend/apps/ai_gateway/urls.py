from django.urls import path
from .views import ReviewAnalyzeAPIView

urlpatterns = [
    path("reviews/<int:review_id>/analyze/", ReviewAnalyzeAPIView.as_view(), name="ai-review-analyze"),
]