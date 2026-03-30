# 특정 객체가 없을 경우 404 에러 반환
from django.shortcuts import get_object_or_404

# (현재 코드에서는 사용 안함 → 제거 가능)
from django.views.generic import TemplateView

# DRF ViewSet (CRUD API를 하나의 클래스에서 관리)
from rest_framework.viewsets import ViewSet

# JSON 응답 반환
from rest_framework.response import Response

# 페이지네이션 처리 클래스
from rest_framework.pagination import PageNumberPagination

# HTTP 상태 코드 사용
from rest_framework import status

# Product 모델 (DB 테이블)
from .models import Product

# Product 데이터를 JSON으로 변환하는 Serializer
from .serializers import ProductSerializer


class ProductPagination(PageNumberPagination):
    """
    페이지네이션 설정

    - 기본 페이지 크기: 6
    - 클라이언트에서 page_size 조정 가능
    - 최대 20개까지 허용
    """
    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 20


class ProductViewSet(ViewSet):
    """
    Product CRUD API

    - list     : 상품 목록 조회 (GET /products/)
    - retrieve : 상품 상세 조회 (GET /products/{id}/)
    - create   : 상품 생성 (POST /products/)
    - update   : 상품 수정 (PUT /products/{id}/)
    - destroy  : 상품 삭제 (DELETE /products/{id}/)
    """

    def list(self, request):
        """
        상품 목록 조회 API

        흐름:
        1. DB에서 전체 상품 조회 (최신순)
        2. 페이지네이션 적용
        3. Serializer로 JSON 변환
        4. 페이지네이션 응답 반환
        """

        # 1️⃣ 전체 상품 조회 (id 기준 내림차순)
        queryset = Product.objects.all().order_by("-id")

        # 2️⃣ 페이지네이션 적용
        paginator = ProductPagination()
        page = paginator.paginate_queryset(queryset, request)

        # 3️⃣ 여러 데이터이므로 many=True
        serializer = ProductSerializer(page, many=True)

        # 4️⃣ 페이지네이션 포함 응답 반환
        return paginator.get_paginated_response(serializer.data)


    def retrieve(self, request, pk=None):
        """
        상품 상세 조회 API

        흐름:
        1. pk(id)로 상품 조회
        2. 없으면 404 에러
        3. Serializer 변환
        4. Response 반환
        """

        # 1️⃣ 상품 조회 (없으면 자동 404)
        product = get_object_or_404(Product, pk=pk)

        # 2️⃣ 단일 객체 변환
        serializer = ProductSerializer(product)

        # 3️⃣ JSON 응답 반환
        return Response(serializer.data)


    def create(self, request):
        """
        상품 생성 API

        흐름:
        1. 요청 데이터(request.data) 받기
        2. Serializer로 검증
        3. 유효하면 DB 저장
        4. 생성된 데이터 반환
        """

        # 1️⃣ 요청 데이터 → Serializer
        serializer = ProductSerializer(data=request.data)

        # 2️⃣ 유효성 검사
        if serializer.is_valid():

            # 3️⃣ DB 저장
            serializer.save()

            # 4️⃣ 생성 성공 응답
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # ❌ 유효성 실패 시 에러 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk=None):
        """
        상품 수정 API

        흐름:
        1. 기존 상품 조회
        2. 요청 데이터로 덮어쓰기
        3. 검증 후 저장
        4. 수정된 데이터 반환
        """

        # 1️⃣ 수정 대상 조회
        product = get_object_or_404(Product, pk=pk)

        # 2️⃣ 기존 객체 + 새로운 데이터 전달
        serializer = ProductSerializer(product, data=request.data)

        # 3️⃣ 유효성 검사
        if serializer.is_valid():

            # 4️⃣ 업데이트 저장
            serializer.save()

            return Response(serializer.data)

        # ❌ 검증 실패
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, pk=None):
        """
        상품 삭제 API

        흐름:
        1. 삭제 대상 조회
        2. DB에서 삭제
        3. 성공 메시지 반환
        """

        # 1️⃣ 삭제 대상 조회
        product = get_object_or_404(Product, pk=pk)

        # 2️⃣ 삭제
        product.delete()

        # 3️⃣ 삭제 성공 응답
        return Response({"message": "deleted"}, status=status.HTTP_204_NO_CONTENT)