"""
File: orchestrator.py
Path: app/engine/orchestrator.py
Codename: Orchestrator
Version: v.1.0.4 (Contract Synced)

Description:
    Central coordination engine for the Hik-handler utility. 
    Manages the lifecycle of a command execution by orchestrating 
    loading, validation, resolution, and transmission.
    Synchronized with HikvisionClient v.1.0.2.
"""

import logging
from typing import Any, Dict, List, Optional

# Internal system component imports
from app.configuration.settings import ConfigManager
from app.configuration.security import SecureContext
from app.engine.loader import ModuleManager
from app.engine.validator import XMLValidator
from app.engine.resolver import ArgumentResolver
from app.communication.session import HikvisionClient, HikvisionNetworkError
from app.engine.post_processors import BasePostProcessor, CSVExporter

# Logger configuration for the module
logger = logging.getLogger(f"hik_handler.{__name__}")

class Orchestrator:
    """
    Main Orchestrator class.
    Implements the mediator pattern to decouple system components.
    """
    
    def __init__(
        self, 
        loader: ModuleManager, 
        validator: XMLValidator,
        resolver: ArgumentResolver,
        client: HikvisionClient,
        base_context: Optional[SecureContext] = None,
        processors: List[BasePostProcessor] = None
    ):
        """
        Initialize the orchestrator with its dependencies.
        
        Args:
            loader (ModuleManager): Handles XML module file operations.
            validator (XMLValidator): Validates XML against XSD schemas.
            resolver (ArgumentResolver): Injects params and extracts ISAPI metadata.
            client (HikvisionClient): Default network client.
            base_context (SecureContext, optional): Global/Default connection settings.
            processors (List[BasePostProcessor]): Optional list of post-processors.
        """
        self._loader = loader
        self._validator = validator
        self._resolver = resolver
        self._client = client
        self._base_context = base_context
        self._processors = processors or []
        self._version = "1.1.0"
        
        logger.debug(f"Orchestrator constructor: instance created (v{self._version})")

    def set_context(self, context: SecureContext) -> None:
        """
        Dynamically sets the active connection context for the session.
        """
        logger.info(f"Orchestrator: Setting active context for host: {context.host}")
        self._base_context = context

    def disconnect(self) -> None:
        """
        Clears the current session context.
        """
        logger.info("Orchestrator: Clearing active session context.")
        self._base_context = None

    def check_connection(self) -> bool:
        """
        Performs a lightweight connectivity check.
        Returns True if the camera responds, False otherwise.
        """
        if not self._base_context:
            logger.warning("Orchestrator: Cannot check connection, no context active.")
            return False
            
        logger.info(f"Orchestrator: Checking connectivity to {self._base_context.host}...")
        try:
            # Lightweight request to check connectivity
            with HikvisionClient(self._base_context) as conn:
                conn.execute(method="GET", url_path="/ISAPI/System/deviceInfo")
            return True
        except Exception as e:
            logger.error(f"Orchestrator: Connection verification failed: {e}")
            return False

    @classmethod
    def bootstrap(cls, config: ConfigManager) -> "Orchestrator":
        """
        Factory method to assemble the Orchestrator and its dependencies.
        
        Args:
            config (ConfigManager): Fully initialized configuration object.
            
        Returns:
            Orchestrator: A ready-to-use orchestrator instance.
        """
        logger.info("Bootstrap: Assembling Orchestrator dependencies...")
        
        # 1. Извлекаем контекст безопасности из конфигуратора
        base_context = config.get_secure_context()
        
        # 2. Инициализируем Data Plane (с путями из конфигуратора)
        loader = ModuleManager(base_dir=str(config.modules_path))
        validator = XMLValidator(xsd_path=str(config.schema_path))
        resolver = ArgumentResolver()
        
        # 3. Инициализируем пост-процессоры
        processors = [CSVExporter(config.export_path)]
        
        # 4. Инициализируем Network Plane
        client = HikvisionClient(context=base_context)
        
        logger.info("Bootstrap: All subsystems initialized. Returning Orchestrator instance.")
        
        # 5. Собираем сам Оркестратор
        return cls(
            loader=loader,
            validator=validator,
            resolver=resolver,
            client=client,
            base_context=base_context,
            processors=processors
        )

    def execute_headless(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        connect_str: Optional[str] = None
    ) -> bool:
        """
        Main execution point for Terminal or Scripting modes (Headless).
        
        Args:
            module_name (str): Name of the XML module to run.
            params (dict): Key-value pairs for template resolution.
            connect_str (str, optional): Custom connection string 'user:pass@host'.
            
        Returns:
            bool: Success status of the command execution.
        """
        logger.info(f"Execution: Starting task '{module_name}' via common entry point.")
        
        # TRANSFORMATION POINT: 
        # We create a specific task context derived from base + arguments
        context = self._prepare_context(module_name, params, connect_str)
        
        if not context:
            logger.error(f"Execution Aborted: Fails to generate SecureContext for '{module_name}'")
            return False

        return self.run_command(context)

    def _prepare_context(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        connect_str: Optional[str] = None
    ) -> Optional[SecureContext]:
        """
        Private helper to generate a command-specific SecureContext.
        This is where 'params' and 'overrides' are merged with 'base_context'.
        """
        logger.debug(f"Context: Merging task parameters for module '{module_name}'")
        
        try:
            # Using existing with_task method to clone context with task details
            return self._base_context.with_task(module_name=module_name, params=params)
        except Exception as e:
            logger.error(f"Context: Generation failure - {str(e)}")
            return None

    def run_command(self, context: SecureContext) -> bool:
        """
        The main sequential pipeline for command execution.
        
        Steps:
            0. Validation against indexed modules.
            1. Loading module XML from storage.
            2. Structural validation against XSD.
            3. Metadata extraction and placeholder resolution.
            4. Network transmission via ISAPI client.
        """
        logger.info(f"Pipeline: Running lifecycle for '{context.module_name}'")
        
        # Step 0: Warm Cache Validation
        available = self.get_available_modules()
        if context.module_name not in available:
            logger.error(f"Pipeline Error: Module '{context.module_name}' is not found in index.")
            return False

        # Step 1: Load Module
        logger.debug(f"Step 1: Fetching module content for '{context.module_name}'")
        try:
            # Get path for validator and content for resolver
            module_path = self._loader.get_module_path(context.module_name)
            module_data = self._loader.read_module(context.module_name)
        except Exception as e:
            logger.error(f"Pipeline Error: Failed to load module '{context.module_name}' - {e}")
            return False

        # Step 2: XSD Validation (Step 0 Security check)
        logger.debug("Step 2: Performing XML structural validation against XSD.")
        is_valid, error_msg = self._validator.validate(module_path)
        if not is_valid:
            logger.error(f"Pipeline Error: XML validation failed for '{context.module_name}': {error_msg}")
            return False

        # Step 3: Argument Resolution
        logger.debug("Step 3: Resolving placeholders and extracting ISAPI metadata.")
        # Use resolve_command to get method, url, and payload from the parsed XML module
        metadata = self._resolver.resolve_command(module_data, context.params)
        method = metadata["method"]
        url = metadata["url"]
        payload = metadata["body"]
        
        # Step 4: Network Dispatch
        logger.info(f"Network: Dispatching {method} request to '{url}'")
        
        try:
            # Instantiate a transient client for the task-specific context.
            # Context manager (with) is mandatory for HikvisionClient v.1.0.2.
            task_client = HikvisionClient(context)
            with task_client as conn:
                response: str = conn.execute(
                    method=method,
                    url_path=url,
                    payload=payload
                )
            
            # Since client v.1.0.2 returns text and checks Content-Type:
            if response:
                logger.info(f"Result: Task '{context.module_name}' completed successfully.")
                logger.debug(f"Response (length: {len(response)}): {response}")
                
                # Step 5: Post-processing pipeline (Export/Logger/etc.)
                for processor in self._processors:
                    try:
                        processor.process(context, response)
                    except Exception as e:
                        logger.error(f"Post-processor '{processor.__class__.__name__}' failed: {e}")
                
                return True
                
        except HikvisionNetworkError as ne:
            logger.error(f"Network Error: ISAPI request failed - {str(ne)}")
        except Exception as e:
            logger.error(f"Pipeline Error: Unexpected error during dispatch - {str(e)}")
            
        logger.error(f"Result: Lifecycle failure for '{context.module_name}'.")
        return False

    def get_available_modules(self) -> List[str]:
        """Returns indexed modules from memory."""
        logger.debug("Orchestrator: Fetching available modules from cache.")
        return self._loader.get_available_modules()

    def discover_modules(self) -> List[str]:
        """Performs disk scan and updates index."""
        logger.info("Discovery: Initiating full modules scan on disk.")
        return self._loader.discover_modules()

    def reload_modules(self) -> bool:
        """Forced refresh of the indexing system."""
        logger.info("System: Manual module index reload triggered.")
        return self._loader.reload_modules()

    def get_status(self) -> Dict[str, Any]:
        """Returns health metrics."""
        logger.debug("System: Gathering status report.")
        return {
            "version": self._version,
            "engine": "hik-handler-core",
            "metrics": {
                "indexed_modules": len(self.get_available_modules())
            }
        }