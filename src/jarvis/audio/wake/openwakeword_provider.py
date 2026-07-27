"""Wake word con OpenWakeWord."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from jarvis.config.loader import WakeConfig
from jarvis.utils.logging import get_logger


class OpenWakeWordProvider:
    name = "openwakeword"

    def __init__(self, cfg: WakeConfig) -> None:
        from openwakeword.model import Model
        from openwakeword.utils import download_models

        self._cfg = cfg
        self._log = get_logger("jarvis.wake")
        # Asegura ONNX locales (hey_jarvis, etc.)
        try:
            download_models()
        except Exception as exc:  # noqa: BLE001
            self._log.warning("wake_model_download_issue", error=str(exc))
        self._model = Model(
            wakeword_models=[cfg.model],
            inference_framework="onnx",
        )
        self._key = cfg.model
        self._log.info("wake_loaded", model=cfg.model)

    def reset(self) -> None:
        self._model.reset()

    def score(self, chunk: NDArray[np.int16]) -> float:
        preds = self._model.predict(chunk)
        value = preds.get(self._key, 0.0)
        return float(value)

    def detected(self, chunk: NDArray[np.int16], threshold: float) -> bool:
        return self.score(chunk) > threshold
