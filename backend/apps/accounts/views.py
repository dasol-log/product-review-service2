from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status  # [추가] status 추가
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import User
from .serializers import UserSerializer, SignupSerializer


class UserViewSet(ViewSet):
    """
    사용자 조회용 ViewSet

    - list: 전체 사용자 목록 조회
    - retrieve: 특정 사용자 상세 조회

    현재는 조회 전용으로 사용
    필요하면 나중에 관리자 권한으로 제한 가능
    """

    permission_classes = [permissions.AllowAny]

    def list(self, request):
        # [수정] 최신 사용자부터 보이도록 정렬 추가
        users = User.objects.all().order_by("-id")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class SignupAPIView(generics.CreateAPIView):
    """
    회원가입 API

    POST /accounts/signup/

    요청 예시:
    {
        "username": "testuser",
        "email": "test@example.com",
        "password": "1234",
        "password_confirm": "1234"
    }
    """

    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    # [추가] 회원가입 성공 시 비밀번호가 아닌 안전한 사용자 정보만 응답하도록 오버라이드
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class MeAPIView(generics.RetrieveAPIView):
    """
    현재 로그인한 사용자 정보 조회 API

    GET /accounts/me/

    헤더:
    Authorization: Bearer <access_token>
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user