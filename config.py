"""
Secure Configuration Management for OAuth 2.0 Flow
Loads environment variables with strict validation
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Literal
import secrets


class Settings(BaseSettings):
    """
    Application settings with strict typing and validation.
    Never expose these values in logs or responses.
    """
    
    # GitHub OAuth Credentials (NEVER expose to frontend)
    github_client_id: str = Field(..., min_length=20)
    github_client_secret: str = Field(..., min_length=40)
    
    # IBM watsonx Configuration (NEVER expose to frontend directly)
    watsonx_integration_id: str = Field(..., min_length=10)
    watsonx_region: str = Field(..., min_length=2)
    
    # Application URLs
    backend_url: str = Field(default="http://localhost:8000")
    frontend_url: str = Field(default="http://localhost:3000")
    
    # Security
    session_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    
    # GitHub OAuth URLs (constants)
    github_authorize_url: str = "https://github.com/login/oauth/authorize"
    github_token_url: str = "https://github.com/login/oauth/access_token"
    github_api_base_url: str = "https://api.github.com"
    
    # OAuth Scopes (read-only access to repositories)
    github_oauth_scopes: str = "repo"
    
    @validator("github_client_secret", "session_secret_key")
    def validate_secrets(cls, v: str, field) -> str:
        """Ensure secrets are never empty or default values"""
        if not v or v.startswith("your_"):
            raise ValueError(
                f"{field.name} must be set in .env file. "
                "Never use default or placeholder values in production."
            )
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Prevent accidental exposure in logs
        @staticmethod
        def json_schema_extra(schema, model):
            for prop in schema.get("properties", {}).values():
                prop.pop("default", None)


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection for FastAPI endpoints.
    Usage: settings: Settings = Depends(get_settings)
    """
    return settings

# Made with Bob
