from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class LoadedModel:
    model: Any
    path: Path
    mtime: float
    version: str


_REGISTRY: dict[str, LoadedModel] = {}


def _candidate_paths(model_name: str) -> list[Path]:
    name = Path(model_name)
    aliases = [name]
    if name.name == 'xgb_model.pkl':
        aliases.append(Path('xgb.joblib'))
    if name.name == 'lstm_model.keras':
        aliases.append(Path('lstm_close.keras'))
    if name.name == 'scaler.pkl':
        aliases.append(Path('close_scaler.pkl'))

    repo_root = Path(__file__).resolve().parents[3]
    search_roots = [Path(settings.model_dir), Path.cwd(), Path.cwd().parent, repo_root, repo_root / 'ml_pipeline' / 'models', repo_root / 'backend' / 'models']
    paths: list[Path] = []
    for root in search_roots:
        for alias in aliases:
            candidate = alias if alias.is_absolute() else root / alias
            if candidate not in paths:
                paths.append(candidate)
    return paths


def _load_from_path(model_path: Path) -> Any:
    if model_path.suffix.lower() in {'.keras', '.h5'}:
        try:
            from tensorflow.keras.models import load_model as keras_load_model
        except Exception:  # noqa: BLE001
            return None
        try:
            return keras_load_model(model_path, compile=False)
        except Exception:  # noqa: BLE001
            return None

    try:
        return joblib.load(model_path)
    except Exception:  # noqa: BLE001
        return None


def _build_version(model_path: Path) -> str:
    try:
        mtime = int(model_path.stat().st_mtime)
    except Exception:
        mtime = 0
    return f"{settings.model_version}:{model_path.name}:{mtime}"


def get_model(model_name: str) -> tuple[Any, str]:
    cached = _REGISTRY.get(model_name)
    if cached and not settings.model_hot_reload:
        return cached.model, cached.version

    if cached and settings.model_hot_reload:
        try:
            if cached.path.exists() and cached.path.stat().st_mtime <= cached.mtime:
                return cached.model, cached.version
        except Exception:
            pass

    for model_path in _candidate_paths(model_name):
        if not model_path.exists():
            continue

        model = _load_from_path(model_path)
        if model is None:
            continue

        loaded = LoadedModel(
            model=model,
            path=model_path,
            mtime=model_path.stat().st_mtime,
            version=_build_version(model_path),
        )
        _REGISTRY[model_name] = loaded
        return loaded.model, loaded.version

    fallback_version = f"{settings.model_version}:{model_name}:missing"
    return None, fallback_version


def load_model(model_name: str) -> Any:
    model, _ = get_model(model_name)
    return model


def get_model_version(model_name: str) -> str:
    _, version = get_model(model_name)
    return version


def warmup_models() -> None:
    for model_name in ('xgb_model.pkl', 'lstm_model.keras', 'scaler.pkl'):
        model, version = get_model(model_name)
        logger.info('model_warmup name=%s status=%s version=%s', model_name, 'loaded' if model is not None else 'fallback', version)


def validate_required_models() -> None:
    required = ('xgb_model.pkl',)
    missing: list[str] = []
    for model_name in required:
        model, version = get_model(model_name)
        if model is None or 'missing' in version.lower():
            missing.append(f'{model_name} ({version})')
    if missing:
        raise RuntimeError(f'Required model artifacts are unavailable: {", ".join(missing)}')
