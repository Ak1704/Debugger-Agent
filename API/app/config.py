from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GITHUB_TOKEN: str = ""
    GITHUB_CACHE_DIR: str = "./cache/github"
    CHROMA_DIR: str = "./cache/chroma"
    DOCKER_IMAGE: str = "universal-ci-debugger-sandbox"
    DOCKER_TIMEOUT: int = 300
    MAX_ITERATIONS: int = 3
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
