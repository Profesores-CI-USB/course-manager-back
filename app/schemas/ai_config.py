from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


_DEFAULT_HYPERPARAMS_DENSE: dict = {
    "max_features": 10,
    "layers": [64, 32],
    "dropout": 0.2,
    "epochs": 50,
    "learning_rate": 0.001,
    "batch_size": 16,
}

_DEFAULT_HYPERPARAMS_LINEAR: dict = {
    "max_features": 10,
    "epochs": 100,
    "learning_rate": 0.01,
    "batch_size": 16,
}


class AIModelConfigCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    model_type: Literal["linear", "dense_nn"]
    target: Literal["final_grade", "pass_probability"]
    hyperparams: dict = Field(default_factory=dict)


class AIModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    hyperparams: dict | None = None


class AIModelConfigOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    model_type: Literal["linear", "dense_nn"]
    target: Literal["final_grade", "pass_probability"]
    hyperparams: dict
    is_trained: bool
    trained_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainResponse(BaseModel):
    config_id: UUID
    is_trained: bool
    trained_at: datetime | None
    samples_used: int
    message: str
