#!/usr/bin/env python3
"""
Experiment logging infrastructure.

This module provides structured logging with file and console handlers,
progress indicators, and phase markers for experiment orchestration.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler

try:
    from colorama import Fore, Style, init as colorama_init
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    COLORS = {
        'DEBUG': Fore.CYAN if COLORAMA_AVAILABLE else '',
        'INFO': Fore.GREEN if COLORAMA_AVAILABLE else '',
        'WARNING': Fore.YELLOW if COLORAMA_AVAILABLE else '',
        'ERROR': Fore.RED if COLORAMA_AVAILABLE else '',
        'CRITICAL': Fore.RED + Style.BRIGHT if COLORAMA_AVAILABLE else '',
    }
    
    RESET = Style.RESET_ALL if COLORAMA_AVAILABLE else ''
    
    def format(self, record):
        """Format log record with colors."""
        if COLORAMA_AVAILABLE:
            log_color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class PhaseFilter(logging.Filter):
    """Filter to add phase context to log records."""
    
    def __init__(self, phase: Optional[str] = None):
        super().__init__()
        self.phase = phase
    
    def filter(self, record):
        """Add phase to log record."""
        if self.phase:
            record.phase = f"[Phase: {self.phase}]"
        else:
            record.phase = ""
        return True


class ExperimentLogger:
    """
    Structured logger for experiment orchestration.
    
    Provides:
    - File logging with rotation
    - Console logging with colors (if colorama available)
    - Phase markers
    - Progress indicators
    """
    
    def __init__(
        self,
        name: str = "experiment",
        log_dir: Optional[Path] = None,
        level: str = "INFO",
        file_logging: bool = True,
        console_logging: bool = True,
        format_style: str = "detailed",
    ):
        """
        Initialize experiment logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files (if None, no file logging)
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            file_logging: Enable file logging
            console_logging: Enable console logging
            format_style: Format style ('simple' or 'detailed')
        """
        if COLORAMA_AVAILABLE:
            colorama_init(autoreset=True)
        
        self.name = name
        self.log_dir = log_dir
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.format_style = format_style
        self.current_phase: Optional[str] = None
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        self.logger.handlers.clear()  # Remove any existing handlers
        
        # Detailed format
        if format_style == "detailed":
            file_format = "[%(asctime)s] [%(levelname)s] %(phase)s %(message)s"
            console_format = "[%(asctime)s] [%(levelname)s] %(phase)s %(message)s"
        else:
            # Simple format
            file_format = "[%(levelname)s] %(message)s"
            console_format = "[%(levelname)s] %(message)s"
        
        # File handler
        if file_logging and log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(self.level)
            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            self.log_file = log_file
        else:
            self.log_file = None
        
        # Console handler
        if console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            if COLORAMA_AVAILABLE and format_style == "detailed":
                console_formatter = ColoredFormatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
            else:
                console_formatter = logging.Formatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Add phase filter
        self.phase_filter = PhaseFilter()
        self.logger.addFilter(self.phase_filter)
    
    def set_phase(self, phase: str) -> None:
        """
        Set current experiment phase.
        
        Args:
            phase: Phase name (e.g., "Generation", "Evaluation")
        """
        self.current_phase = phase
        self.phase_filter.phase = phase
    
    def clear_phase(self) -> None:
        """Clear current phase."""
        self.current_phase = None
        self.phase_filter.phase = None
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def phase_start(self, phase: str, message: str = "") -> None:
        """
        Log phase start.
        
        Args:
            phase: Phase name
            message: Optional message
        """
        self.set_phase(phase)
        if message:
            self.info(f"Starting {phase.lower()} phase: {message}")
        else:
            self.info(f"Starting {phase.lower()} phase...")
    
    def phase_end(self, phase: str, message: str = "") -> None:
        """
        Log phase end.
        
        Args:
            phase: Phase name
            message: Optional message
        """
        if message:
            self.info(f"✓ Completed {phase.lower()} phase: {message}")
        else:
            self.info(f"✓ Completed {phase.lower()} phase")
        self.clear_phase()
    
    def progress(self, current: int, total: int, item: str = "item") -> None:
        """
        Log progress update.
        
        Args:
            current: Current progress
            total: Total items
            item: Item name (e.g., "test", "evaluation")
        """
        percentage = (current / total * 100) if total > 0 else 0
        self.info(f"Progress: {current}/{total} {item}(s) ({percentage:.1f}%)")
    
    def success(self, message: str) -> None:
        """
        Log success message.
        
        Args:
            message: Success message
        """
        if COLORAMA_AVAILABLE:
            self.info(f"{Fore.GREEN}✓{Style.RESET_ALL} {message}")
        else:
            self.info(f"✓ {message}")
    
    def failure(self, message: str) -> None:
        """
        Log failure message.
        
        Args:
            message: Failure message
        """
        if COLORAMA_AVAILABLE:
            self.error(f"{Fore.RED}✗{Style.RESET_ALL} {message}")
        else:
            self.error(f"✗ {message}")
    
    def section(self, title: str) -> None:
        """
        Log section header.
        
        Args:
            title: Section title
        """
        self.info("")
        self.info("=" * 60)
        self.info(title)
        self.info("=" * 60)
    
    def get_log_file(self) -> Optional[Path]:
        """
        Get path to log file.
        
        Returns:
            Path to log file or None if file logging disabled
        """
        return self.log_file


class ProgressBar:
    """Progress bar wrapper using tqdm if available, otherwise simple logging."""
    
    def __init__(self, total: int, desc: str = "", logger: Optional[ExperimentLogger] = None):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items
            desc: Description
            logger: Logger for fallback if tqdm not available
        """
        self.total = total
        self.desc = desc
        self.logger = logger
        self.current = 0
        
        if TQDM_AVAILABLE:
            self.pbar = tqdm(total=total, desc=desc, unit="item")
        else:
            self.pbar = None
            if logger:
                logger.info(f"Starting: {desc} ({total} items)")
    
    def update(self, n: int = 1) -> None:
        """
        Update progress.
        
        Args:
            n: Number of items completed
        """
        self.current += n
        if self.pbar:
            self.pbar.update(n)
        elif self.logger and self.current % max(1, self.total // 10) == 0:
            # Log every 10%
            percentage = (self.current / self.total * 100) if self.total > 0 else 0
            self.logger.info(f"{self.desc}: {self.current}/{self.total} ({percentage:.1f}%)")
    
    def close(self) -> None:
        """Close progress bar."""
        if self.pbar:
            self.pbar.close()
        elif self.logger:
            self.logger.info(f"Completed: {self.desc} ({self.current}/{self.total})")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Test logger
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ExperimentLogger(
            name="test",
            log_dir=Path(tmpdir),
            level="DEBUG",
            format_style="detailed"
        )
        
        logger.section("Test Logging")
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        
        logger.phase_start("Generation", "Testing phase markers")
        logger.success("Success!")
        logger.failure("Failure!")
        logger.phase_end("Generation", "Phase complete")
        
        logger.progress(5, 10, "tests")
        
        print(f"\nLog file: {logger.get_log_file()}")
