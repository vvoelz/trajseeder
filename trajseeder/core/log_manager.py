import json
import logging
import threading
from pathlib import Path
from datetime import datetime, timezone


class JsonlFormatter(logging.Formatter):
    """ Formats each log record as JSON object (1 per line) """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            #"level": record.levelname,
            #"logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def create_logger(job_path: Path, job_id: str) -> logging.Logger:

    logger = logging.getLogger(f"Job#{job_id}")

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_path = job_path / "job.log"
        handler = logging.FileHandler(log_path)
        handler.setFormatter(JsonlFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


class Heartbeat:
    """ 
    Adds a statement to our log file every 30 seconds to prevent silent
    crashes. 
    """

    def __init__(self, logger: logging.Logger, interval: float = 30.0):
        self.logger = logger
        self.interval = interval
        self._stop_flag = threading.Event()
        self._thread: threading.Thread | None = None

    def __loop(self):
        while not self._stop_flag.is_set():
            self.logger.info("heartbeat")
            self._stop_flag.wait(self.interval)

    def start(self):
        self._thread = threading.Thread(target=self.__loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=5)


def time_since_last_heartbeat(log_path: Path) -> float:
    """
    Takes in the path to job.log
    Returns seconds since the last heartbeat
    Returns float('inf') if no heartbeat has ever been recorded
    to catch edge case of crash before heartbeat.
    """
    if not log_path.exists():
        return None

    last_ts = None
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip any malformed/partial line, e.g. mid-write
            if record.get("message") == "heartbeat":
                last_ts = record["timestamp"]

    if last_ts is None:
        return float("inf")
    
    last_ts = datetime.fromisoformat(last_ts)
    now = datetime.now(timezone.utc)

    return (now - last_ts).total_seconds()