"""
File: post_processors.py
Path: app/engine/post_processors.py
Codename: PostProcessorBase
Version: v.1.0.0

Abstract base class for post-processing command responses.
Allows decoupling output/export logic from the core Orchestrator.
"""

from abc import ABC, abstractmethod
import csv
import logging
from typing import Any, Dict
from pathlib import Path
from app.configuration.security import SecureContext

# Module-level logger
logger = logging.getLogger(f"hik_handler.{__name__}")

class BasePostProcessor(ABC):
    """
    Interface for response post-processors.
    All export or secondary processing logic must implement this.
    """

    @abstractmethod
    def process(self, context: SecureContext, response: str) -> None:
        """
        Process the response data based on task context.
        
        :param context: The SecureContext containing command parameters.
        :param response: Raw response string from the device.
        """
        pass

class CSVExporter(BasePostProcessor):
    """
    Processor to export command responses into CSV format.
    """
    
    def __init__(self, export_path: Path):
        self._export_path = export_path
        
    def process(self, context: SecureContext, response: str) -> None:
        """
        Exports response to CSV if 'export' param is set to 'csv'.
        
        :param context: Task context with parameters.
        :param response: Raw XML response.
        """
        export_val = context.params.get("export")
        if export_val != "csv":
            logger.debug("CSVExporter: Skipping processing, 'export' != 'csv'")
            return
            
        logger.info(f"CSVExporter: Processing export for task '{context.module_name}'")
        
        try:
            # Simple implementation: save response to a file in export directory
            file_name = f"{context.module_name}_export.csv"
            full_path = self._export_path / file_name
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(response)
                
            logger.info(f"CSVExporter: Successfully saved export to {full_path}")
            
        except Exception as e:
            logger.error(f"CSVExporter: Failed to write CSV file: {e}")
            raise
