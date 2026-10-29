import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # AWS DynamoDB configuration
    aws_region: str = "us-east-1"
    dynamodb_table: str = "url_shortener"

    # Base URL for building shortened links (e.g. http://<ec2-ip>:8000)
    base_url: str = "http://localhost:8000"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS configuration
    cors_origins: str = "*"

    # Local development fallback
    use_mock_db: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins string into a list."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def clean_base_url(self) -> str:
        """Return base URL without trailing slash."""
        return self.base_url.rstrip("/")


settings = Settings()
