from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet,
    ProductListPageView,
    ProductDetailPageView,
    ProductCreatePageView,
    ProductUpdatePageView
)

router = DefaultRouter()
router.register("", ProductViewSet, basename="product")

urlpatterns = [
    path("", ProductListPageView.as_view(), name="product-page-list"),
    path("create/", ProductCreatePageView.as_view(), name="product-page-create"),
    path("<int:pk>/update/", ProductUpdatePageView.as_view(), name="product-page-edit"),
    path("<int:pk>/", ProductDetailPageView.as_view(), name="product-page-detail"),

    path("api/", include(router.urls)),
]