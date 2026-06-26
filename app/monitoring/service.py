# Application monitoring and logging with Loguru.
"""Logging configuration, metric tracking, and system monitoring utilities."""

from __future__ import annotations

import os
import platform
import sys
import time
import uuid
from datetime import datetime
from typing import Any

import psutil
from loguru import logger

from app.core import settings


class MonitoringService:
    """Application monitoring service using Loguru."""

    _initialized = False

    @classmethod
    def setup_logging(cls) -> None:
        """Configure Loguru logging with console and file handlers."""
        if cls._initialized:
            return

        # Remove default handler
        logger.remove()

        # Add console handler
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level=log_level,
            colorize=True,
        )

        # Add file handler with rotation
        log_file = settings.LOG_FILE
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
        )

        cls._initialized = True
        logger.info("Logging initialized at level {}", log_level)

    @staticmethod
    def get_cpu_percent() -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    @staticmethod
    def get_memory_usage_mb() -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    @staticmethod
    def get_system_info() -> dict:
        """Get system information."""
        return {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        }

    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID4 string."""
        return str(uuid.uuid4())


class Timer:
    """Simple context manager for timing code blocks."""

    def __init__(self, name: str = "timer"):
        self.name = name
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> Timer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000


# Initialize monitoring on import
MonitoringService.setup_logging()

__all__ = [
    "MonitoringService",
    "Timer",
    "logger",
]
