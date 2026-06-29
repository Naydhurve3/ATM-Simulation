import numpy as np
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dropout, Dense
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    _TF_AVAILABLE = True
except Exception:
    _TF_AVAILABLE = False
from src.models.base_model import BaseModel
from src.data_analysis import DataAnalysis
from src.utils import DATA_MODELS


class LSTMForecaster(BaseModel):
    def __init__(self):
        super().__init__("lstm_forecaster")
        self.lookback = 3
        self.scaler = None
        self.model_path_keras = DATA_MODELS / "lstm_forecaster.keras"
        self.scaler_path = DATA_MODELS / "lstm_scaler.pkl"

    def _get_data(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        da = DataAnalysis()
        trend = da.monthly_trend(bank_name, metric)
        values = trend[metric].values.astype(float)
        return values

    def _create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.lookback):
            X.append(data[i:i + self.lookback])
            y.append(data[i + self.lookback])
        return np.array(X).reshape(-1, self.lookback, 1), np.array(y)

    def _build_model(self):
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(self.lookback, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(), loss="mae")
        return model

    def is_available(self):
        return _TF_AVAILABLE

    def train(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        values = self._get_data(bank_name, metric)
        if len(values) < self.lookback + 1:
            self.metrics = {"MAE": None, "RMSE": None, "MAPE": None}
            return self

        self.scaler = MinMaxScaler()
        scaled = self.scaler.fit_transform(values.reshape(-1, 1)).flatten()

        X, y = self._create_sequences(scaled)

        self.model = self._build_model()
        es = EarlyStopping(patience=5, restore_best_weights=True)
        self.model.fit(X, y, epochs=50, batch_size=8, verbose=0, callbacks=[es])

        preds_scaled = self.model.predict(X, verbose=0).flatten()
        preds = self.scaler.inverse_transform(preds_scaled.reshape(-1, 1)).flatten()
        y_true = self.scaler.inverse_transform(y.reshape(-1, 1)).flatten()

        self.metrics = {
            "MAE": round(mean_absolute_error(y_true, preds), 2),
            "RMSE": round(np.sqrt(mean_squared_error(y_true, preds)), 2),
            "MAPE": round(np.mean(np.abs((y_true - preds) / (y_true + 1e-8))) * 100, 2),
        }

        self.is_trained = True
        DATA_MODELS.mkdir(parents=True, exist_ok=True)
        self.model.save(str(self.model_path_keras))
        joblib.dump(self.scaler, self.scaler_path)
        return self

    def predict(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        if not self.is_trained and not self.load():
            return {"error": "Model not trained"}

        values = self._get_data(bank_name, metric)
        if len(values) < self.lookback:
            return {"error": "Not enough data for prediction"}

        last_seq_scaled = self.scaler.transform(values[-self.lookback:].reshape(-1, 1)).flatten()
        X_input = last_seq_scaled.reshape(1, self.lookback, 1)

        mc_preds = []
        for _ in range(20):
            pred = self.model(X_input, training=True).numpy()[0, 0]
            mc_preds.append(pred)
        mc_preds = np.array(mc_preds)

        mean_scaled = np.mean(mc_preds)
        std_scaled = np.std(mc_preds)

        predicted_value = float(self.scaler.inverse_transform([[mean_scaled]])[0, 0])
        lower_bound = float(self.scaler.inverse_transform([[mean_scaled - 1.96 * std_scaled]])[0, 0])
        upper_bound = float(self.scaler.inverse_transform([[mean_scaled + 1.96 * std_scaled]])[0, 0])

        return {
            "predicted_value": round(predicted_value, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
        }

    def load(self):
        if self.model_path_keras.exists() and self.scaler_path.exists():
            self.model = load_model(str(self.model_path_keras))
            self.scaler = joblib.load(self.scaler_path)
            self.is_trained = True
            return True
        return False

    def backtest(self, bank_name=None, metric="DC_Vol_Cash_ATM", expand_by=1):
        values = self._get_data(bank_name, metric)
        if len(values) < self.lookback + 2:
            return []

        results = []
        for i in range(self.lookback, len(values) - 1, expand_by):
            train_vals = values[:i + 1]
            actual = values[i + 1]

            scaler = MinMaxScaler()
            train_scaled = scaler.fit_transform(train_vals.reshape(-1, 1)).flatten()

            X_train, y_train = self._create_sequences(train_scaled)

            model = self._build_model()
            es = EarlyStopping(patience=5, restore_best_weights=True)
            model.fit(X_train, y_train, epochs=50, batch_size=8, verbose=0, callbacks=[es])

            last_seq = train_scaled[-self.lookback:].reshape(1, self.lookback, 1)
            pred_scaled = model.predict(last_seq, verbose=0)[0, 0]
            pred = scaler.inverse_transform([[pred_scaled]])[0, 0]

            results.append((float(actual), float(pred)))

        if results:
            actuals = [r[0] for r in results]
            preds = [r[1] for r in results]
            mae = round(mean_absolute_error(actuals, preds), 2)
            rmse = round(np.sqrt(mean_squared_error(actuals, preds)), 2)
            results.append({"MAE": mae, "RMSE": rmse})

        return results
