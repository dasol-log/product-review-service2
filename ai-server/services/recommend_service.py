# from models.embedding_model import embedding_model
# from sklearn.metrics.pairwise import cosine_similarity


# def make_embeddings(texts: list[str]) -> list[list[float]]:
#     """
#     여러 문장을 받아 임베딩 벡터 리스트로 반환
#     """
#     vectors = embedding_model.encode(texts)
#     return [vector.tolist() for vector in vectors]


# def calculate_similarity(text1: str, text2: str) -> float:
#     """
#     두 문장의 cosine similarity 계산
#     """
#     vectors = embedding_model.encode([text1, text2])
#     score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
#     return float(score)


# 쿠버네티스 실습용
from typing import List


def make_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Kubernetes 실습용 mock embedding
    실제 모델 대신 384차원 벡터 반환
    """
    return [[0.0] * 384 for _ in texts]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    (실습용) 실제 사용 안 할 예정이지만
    혹시 호출될 경우 대비용
    """
    return 0.5