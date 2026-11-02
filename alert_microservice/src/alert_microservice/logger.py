import logging
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "app.log"

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[custom_logger]}</cyan> | "
    "<yellow>{extra[request_id]}</yellow> | "
    "user={extra[user_id]} | "
    "<level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        if record.name and record.name != "logging":
            custom_logger = record.name
        else:
            custom_logger = f"{record.filename}:{record.lineno}"

        logger.opt(depth=depth, exception=record.exc_info).bind(custom_logger=custom_logger, logger_name=record.name).log(level, record.getMessage())


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.configure(extra={"custom_logger": "app", "request_id": "-", "user_id": "-"})
    logger.add(sys.stderr, level="INFO", format=CONSOLE_FORMAT, enqueue=True, backtrace=True, diagnose=False)
    logger.add(LOG_FILE, level="INFO", serialize=True, rotation="500 MB", retention="10 days", enqueue=True, backtrace=True, diagnose=False)
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
    for logger_name in ("uvicorn", "uvicorn.error", "fastapi"):
        intercept_logger = logging.getLogger(logger_name)
        intercept_logger.handlers = [InterceptHandler()]
        intercept_logger.propagate = False
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)


setup_logging()