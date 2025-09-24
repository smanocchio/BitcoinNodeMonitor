"""Process and system metrics."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import psutil

LOGGER = logging.getLogger(__name__)


def collect_process_metrics(process_name: str = "bitcoind") -> Optional[dict[str, float]]:
    """Return CPU%, RSS MB, and open file descriptors for a named process."""

    for proc in psutil.process_iter(["name", "cpu_percent", "memory_info", "num_fds"]):
        if proc.info.get("name") == process_name:
            memory = proc.info.get("memory_info")
            return {
                "cpu_percent": float(proc.info.get("cpu_percent", 0.0)),
                "memory_rss_mb": float(getattr(memory, "rss", 0) / (1024 * 1024) if memory else 0),
                "open_files": float(proc.info.get("num_fds", 0)),
            }
    LOGGER.debug("Process not found for metrics collection", extra={"process": process_name})
    return None


def collect_disk_usage(path: str | None) -> Optional[dict[str, float]]:
    """Return disk usage statistics for ``path`` if it exists.

    When the path is missing (for example, when the chainstate directory is not mounted
    inside the collector container) we log a debug message and return ``None`` so that
    callers can skip emitting filesystem metrics instead of failing.
    """

    if not path:
        LOGGER.debug("Disk metrics disabled; no path provided")
        return None

    try:
        usage = psutil.disk_usage(str(Path(path)))
    except FileNotFoundError:
        LOGGER.debug("Disk path not found for metrics collection", extra={"path": path})
        return None
    except Exception as exc:  # pragma: no cover - defensive guard
        LOGGER.warning("Unexpected disk usage error", exc_info=exc, extra={"path": path})
        return None

    return {
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_percent": round((usage.free / usage.total) * 100, 2),
    }
