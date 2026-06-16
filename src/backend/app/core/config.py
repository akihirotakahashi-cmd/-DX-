from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/chihousousei_dx"

    # AWS Cognito (DEC-029)
    COGNITO_REGION: str = "ap-northeast-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""

    # AWS S3 (DEC-018)
    S3_BUCKET_PROPOSALS: str = "chihousousei-dx-proposals"
    S3_REGION: str = "ap-northeast-1"

    # Amazon SES (DEC-007)
    SES_REGION: str = "ap-northeast-1"
    SES_FROM_EMAIL: str = "no-reply@example.com"

    # Claude API (DEC-028)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Portal base URL (SCR-14)
    PORTAL_BASE_URL: str = "http://localhost:3000"


settings = Settings()
