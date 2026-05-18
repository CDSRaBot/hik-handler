# File: logger.py
# Path: app/engine/logger.py
# Code Name: LogManager
# Version: 1.1.0

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any

def setup_logger(config: Any) -> logging.Logger:
    """
    Initializes and configures the hik_handler logger as a parent for the whole app.
    
    Args:
        config (Any): Configuration object containing 'data' attribute.
        
    Returns:
        logging.Logger: Configured logger instance (Singleton pattern).
    """
    # Define the base name for the project logger hierarchy
    base_name = "hik_handler"
    logger = logging.getLogger(base_name)

    # Guard clause: prevent adding multiple handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Extract configuration data safely
    config_data = getattr(config, "data", {}) if config else {}
    log_settings = config_data.get("logging", {})
    
    # Define log directory and ensure it exists
    log_dir = config_data.get("paths", {}).get("log_dir", "logs")
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Set logging level (default to INFO)
    log_level_str = log_settings.get("level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    # Format: Timestamp - Level - Module - Message
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # 1. File Handler (Rotating)
    log_file = log_dir_path / "hik-handler.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_settings.get("max_size_mb", 5) * 1024 * 1024,
        backupCount=log_settings.get("backup_count", 3),
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    
    # 2. Console Handler (for CLI feedback)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    # Set to CRITICAL to suppress technical noise on screen; UI will handle error display
    console_handler.setLevel(logging.CRITICAL)
    
    # Attach handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Ensure this logger is the root for all project sub-modules
    logger.propagate = True

    # Initial logs
    logger.info("\n ===============<   Initializing Hik-handler system...   >=============== \n")
    logger.debug(f"Logger infrastructure ready. Root: {base_name}, Level: {log_level_str}")
    logger.info("Logging system initialized (File & Console).")
    
    return logger