import math

from fastapi import HTTPException, status

from app.core.config import settings


class BaseInferenceModel:
    name: str = "base"

    def predict(self, features: list[float]) -> dict:
        raise NotImplementedError


class SimpleNeuralNetModel(BaseInferenceModel):
    name = "simple_nn"

    def __init__(self) -> None:
        self.hidden_weights = [
            [0.35, -0.22, 0.81],
            [-0.61, 0.48, 0.14],
        ]
        self.hidden_bias = [0.1, -0.05]
        self.output_weights = [0.72, -0.41]
        self.output_bias = 0.03

    @staticmethod
    def _sigmoid(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def predict(self, features: list[float]) -> dict:
        if len(features) != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El modelo simple_nn requiere exactamente 3 features",
            )

        hidden_layer = []
        for neuron_weights, neuron_bias in zip(self.hidden_weights, self.hidden_bias):
            activation = sum(w * x for w, x in zip(neuron_weights, features)) + neuron_bias
            hidden_layer.append(self._sigmoid(activation))

        output_activation = (
            hidden_layer[0] * self.output_weights[0]
            + hidden_layer[1] * self.output_weights[1]
            + self.output_bias
        )
        score = self._sigmoid(output_activation)

        return {
            "model": self.name,
            "score": round(score, 6),
            "label": "positive" if score >= 0.5 else "negative",
        }


MODELS: dict[str, BaseInferenceModel] = {
    "simple_nn": SimpleNeuralNetModel(),
}


def get_active_model() -> BaseInferenceModel:
    model = MODELS.get(settings.ai_model_name)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Modelo de IA '{settings.ai_model_name}' no registrado",
        )
    return model
