"""Configuration management using Pydantic Settings."""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("TESTING") != "1" else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    db_connection_string: str = Field(
        default="sqlite:///:memory:",
        description="Database connection string for Azure SQL",
    )

    # Application Configuration
    app_name: str = Field(default="azure-cloud-grooming-service", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")


settings = Settings()
