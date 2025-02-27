"""
Logging utility for i3ctl.
"""

import logging
import os
import sys
from typing import Dict, Optional, TextIO, Union, List
from enum import Enum
import atexit


# Define TRACE level value once
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")

class LogLevel(Enum):
    """Enum for log levels with verbosity mapping."""
    ERROR = logging.ERROR        # -q/--quiet
    WARNING = logging.WARNING    # default
    INFO = logging.INFO          # -v
    DEBUG = logging.DEBUG        # -vv
    TRACE = TRACE_LEVEL          # -vvv (custom level below DEBUG)


class Logger:
    """Class-based logger with enhanced functionality."""
    
    # Reference to the custom log level
    TRACE = TRACE_LEVEL
    
    def __init__(self, name: str = "i3ctl"):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.handlers: List[logging.Handler] = []
        self.log_file: Optional[str] = None
        self.verbosity = 0
        
        # Set default level
        self.set_level(LogLevel.WARNING)
        
        # Register cleanup
        atexit.register(self.cleanup)
    
    def trace(self, msg: str, *args, **kwargs) -> None:
        """
        Log at TRACE level (more detailed than DEBUG).
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.log(self.TRACE, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """
        Log at DEBUG level.
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """
        Log at INFO level.
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """
        Log at WARNING level.
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """
        Log at ERROR level.
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """
        Log at CRITICAL level.
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.critical(msg, *args, **kwargs)
        
    def exception(self, msg: str, *args, **kwargs) -> None:
        """
        Log an exception with traceback at ERROR level.
        
        Args:
            msg: Message to log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.logger.exception(msg, *args, **kwargs)
    
    def set_level(self, level: Union[int, LogLevel]) -> None:
        """
        Set the logging level.
        
        Args:
            level: Logging level (int or LogLevel enum)
        """
        if isinstance(level, LogLevel):
            level = level.value
            
        self.logger.setLevel(level)
    
    def set_verbosity(self, verbosity: int) -> None:
        """
        Set verbosity level and adjust log level accordingly.
        
        Args:
            verbosity: Verbosity level (0-3)
        """
        self.verbosity = verbosity
        
        if verbosity <= -1:  # quiet
            self.set_level(LogLevel.ERROR)
        elif verbosity == 0:  # default
            self.set_level(LogLevel.WARNING)
        elif verbosity == 1:  # -v
            self.set_level(LogLevel.INFO)
        elif verbosity == 2:  # -vv
            self.set_level(LogLevel.DEBUG)
        else:  # -vvv or higher
            self.set_level(self.TRACE)
    
    def add_file_handler(self, log_file: str) -> None:
        """
        Add a file handler to the logger.
        
        Args:
            log_file: Path to log file
        """
        if not log_file:
            return
            
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Add handler
        self.logger.addHandler(file_handler)
        self.handlers.append(file_handler)
        self.log_file = log_file
    
    def add_console_handler(self, stream: TextIO = sys.stdout) -> None:
        """
        Add a console handler to the logger.
        
        Args:
            stream: Stream to log to
        """
        # Create formatter - simpler for console
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        
        # Create console handler
        console_handler = logging.StreamHandler(stream)
        console_handler.setFormatter(formatter)
        
        # Add handler
        self.logger.addHandler(console_handler)
        self.handlers.append(console_handler)
    
    def cleanup(self) -> None:
        """Clean up handlers when the program exits."""
        for handler in self.handlers:
            handler.close()
            self.logger.removeHandler(handler)


# Create default logger instance
logger = Logger()
logger.add_console_handler()


def setup_logger(
    name: str = "i3ctl",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    stream: Optional[TextIO] = sys.stdout,
) -> Logger:
    """
    Set up and configure logger (backward compatibility function).

    Args:
        name: Logger name
        level: Logging level
        log_file: Optional path to log file
        stream: Optional stream to log to (default: sys.stdout)

    Returns:
        Configured logger instance
    """
    # Use the new Logger class
    logger_instance = Logger(name)
    
    # Set level
    logger_instance.set_level(level)
    
    # Add console handler if stream is provided
    if stream:
        logger_instance.add_console_handler(stream)
    
    # Add file handler if log_file is provided
    if log_file:
        logger_instance.add_file_handler(log_file)
    
    return logger_instance