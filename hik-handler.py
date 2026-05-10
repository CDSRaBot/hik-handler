"""
File: hik-handler.py
Path: /hik-handler.py
Code name: ENTRY_POINT
Version: v.1.0.1
"""

import logging
import sys
from app.engine.orchestrator import Orchestrator
from app.engine.logger import setup_logger

# Initial logger for entry point bootstrap
# Note: It will use default settings until setup_logger is called
logger = logging.getLogger(__name__)

def main():
    """
    Main application entry point.
    Coordinates core bootstrap, infrastructure setup, and command execution.
    """
    logger.info("Initializing Hik-handler system...")
    
    try:
        # Step 1: Bootstrap the core to load configuration
        # This is required to get paths and settings for the logger
        orchestrator = Orchestrator.bootstrap("config.toml")
        
        # Step 2: Initialize infrastructure (Logging)
        # We pass the loaded config object to configure file rotation and levels
        setup_logger(orchestrator.config)
        logger.info("Infrastructure and logging are successfully initialized.")
        
        logger.info("--- Hik-handler Session Started ---")
        
        # Step 3: Determine execution mode based on CLI arguments
        if len(sys.argv) > 1:
            # Headless mode for integration (scripts, external calls)
            logger.info("Executing in headless integration mode.")
            orchestrator.execute_headless(sys.argv[1:])
        else:
            # Interactive mode (REPL terminal)
            logger.info("Starting interactive terminal session.")
            orchestrator.run_command()
            
        logger.info("--- Hik-handler Session Finished ---")
        
    except KeyboardInterrupt:
        # Silent exit on user interrupt (Ctrl+C)
        logger.info("Application execution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        # Catch and log any unhandled critical errors
        logger.exception(f"Unhandled critical system error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()