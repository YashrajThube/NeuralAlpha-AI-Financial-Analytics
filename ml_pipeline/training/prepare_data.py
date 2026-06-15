import yfinance as yf
import pandas as pd
from pathlib import Path

SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]
OUTPUT_DIR = Path("ml_pipeline/data/raw")


def download_and_merge():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for sym in SYMBOLS:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2y")
            if hist.empty:
                continue
            hist = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
            hist.columns = ["open", "high", "low", "close", "volume"]
            hist["symbol"] = sym
            hist.index.name = "timestamp"
            hist = hist.reset_index()
            frames.append(hist)
        except Exception as exc:
            print(f"Skipping {sym} due to upstream fetch error: {exc}")

    out = OUTPUT_DIR / "stock_market_data.csv"
    if not frames:
        if out.exists():
            existing = pd.read_csv(out)
            print(f"Using existing dataset at {out} (rows={len(existing)})")
            return existing
        raise RuntimeError("No market data downloaded and no existing local dataset found.")

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values("timestamp").reset_index(drop=True)
    merged.to_csv(out, index=False)
    print(f"Saved {len(merged)} rows to {out}")
    return merged


if __name__ == "__main__":
    download_and_merge()