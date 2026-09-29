from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env in project root or current working dir
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
if not ENV_FILE.exists():
    ENV_FILE = Path(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- LLM ---
    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_MODEL_SMALL: str = "gpt-4o-mini"
    OPENAI_MODEL_STRONG: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE_EXTRACT: float = 0.0
    LLM_TEMPERATURE_EVAL: float = 0.1
    LLM_TEMPERATURE_QUESTIONS: float = 0.5
    LLM_MOCK: bool = True
    ENABLE_LLM_FOLLOWUPS: bool = False
    ENABLE_VECTOR_RETRIEVAL: bool = False

    # --- Token budgets ---
    MAX_INPUT_CHARS_EXTRACTION: int = 24000
    MAX_INPUT_CHARS_QUESTIONS: int = 9000
    MAX_INPUT_CHARS_EVALUATION: int = 16000
    MAX_OUTPUT_TOKENS_EXTRACTION: int = 4000
    MAX_OUTPUT_TOKENS_QUESTIONS: int = 1800
    MAX_OUTPUT_TOKENS_EVALUATION: int = 3000
    PER_CANDIDATE_COST_CAP_USD: float = 0.50

    # --- GitHub ---
    GITHUB_TOKEN: str = ""
    GITHUB_MAX_REPOS: int = 3
    GITHUB_MAX_COMMITS_SCANNED: int = 100

    # --- Assessment ---
    MAX_TURNS: int = 8
    MAX_FOLLOWUPS_PER_QUESTION: int = 1
    ASSESSMENT_MAX_MINUTES: int = 30
    PER_QUESTION_MINUTES: int = 6
    ASSESSMENT_LINK_TTL_HOURS: int = 72
    VAGUE_ANSWER_MIN_WORDS: int = 40

    # --- Proctoring ---
    ENABLE_PROCTORING: bool = True
    PROCTORING_DISABLE_COPY_PASTE: bool = True
    PROCTORING_TRACK_TAB_SWITCH: bool = True
    PROCTORING_MAX_TAB_SWITCH_WARNINGS: int = 3

    # --- Scoring ---
    SPARSE_FACTOR: float = 0.5
    BAND_STRONG_MIN: float = 80.0
    BAND_MODERATE_MIN: float = 60.0

    # --- Auth ---
    HR_USERNAME: str = "hr"
    HR_PASSWORD: str = "adminpassword123"
    JWT_SECRET: str = "supersecret-candidatelens-jwt-key-2026"
    LINK_SIGNING_SECRET: str = "supersecret-candidatelens-link-key-2026"
    JWT_TTL_MINUTES: int = 480

    # --- Data ---
    DATA_DIR: str = "./data"
    RETENTION_DAYS: int = 90
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    @property
    def data_path(self) -> Path:
        p = Path(self.DATA_DIR)
        if not p.is_absolute():
            p = ROOT_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_path(self) -> Path:
        p = self.data_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def artifacts_path(self) -> Path:
        p = self.data_path / "artifacts"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_path(self) -> Path:
        p = self.data_path / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def database_url(self) -> str:
        db_file = self.data_path / "candidatelens.db"
        # SQLite URL with forward slashes
        return f"sqlite:///{db_file.as_posix()}"


settings = Settings()
