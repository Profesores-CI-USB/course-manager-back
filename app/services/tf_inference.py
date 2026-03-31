"""
Capa de inferencia ML (scikit-learn).

Todas las operaciones de entrenamiento y predicción son síncronas
y deben ejecutarse en un executor para no bloquear el event loop.
Ejemplo de uso:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, build_and_train, X, y, ...)
"""

from __future__ import annotations

import pickle
from pathlib import Path

from app.core.exceptions import BadRequestException, InternalException

MIN_TRAINING_SAMPLES = 10


def _build_estimator(model_type: str, target: str, hyperparams: dict):
    """Construye el estimador scikit-learn según model_type y target."""
    try:
        import numpy as np  # noqa: F401 — ensure numpy is available
        from sklearn.linear_model import LinearRegression, LogisticRegression
        from sklearn.neural_network import MLPClassifier, MLPRegressor
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        raise InternalException(
            "scikit-learn no está instalado. Ejecuta: pip install scikit-learn numpy"
        )

    max_iter: int = hyperparams.get("epochs", 200)
    lr: float = hyperparams.get("learning_rate", 0.001)
    hidden_units: list[int] = hyperparams.get("hidden_units", [64, 32])

    if model_type == "linear":
        if target == "pass_probability":
            estimator = LogisticRegression(max_iter=max_iter, C=1.0 / lr)
        else:
            estimator = LinearRegression()

    elif model_type == "dense_nn":
        hidden_layer_sizes = tuple(hidden_units)
        if target == "pass_probability":
            estimator = MLPClassifier(
                hidden_layer_sizes=hidden_layer_sizes,
                max_iter=max_iter,
                learning_rate_init=lr,
            )
        else:
            estimator = MLPRegressor(
                hidden_layer_sizes=hidden_layer_sizes,
                max_iter=max_iter,
                learning_rate_init=lr,
            )

    else:
        raise BadRequestException(f"Tipo de modelo desconocido: {model_type}")

    # Wrap in pipeline with scaler
    return Pipeline([("scaler", StandardScaler()), ("model", estimator)])


# ── Public: training ──────────────────────────────────────────────────────────

def build_and_train(
    X: list[list[float]],
    y: list[float],
    model_type: str,
    target: str,
    hyperparams: dict,
    weights_path: str,
) -> int:
    """Entrena el modelo y guarda los pesos. Retorna la cantidad de muestras usadas.
    Esta función es SÍNCRONA — ejecutar con run_in_executor."""
    try:
        import numpy as np
    except ImportError:
        raise InternalException("numpy no está instalado.")

    X_arr = np.array(X, dtype="float64")
    y_arr = np.array(y, dtype="float64")

    if len(X_arr) < MIN_TRAINING_SAMPLES:
        raise BadRequestException(
            f"Datos insuficientes: se necesitan al menos {MIN_TRAINING_SAMPLES} muestras "
            f"con nota final registrada, se encontraron {len(X_arr)}."
        )

    pipeline = _build_estimator(model_type, target, hyperparams)
    pipeline.fit(X_arr, y_arr)

    Path(weights_path).parent.mkdir(parents=True, exist_ok=True)
    with open(weights_path, "wb") as f:
        pickle.dump(pipeline, f)

    return len(X_arr)


# ── Public: inference ─────────────────────────────────────────────────────────

def run_prediction(
    weights_path: str,
    X: list[list[float]],
    target: str,
) -> list[float]:
    """Carga el modelo y ejecuta predicciones. Retorna lista de floats.
    Esta función es SÍNCRONA — ejecutar con run_in_executor."""
    try:
        import numpy as np
    except ImportError:
        raise InternalException("numpy no está instalado.")

    if not Path(weights_path).exists():
        raise InternalException(f"Archivo de pesos no encontrado: {weights_path}")

    try:
        with open(weights_path, "rb") as f:
            pipeline = pickle.load(f)  # noqa: S301 — trusted internal file
    except Exception as exc:
        raise InternalException(f"Error cargando modelo: {exc}") from exc

    X_arr = np.array(X, dtype="float64")

    if target == "pass_probability":
        # predict_proba returns [[p_neg, p_pos], ...] for classifiers
        try:
            preds = pipeline.predict_proba(X_arr)[:, 1]
        except AttributeError:
            preds = pipeline.predict(X_arr)
        preds = np.clip(preds, 0.0, 1.0)
    else:
        # final_grade: regressor predicts normalized value (0–1), denormalize to 0–100
        preds = pipeline.predict(X_arr)
        preds = np.clip(preds * 100.0, 0.0, 100.0)

    return [round(float(p), 4) for p in preds]
