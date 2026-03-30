# → 하나의 클래스에서 list, retrieve, create 등 여러 API를 묶어서 관리
from rest_framework.viewsets import ViewSet

# API 응답을 반환하기 위한 객체 (JSON 형태로 반환됨)
from rest_framework.response import Response

# 객체가 없을 경우 404 에러를 자동으로 발생시키는 함수
from django.shortcuts import get_object_or_404

# User 모델 (DB와 연결된 데이터 구조)
from .models import User

# User 데이터를 JSON으로 변환해주는 Serializer
from .serializers import UserSerializer


class UserViewSet(ViewSet):
    """
    User API ViewSet

    - list     : 전체 사용자 조회 (GET /users/)
    - retrieve : 특정 사용자 조회 (GET /users/{id}/)
    """

    def list(self, request):
        """
        전체 사용자 조회 API

        흐름:
        1. DB에서 모든 User 조회
        2. Serializer로 JSON 변환
        3. Response로 반환
        """

        # 1️⃣ 모든 사용자 데이터 조회 (QuerySet 반환)
        users = User.objects.all()

        # 2️⃣ 여러 개 데이터이므로 many=True 설정
        serializer = UserSerializer(users, many=True)

        # 3️⃣ JSON 형태로 응답 반환
        return Response(serializer.data)


    def retrieve(self, request, pk=None):
        """
        특정 사용자 상세 조회 API

        흐름:
        4. pk(id)를 기준으로 User 조회
        5. 없으면 404 에러 발생
        6. Serializer로 JSON 변환
        7. Response 반환
        """

        # 1️⃣ pk에 해당하는 사용자 조회 (없으면 자동 404)
        user = get_object_or_404(User, pk=pk)

        # 2️⃣ 단일 객체이므로 many=False (기본값)
        serializer = UserSerializer(user)

        # 3️⃣ JSON 형태로 응답 반환
        return Response(serializer.data)