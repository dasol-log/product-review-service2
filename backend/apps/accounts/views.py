from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions
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
        users = User.objects.all()
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