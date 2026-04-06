from requests import RequestException

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import EmbeddingRequestSerializer, SimilarityRequestSerializer
from .services import FastAPIClient


class EmbeddingAPIView(APIView):
    def post(self, request):
        serializer = EmbeddingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        texts = serializer.validated_data["texts"]

        try:
            # 현재 구조 유지: 한 문장씩 보내서 리스트로 반환
            embeddings = [FastAPIClient.get_embedding(text) for text in texts]
            return Response({"embeddings": embeddings}, status=status.HTTP_200_OK)
        except RequestException as e:
            return Response(
                {"detail": f"FastAPI 호출 실패: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class SimilarityAPIView(APIView):
    def post(self, request):
        serializer = SimilarityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text1 = serializer.validated_data["text1"]
        text2 = serializer.validated_data["text2"]

        try:
            result = FastAPIClient.get_similarity(text1, text2)
            return Response(result, status=status.HTTP_200_OK)
        except RequestException as e:
            return Response(
                {"detail": f"FastAPI 호출 실패: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )