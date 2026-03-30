from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import UserViewSet, SignupAPIView, MeAPIView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    # 기존 UserViewSet 유지
    path("", include(router.urls)),

    # 회원가입
    path("signup/", SignupAPIView.as_view(), name="signup"),

    # JWT 로그인 / 재발급
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeAPIView.as_view(), name="me"),
]