import json
import logging
import sys
from datetime import datetime, timezone

from app.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "candidate_id"):
            log_obj["candidate_id"] = getattr(record, "candidate_id")
        if hasattr(record, "stage"):
            log_obj["stage"] = getattr(record, "stage")
        if hasattr(record, "model"):
            log_obj["model"] = getattr(record, "model")
        if hasattr(record, "metrics"):
            log_obj["metrics"] = getattr(record, "metrics")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging():
    log_file = settings.logs_path / "app.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if re-initialized
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = JSONFormatter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("candidatelens")
