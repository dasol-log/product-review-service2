from django.urls import path
from .views import EmbeddingAPIView, SimilarityAPIView

urlpatterns = [
    path("embed/", EmbeddingAPIView.as_view(), name="ai-embed"),
    path("similarity/", SimilarityAPIView.as_view(), name="ai-similarity")
]