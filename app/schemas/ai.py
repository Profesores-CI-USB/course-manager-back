from pydantic import BaseModel, Field


class AIPredictRequest(BaseModel):
    features: list[float] = Field(..., min_length=3, max_length=3)


class AIPredictResponse(BaseModel):
    model: str
    score: float
    label: str
