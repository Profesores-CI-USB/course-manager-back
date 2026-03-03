from fastapi import APIRouter

from app.schemas.ai import AIPredictRequest, AIPredictResponse
from app.services.ai_model import get_active_model


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/predict", response_model=AIPredictResponse)
async def predict(payload: AIPredictRequest):
    model = get_active_model()
    result = model.predict(payload.features)
    return AIPredictResponse(**result)
