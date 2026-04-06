from typing import List

from pydantic import BaseModel


# Django → FastAPI 요청 데이터
class EmbeddingRequest(BaseModel):
    texts: List[str]


class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]


class SimilarityRequest(BaseModel):
    text1: str
    text2: str


class SimilarityResponse(BaseModel):
    similarity: float
