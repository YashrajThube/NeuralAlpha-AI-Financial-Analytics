from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILES = (REPO_ROOT / '.env', REPO_ROOT / 'backend' / '.env')
PLACEHOLDER_SECRETS = {
    'your_newsapi_key_here',
    'rotate_in_gcp_and_set_restricted_key',
    'replace-with-long-random-secret',
    'change-me-in-prod',
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding='utf-8',
        extra='ignore',
        protected_namespaces=('settings_',),
    )

    app_name: str = 'NeuralAlpha API'
    environment: str = Field(default='development')
    debug: bool = Field(default=False)

    api_v1_prefix: str = '/api/v1'
    cors_origins: str = Field(
        default='http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5176,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176',
        validation_alias=AliasChoices('CORS_ORIGINS', 'CORS_ALLOWED_ORIGINS'),
    )
    public_api_key: str = Field(default='', validation_alias=AliasChoices('PUBLIC_API_KEY', 'API_KEY'))
    api_key_required: bool = Field(default=True, validation_alias=AliasChoices('API_KEY_REQUIRED', 'REQUIRE_API_KEY'))
    api_key_allowed_ips_raw: str = Field(default='', validation_alias=AliasChoices('API_KEY_ALLOWED_IPS', 'ALLOWED_IPS'))

    database_url: str = Field(default='mysql+aiomysql://neuralalpha:neuralalpha@127.0.0.1:3306/neuralalpha')

    jwt_secret_key: str = Field(default='change-me-in-prod')
    jwt_algorithm: str = Field(default='HS256')
    access_token_expire_minutes: int = Field(default=60)

    model_dir: str = Field(default='models')
    model_version: str = Field(default='v1')
    model_hot_reload: bool = Field(default=False)
    model_warmup_on_startup: bool = Field(default=True)
    enforce_real_models: bool = Field(default=False)

    redis_url: str = Field(default='redis://127.0.0.1:6379/0')
    cache_ttl_seconds: int = Field(default=600, ge=60, le=3600)
    cache_enabled: bool = Field(default=True)

    rate_limit_per_window: int = Field(default=3000, ge=10, le=5000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    max_request_body_bytes: int = Field(default=20000, ge=1024, le=2000000)
    strict_api_validation: bool = Field(default=False)

    gemini_api_key: str = Field(default='', validation_alias=AliasChoices('GOOGLE_API_KEY', 'GEMINI_API_KEY'))
    gemini_model: str = Field(default='gemini-1.5-flash')
    gemini_model_candidates: str = Field(default='gemini-1.5-flash,gemini-1.5-pro')
    llm_timeout: float = Field(default=1.0, ge=0.2, le=10.0, validation_alias=AliasChoices('LLM_TIMEOUT', 'LLM_TIMEOUT_SECONDS'))
    llm_secondary_timeout: float = Field(default=0.4, ge=0.1, le=5.0)

    monitoring_latency_alert_ms: float = Field(default=1500.0, ge=10.0, le=60000.0)
    monitoring_error_rate_alert: float = Field(default=0.1, ge=0.0, le=1.0)
    monitoring_fallback_alert: float = Field(default=0.2, ge=0.0, le=1.0)
    monitoring_slo_latency_ms: float = Field(default=3000.0, ge=100.0, le=60000.0)
    monitoring_slo_error_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    monitoring_anomaly_multiplier: float = Field(default=1.5, ge=1.0, le=10.0)
    monitoring_slo_window_minutes: int = Field(default=1, ge=1, le=1440)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip() and origin.strip() != '*']

    @property
    def api_key_allowed_ips(self) -> set[str]:
        return {ip.strip() for ip in self.api_key_allowed_ips_raw.split(',') if ip.strip()}

    @property
    def gemini_models(self) -> list[str]:
        ordered = [self.gemini_model, *self.gemini_model_candidates.split(',')]
        seen: set[str] = set()
        models: list[str] = []
        for model_name in ordered:
            normalized = model_name.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            models.append(normalized)
        return models

    @property
    def is_local_environment(self) -> bool:
        return self.environment.strip().lower() in {'local', 'dev', 'development', 'test'}

    @property
    def api_key_configured(self) -> bool:
        return bool(self.public_api_key.strip())

    @field_validator('public_api_key', 'gemini_api_key', mode='before')
    @classmethod
    def normalize_placeholder_secret(cls, value):
        if value is None:
            return ''
        text = str(value).strip()
        if text.lower() in PLACEHOLDER_SECRETS:
            return ''
        return text

    @field_validator('debug', mode='before')
    @classmethod
    def normalize_debug_flag(cls, value):
        if isinstance(value, str) and value.strip().lower() in {'release', 'prod', 'production'}:
            return False
        return value

    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        return self.rate_limit_per_window

    @RATE_LIMIT_PER_MINUTE.setter
    def RATE_LIMIT_PER_MINUTE(self, value: int) -> None:
        self.rate_limit_per_window = value

    @property
    def STRICT_API_VALIDATION(self) -> bool:
        return self.strict_api_validation

    @STRICT_API_VALIDATION.setter
    def STRICT_API_VALIDATION(self, value: bool) -> None:
        self.strict_api_validation = value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
