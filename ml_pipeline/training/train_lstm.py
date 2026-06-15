"""
Train LSTM close-price forecaster.
Produces lstm_close.keras + close_scaler.pkl dict artifact.
The scaler artifact format MUST match model_loader.py:
  { "scaler": MinMaxScaler, "window_size": int, "model_version": str }
"""

from __future__ import annotations
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

WINDOW_SIZE = 10
MODEL_VERSION = "lstm-close-v1"
MODEL_OUTPUT = Path("ml_pipeline/models/lstm_close.keras")
SCALER_OUTPUT = Path("ml_pipeline/models/close_scaler.pkl")
DATA_PATH = Path("ml_pipeline/data/raw/stock_market_data.csv")


def train_lstm(data_path: Path, model_out: Path, scaler_out: Path) -> None:
    df = pd.read_csv(data_path)
    close = pd.to_numeric(df["close"], errors="coerce").dropna().to_numpy(dtype=np.float32)

    # Use last 3000 rows for speed
    close = close[-3000:] if len(close) > 3000 else close

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(close.reshape(-1, 1)).ravel().astype(np.float32)

    # Build sliding windows
    X, y = [], []
    for i in range(WINDOW_SIZE, len(scaled)):
        X.append(scaled[i - WINDOW_SIZE:i])
        y.append(scaled[i])
    X = np.array(X, dtype=np.float32).reshape(-1, WINDOW_SIZE, 1)
    y = np.array(y, dtype=np.float32)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE, 1)),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.1),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(
        X_train,
        y_train,
        epochs=30,
        batch_size=32,
        validation_data=(X_test, y_test),
        callbacks=[EarlyStopping(patience=5, restore_best_weights=True)],
        verbose=1,
    )

    y_pred_scaled = model.predict(X_test, verbose=0).ravel()
    y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
    y_true = scaler.inverse_transform(y_test.reshape(-1, 1)).ravel()
    mae = float(np.mean(np.abs(y_true - y_pred)))
    print(f"LSTM test MAE: {mae:.4f}")

    model_out.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_out)

    # CRITICAL: artifact dict format must match model_loader.py
    joblib.dump(
        {"scaler": scaler, "window_size": WINDOW_SIZE, "model_version": MODEL_VERSION},
        scaler_out,
    )
    print(f"Saved model to {model_out}, scaler to {scaler_out}")


if __name__ == "__main__":
    train_lstm(DATA_PATH, MODEL_OUTPUT, SCALER_OUTPUT)
