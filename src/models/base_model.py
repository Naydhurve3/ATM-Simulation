import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from src.utils import DATA_MODELS

class BaseModel:
    def __init__(self, name):
        self.name = name
        self.model = None
        self.model_path = DATA_MODELS / f"{name}.pkl"
        self.metrics = {}
        self.is_trained = False

    def train(self, *args, **kwargs):
        raise NotImplementedError

    def predict(self, *args, **kwargs):
        raise NotImplementedError

    def save(self):
        DATA_MODELS.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "metrics": self.metrics}, self.model_path)

    def load(self):
        if self.model_path.exists():
            data = joblib.load(self.model_path)
            self.model = data["model"]
            self.metrics = data.get("metrics", {})
            self.is_trained = True
            return True
        return False

    def delete_saved(self):
        if self.model_path.exists():
            self.model_path.unlink()
            self.is_trained = False
