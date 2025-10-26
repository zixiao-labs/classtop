from loguru import logger
from pathlib import Path
import sys
from typing import List
import inspect

# Place logs in user home directory under .classtop
APP_DIR = Path.home() / ".classtop"
APP_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Configure loguru
logger.remove()

# Terminal sink: enable colors and show file/function/line (only if stderr is available)
if sys.stderr is not None:
    try:
        TERMINAL_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        logger.add(sys.stderr, level="INFO", colorize=True, format=TERMINAL_FORMAT)
    except Exception:
        # In production mode without console, stderr might not be writable
        pass

# File sink: plain text with full context
FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
logger.add(str(LOG_FILE), rotation="10 MB", retention="10 days", encoding="utf-8", level="DEBUG", format=FILE_FORMAT)

def init_logger():
    logger.info("Logger initialized")


def _caller_depth() -> int:
    """Return number of stack frames to skip so loguru reports the original caller.

    We need to skip the frames inside this module (wrapper functions) so loguru
    reports the user's calling file/line instead of this module.
    """
    # Walk the stack until we find a frame outside this file
    current_file = Path(__file__).resolve()
    for depth, frame_info in enumerate(inspect.stack()):
        try:
            fpath = Path(frame_info.filename).resolve()
            if fpath != current_file:
                # We need to subtract 1 because:
                # - enumerate starts at 0 (this function's frame)
                # - depth=1 would be log_message's frame
                # - depth=2+ would be the actual caller
                # But loguru's opt(depth=N) counts from the opt() call itself,
                # so we need to adjust by -1 to get the right frame
                return max(0, depth - 1)
        except Exception:
            continue
    return 0


def log_message(level: str, message: str) -> None:
    """Log a message at given level (debug/info/warning/error/critical).

    Uses logger.opt(depth=...) to skip the wrapper and report the actual caller.
    """
    level = (level or "info").upper()
    depth = _caller_depth()
    try:
        # Use logger.opt to skip wrapper frames and then call logger.log with the
        # provided level string. logger.log accepts level names like "INFO".
        logger.opt(depth=depth).log(level, message)
    except Exception:
        # fallback to plain logger.log if something goes wrong
        logger.log(level, message)


def tail_logs(lines: int = 200) -> List[str]:
    """Return the last `lines` lines from the log file as a list of strings."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return [l.rstrip("\n") for l in all_lines[-lines:]]
    except FileNotFoundError:
        return []
