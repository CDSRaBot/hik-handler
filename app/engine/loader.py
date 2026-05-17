# File: loader.py
# Path: app/engine/loader.py
# Code Name: ModuleManager
# Version: 0.4.0

import logging
import json
from pathlib import Path
from typing import List, Set, Dict, Any

# Logger configuration for the loader module
logger = logging.getLogger(f"hik_handler.{__name__}")

class ModuleManager:
    """
    Responsible for discovering, indexing, caching, and verifying the existence 
    of XML modules in the file system, as well as managing the modules.inf index.
    """

    def __init__(self, base_dir: str = "modules", index_file: str = "modules.inf"):
        """
        Initialize the module manager.
        :param base_dir: Path to the directory with XML modules.
        :param index_file: Metadata index file name.
        """
        self._base_dir = Path(base_dir).resolve()
        self._index_path = self._base_dir / index_file
        self._failed_modules: Set[str] = set()
        self._cached_modules: List[str] = []
        
        logger.debug(f"Initializing ModuleManager with base_dir: {self._base_dir}")
        
        # Create directory if it does not exist (Architectural directive)
        if not self._base_dir.exists():
            logger.info(f"Modules directory not found. Creating: {self._base_dir}")
            self._base_dir.mkdir(parents=True)
            
        # Attempt to load cache from index on startup
        self._load_index()

    def _load_index(self) -> None:
        """Loads the list of modules from the index file into memory."""
        if self._index_path.exists():
            try:
                with open(self._index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cached_modules = data.get("modules", [])
                logger.debug(f"Index loaded. Modules in cache: {len(self._cached_modules)}")
            except Exception as e:
                logger.warning(f"Failed to read index {self._index_path}: {e}")
                self._cached_modules = []

    def _save_index(self, modules_list: List[str]) -> None:
        """Saves the list of modules to the index file."""
        try:
            with open(self._index_path, 'w', encoding='utf-8') as f:
                json.dump({"modules": modules_list}, f, ensure_ascii=False, indent=4)
            logger.debug(f"Index successfully updated: {self._index_path}")
        except Exception as e:
            logger.error(f"Error writing index {self._index_path}: {e}")

    def get_module_path(self, module_name: str) -> Path:
        """
        Returns a secure path to the module file.
        Checks file existence and protects against Path Traversal.
        """
        logger.debug(f"Requesting path for module: {module_name}")
        
        # Form the target path
        module_file = (self._base_dir / f"{module_name}.xml").resolve()
        
        # Security check: the file must be inside the base directory
        if self._base_dir not in module_file.parents:
            logger.error(f"Attempted access outside allowed directory: {module_name}")
            raise PermissionError("Access to the file is denied by security settings")

        if not module_file.exists():
            logger.warning(f"Module file {module_name} not found on disk")
            raise FileNotFoundError(f"Module '{module_name}' does not exist")

        return module_file

    def read_module(self, module_name: str) -> str:
        """
        Reads the content of the XML module file.
        :param module_name: The name of the module (e.g., '01_minimal_plugin').
        :return: String containing XML content.
        :raises FileNotFoundError: If the module file does not exist.
        """
        module_path = self.get_module_path(module_name)
        if not module_path.exists():
            logger.error(f"Module file not found for reading: {module_path}")
            raise FileNotFoundError(f"Module {module_name} not found at {module_path}")

        logger.debug(f"Reading module content from: {module_path}")
        return module_path.read_text(encoding='utf-8')


    def discover_modules(self) -> List[str]:
        """
        Scans the directory, updates the in-memory cache and the modules.inf file.
        Returns a list of discovered XML file names.
        """
        logger.debug("Starting module directory scan")
        valid_modules = []
        
        try:
            for file in self._base_dir.glob("*.xml"):
                logger.debug(f"File discovered: {file.name}")
                valid_modules.append(file.stem)
            
            # Update cache and save index
            self._cached_modules = sorted(valid_modules)
            self._save_index(self._cached_modules)
            
            logger.info(f"Scan completed. Modules found: {len(self._cached_modules)}")
            return self._cached_modules
            
        except Exception as e:
            logger.error(f"Error scanning directory {self._base_dir}: {e}")
            return self._cached_modules # Return old cache on error

    def reload_modules(self) -> bool:
        """
        Interface method to forcefully update the module list.
        Synchronized with Orchestrator requirements.
        
        Returns:
            bool: True if modules were found, False if the list is empty.
        """
        logger.debug("Manual module index reload requested.")
        modules = self.discover_modules()
        
        if not modules:
            logger.info("Module list is empty.")
            return False
            
        return True
        
    def get_available_modules(self) -> List[str]:
        """Returns the list of modules from memory cache without disk access."""
        logger.debug("Requesting available modules from cache.")
        if not self._cached_modules:
            logger.debug("Cache empty, triggering discovery.")
            return self.discover_modules()
        return self._cached_modules

    def get_failed_modules(self) -> Set[str]:
        """Returns a set of modules that failed verification during loading."""
        logger.debug(f"Returning {len(self._failed_modules)} failed modules.")
        return self._failed_modules