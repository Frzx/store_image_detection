from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict(
    env_file = "./.env",
    env_ignore_empty = True,
    extra = "ignore"
)

class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    model_config = _base_config

    @property
    def POSTGRES_URL(self):
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_SYNC_URL(self):
        return (
            f"postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    )
    
class CeleryRedisSettings(BaseSettings):
    CELERY_REDIS_HOST: str
    CELERY_REDIS_PORT: str
    CELERY_REDIS_DB: int

    model_config = _base_config

    @property
    def BROKER_URL(self):
        return f"redis://{self.CELERY_REDIS_HOST}:{self.CELERY_REDIS_PORT}/{self.CELERY_REDIS_DB}"

    @property
    def RESULT_BACKEND(self):
        return f"redis://{self.CELERY_REDIS_HOST}:{self.CELERY_REDIS_PORT}/{self.CELERY_REDIS_DB}"


class ModelSettings(BaseSettings):
    MODEL_ONNX_PATH: str = "models/detr-resnet-50.onnx"
    MODEL_REPO_ID: str = "facebook/detr-resnet-50"
    MODEL_HF_ONNX_FILENAME: str = "model.onnx"
    MODEL_EXPORT_OPSET: int = 18
    MODEL_IMAGE_SIZE: int = 800
    MODEL_SCORE_THRESHOLD: float = 0.3
    FRAME_EXTRACTION_INTERVAL_SECONDS: float = 0.5
    FFMPEG_BIN: str = "ffmpeg"

    model_config = _base_config


database_settings = DatabaseSettings()
celery_redis_settings = CeleryRedisSettings()
model_settings = ModelSettings()
