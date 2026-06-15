from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    'close',
    'sma_5',
    'sma_20',
    'rsi_14',
    'macd_signal',
    'bb_width',
    'daily_return',
    'volume_zscore',
]


def compute_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    close = out['close'].astype(float)
    volume = out['volume'].astype(float)

    out['sma_5'] = close.rolling(5, min_periods=1).mean()
    out['sma_20'] = close.rolling(20, min_periods=1).mean()

    delta = close.diff().fillna(0.0)
    gain = delta.clip(lower=0.0).rolling(14, min_periods=1).mean()
    loss = (-delta.clip(upper=0.0)).rolling(14, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    out['rsi_14'] = 100 - (100 / (1 + rs.fillna(0.0)))

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    out['macd_signal'] = macd.ewm(span=9, adjust=False).mean()

    rolling_mean = close.rolling(20, min_periods=1).mean()
    rolling_std = close.rolling(20, min_periods=1).std(ddof=0).fillna(0.0)
    upper = rolling_mean + (2 * rolling_std)
    lower = rolling_mean - (2 * rolling_std)
    out['bb_width'] = ((upper - lower) / rolling_mean.replace(0, np.nan)).fillna(0.0)

    out['daily_return'] = close.pct_change().fillna(0.0)
    vol_mean = volume.rolling(20, min_periods=1).mean()
    vol_std = volume.rolling(20, min_periods=1).std(ddof=0).replace(0, np.nan)
    out['volume_zscore'] = ((volume - vol_mean) / vol_std).fillna(0.0)

    return out[FEATURE_COLUMNS].copy()