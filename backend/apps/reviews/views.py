from rest_framework import permissions, status, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    리뷰 CRUD API
    - GET /reviews/
    - GET /reviews/<id>/
    - POST /reviews/
    - PATCH /reviews/<id>/
    - DELETE /reviews/<id>/

    최소 이미지 업로드 테스트용 코드
    """

    queryset = Review.objects.all().order_by("-created_at")
    serializer_class = ReviewSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """
        조회는 누구나 가능
        생성/수정/삭제는 로그인 사용자만 가능
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        로그인 사용자로 리뷰 저장
        """
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "deleted"},
            status=status.HTTP_204_NO_CONTENT
        )