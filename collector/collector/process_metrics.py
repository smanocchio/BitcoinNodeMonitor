"""Process and system metrics."""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover
    import psutil  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore[assignment]


def collect_process_metrics(process_name: str = "bitcoind") -> dict[str, float]:
    """Return CPU%, RSS MB, and open file descriptors for a named process."""

    if psutil is None:
        raise RuntimeError("psutil is required to collect process metrics")
    for proc in psutil.process_iter(["name", "cpu_percent", "memory_info", "num_fds"]):
        if proc.info.get("name") == process_name:
            memory = proc.info.get("memory_info")
            return {
                "cpu_percent": float(proc.info.get("cpu_percent", 0.0)),
                "memory_rss_mb": float(getattr(memory, "rss", 0) / (1024 * 1024) if memory else 0),
                "open_files": float(proc.info.get("num_fds", 0)),
            }
    return {"cpu_percent": 0.0, "memory_rss_mb": 0.0, "open_files": 0.0}


def collect_disk_usage(path: str) -> dict[str, float]:
    if psutil is None:
        raise RuntimeError("psutil is required to collect disk usage")
    usage = psutil.disk_usage(str(Path(path)))
    return {
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_percent": round((usage.free / usage.total) * 100, 2),
    }
