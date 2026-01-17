"""
Configuration management using Pydantic Settings for ansible-inspec server.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import List, Dict, Optional, Any, Union
import os


class AuthSettings(BaseSettings):
    """Authentication configuration"""
    enabled: bool = Field(default=False, description="Enable authentication")
    
    # Azure AD OAuth2
    azure_tenant_id: Optional[str] = Field(default=None, description="Azure AD Tenant ID")
    azure_client_id: Optional[str] = Field(default=None, description="Azure AD Client ID")
    azure_client_secret: Optional[str] = Field(default=None, description="Azure AD Client Secret")
    
    # JWT Settings
    jwt_secret: str = Field(
        default="dev-secret-change-in-production",
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiry in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry in days")
    
    # OAuth2 Settings
    oauth_redirect_uri: str = Field(
        default="http://localhost:8080/api/v1/auth/callback",
        description="OAuth2 redirect URI"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="AUTH__",
        env_nested_delimiter="__"
    )


class DatabaseSettings(BaseSettings):
    """Database configuration using Prisma ORM"""
    url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database URL for Prisma (no async driver prefix needed)"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="DATABASE__",
        env_nested_delimiter="__"
    )


class VCSSettings(BaseSettings):
    """Version Control System configuration"""
    enabled: bool = Field(default=False, description="Enable VCS sync")
    poll_interval_minutes: int = Field(default=15, description="Polling interval in minutes")
    config_dir: str = Field(default="./data/vcs_repos", description="VCS repositories directory")
    
    # Repositories configuration (can be JSON string or list)
    repositories: List[Dict[str, Any]] = Field(default_factory=list, description="VCS repositories")
    
    # Webhooks
    webhook_enabled: bool = Field(default=False, description="Enable webhook support")
    webhook_secret: Optional[str] = Field(default=None, description="Webhook secret for validation")
    
    model_config = SettingsConfigDict(
        env_prefix="VCS__",
        env_nested_delimiter="__"
    )


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration"""
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    alert_email: Optional[str] = Field(default=None, description="Email for alerts")
    alert_webhook: Optional[str] = Field(default=None, description="Webhook URL for alerts")
    
    model_config = SettingsConfigDict(
        env_prefix="MONITORING__",
        env_nested_delimiter="__"
    )


class Settings(BaseSettings):
    """Main application settings"""
    # General
    debug: bool = Field(default=False, description="Debug mode")
    data_dir: str = Field(default="./data", description="Data directory")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Storage
    storage_backend: str = Field(
        default="file",
        description="Storage backend: file, database, hybrid"
    )
    
    # Hybrid storage validation
    validation_days: int = Field(default=30, description="Hybrid storage validation period in days")
    auto_cutover: bool = Field(default=False, description="Automatic cutover after validation")
    
    # Encryption
    encryption_key: Optional[str] = Field(default=None, description="Fernet encryption key")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # CORS - accept string or list, will be converted to list
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:8081,http://localhost:3000",
        description="CORS allowed origins (comma-separated string or JSON list)"
    )
    
    # Sub-configurations
    auth: AuthSettings = Field(default_factory=AuthSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    vcs: VCSSettings = Field(default_factory=VCSSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables (e.g., from Docker Compose)
    )
    
    @field_validator('storage_backend')
    @classmethod
    def validate_storage_backend(cls, v: str) -> str:
        """Validate storage backend choice"""
        valid_backends = ['file', 'database', 'hybrid']
        if v not in valid_backends:
            raise ValueError(f"storage_backend must be one of {valid_backends}")
        return v
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from comma-separated string or list"""
        if v is None or v == "":
            return ["http://localhost:8081", "http://localhost:3000"]
        if isinstance(v, str):
            # Split by comma and strip whitespace
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
            return origins if origins else ["http://localhost:8081", "http://localhost:3000"]
        elif isinstance(v, list):
            return v
        return ["http://localhost:8081", "http://localhost:3000"]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings
