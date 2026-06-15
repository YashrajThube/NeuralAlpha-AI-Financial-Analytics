"""Organize NeuralAlpha datasets into a production-ready raw data layout.

Tasks performed:
1. Ensure ml_pipeline/data/raw exists.
2. Resolve sources named archive (2) to archive (5) as directory/zip/csv.
3. Extract zips when needed and keep only CSV content.
4. Rename and move to canonical file names.
5. Cleanup temporary and unnecessary source artifacts.
6. Validate final CSV readability with pandas and print first five rows.
"""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd


LOGGER = logging.getLogger("setup_data")

DATASET_RENAME_MAP: dict[str, str] = {
    "archive (2)": "stock_market_data.csv",
    "archive (3)": "crypto_market_data.csv",
    "archive (4)": "financial_news_data.csv",
    "archive (5)": "reddit_sentiment_data.csv",
}


def configure_logging() -> None:
    """Configure structured logging for script execution."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_project_root() -> Path:
    """Resolve repository root from current script location."""
    return Path(__file__).resolve().parents[2]


def get_data_root(project_root: Path) -> Path:
    """Return path to ml_pipeline/data directory."""
    return project_root / "ml_pipeline" / "data"


def ensure_raw_dir(data_root: Path) -> Path:
    """Create raw directory if it does not exist."""
    raw_dir = data_root / "raw"
    os.makedirs(raw_dir, exist_ok=True)
    LOGGER.info("Ensured raw directory: %s", raw_dir)
    return raw_dir


def find_candidate_paths(data_root: Path, source_key: str) -> list[Path]:
    """Find source candidates for a given archive key."""
    candidates: list[Path] = []
    for item in data_root.iterdir():
        if item.name == "raw":
            continue
        item_stem = item.stem.lower()
        key = source_key.lower()
        if item_stem == key or item.name.lower() == key:
            candidates.append(item)
            continue
        if item_stem.startswith(key) or item.name.lower().startswith(key):
            candidates.append(item)
    return candidates


def choose_best_candidate(candidates: list[Path]) -> Path | None:
    """Choose best candidate by priority: csv > directory > zip > other."""
    if not candidates:
        return None

    def rank(path: Path) -> tuple[int, str]:
        if path.is_file() and path.suffix.lower() == ".csv":
            return (0, path.name)
        if path.is_dir():
            return (1, path.name)
        if path.is_file() and path.suffix.lower() == ".zip":
            return (2, path.name)
        return (3, path.name)

    return sorted(candidates, key=rank)[0]


def collect_csvs_from_directory(directory: Path) -> list[Path]:
    """Collect all CSV files recursively from a directory."""
    return [p for p in directory.rglob("*.csv") if p.is_file()]


def extract_zip_to_temp(zip_path: Path, temp_dir: Path) -> list[Path]:
    """Extract ZIP archive and return discovered CSV files."""
    LOGGER.info("Extracting ZIP source: %s", zip_path)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    return [p for p in temp_dir.rglob("*.csv") if p.is_file()]


def select_primary_csv(csv_files: list[Path], source_name: str) -> Path:
    """Select primary dataset CSV, preferring largest file size."""
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for source: {source_name}")
    csv_files.sort(key=lambda p: p.stat().st_size, reverse=True)
    return csv_files[0]


def move_to_target_csv(source_csv: Path, target_csv: Path) -> None:
    """Move a resolved source CSV into final target location."""
    if target_csv.exists():
        target_csv.unlink()
    shutil.move(str(source_csv), str(target_csv))
    LOGGER.info("Created canonical dataset: %s", target_csv)


def cleanup_source_artifact(path: Path) -> None:
    """Remove source artifact after successful conversion."""
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        LOGGER.info("Removed source directory: %s", path)
    else:
        path.unlink(missing_ok=True)
        LOGGER.info("Removed source file: %s", path)


def process_one_dataset(data_root: Path, raw_dir: Path, source_key: str, target_name: str) -> bool:
    """Process one dataset from archive source to canonical raw CSV."""
    candidates = find_candidate_paths(data_root, source_key)
    source = choose_best_candidate(candidates)
    target_csv = raw_dir / target_name

    if source is None:
        LOGGER.error("Source not found for key: %s", source_key)
        return False

    LOGGER.info("Processing %s from source: %s", source_key, source)

    temp_dir = data_root / "_tmp_setup_data"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        csv_candidates: list[Path]

        if source.is_file() and source.suffix.lower() == ".csv":
            csv_candidates = [source]
        elif source.is_dir():
            csv_candidates = collect_csvs_from_directory(source)
        elif source.is_file() and source.suffix.lower() == ".zip":
            csv_candidates = extract_zip_to_temp(source, temp_dir)
        else:
            LOGGER.error("Unsupported source type for %s: %s", source_key, source)
            return False

        primary_csv = select_primary_csv(csv_candidates, source_key)
        move_to_target_csv(primary_csv, target_csv)

        cleanup_source_artifact(source)
        return True
    except (FileNotFoundError, zipfile.BadZipFile, OSError) as exc:
        LOGGER.exception("Failed processing %s: %s", source_key, exc)
        return False
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            LOGGER.info("Removed temporary extraction directory: %s", temp_dir)


def cleanup_non_csv_in_raw(raw_dir: Path) -> None:
    """Delete non-CSV files from raw directory."""
    for item in raw_dir.iterdir():
        if item.is_file() and item.suffix.lower() != ".csv":
            item.unlink(missing_ok=True)
            LOGGER.info("Deleted non-CSV from raw directory: %s", item)


def validate_and_preview(raw_dir: Path) -> None:
    """Validate all final datasets with pandas and print top rows."""
    LOGGER.info("Validating canonical datasets with pandas")
    for final_name in DATASET_RENAME_MAP.values():
        csv_path = raw_dir / final_name
        if not csv_path.exists():
            LOGGER.error("Missing required dataset: %s", csv_path)
            continue

        try:
            df = pd.read_csv(csv_path)
            LOGGER.info("Readable dataset: %s | rows=%d cols=%d", csv_path.name, len(df), len(df.columns))
            print(f"\n===== {csv_path.name} : first 5 rows =====")
            print(df.head(5).to_string(index=False))
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Pandas read failed for %s: %s", csv_path, exc)


def run() -> int:
    """Run full dataset organization workflow."""
    configure_logging()

    project_root = get_project_root()
    data_root = get_data_root(project_root)
    raw_dir = ensure_raw_dir(data_root)

    success = 0
    for source_key, target_name in DATASET_RENAME_MAP.items():
        if process_one_dataset(data_root, raw_dir, source_key, target_name):
            success += 1

    cleanup_non_csv_in_raw(raw_dir)
    validate_and_preview(raw_dir)

    LOGGER.info("Dataset setup complete: %d/%d successful", success, len(DATASET_RENAME_MAP))
    return 0 if success == len(DATASET_RENAME_MAP) else 1


if __name__ == "__main__":
    raise SystemExit(run())
