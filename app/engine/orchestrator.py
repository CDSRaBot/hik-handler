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
from app.configuration.security import SecureContext
from app.engine.loader import ModuleManager
from app.engine.validator import XMLValidator
from app.engine.resolver import ArgumentResolver
from app.communication.session import HikvisionClient, HikvisionNetworkError

# Logger configuration for the module
logger = logging.getLogger(__name__)

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
        base_context: SecureContext
    ):
        """
        Initialize the orchestrator with its dependencies.
        
        Args:
            loader (ModuleManager): Handles XML module file operations.
            validator (XMLValidator): Validates XML against XSD schemas.
            resolver (ArgumentResolver): Injects params and extracts ISAPI metadata.
            client (HikvisionClient): Default network client.
            base_context (SecureContext): Global/Default connection settings.
        """
        self._loader = loader
        self._validator = validator
        self._resolver = resolver
        self._client = client
        self._base_context = base_context
        self._version = "1.0.4"
        
        logger.debug(f"Orchestrator constructor: instance created (v{self._version})")

    @classmethod
    def bootstrap(cls, base_context: SecureContext) -> "Orchestrator":
        """
        Factory method (Composition Root) to assemble the orchestrator 
        with all necessary subsystems.
        """
        logger.debug("Orchestrator: bootstrapping subsystems (loader, validator, resolver, client)")
        
        return cls(
            loader=ModuleManager(),
            validator=XMLValidator(),
            resolver=ArgumentResolver(),
            # Initialized with base context for default state
            client=HikvisionClient(base_context),
            base_context=base_context
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
        connect_str: Optional[str]
    ) -> Optional[SecureContext]:
        """
        Private helper to generate a command-specific SecureContext.
        This is where 'params' and 'overrides' are merged with 'base_context'.
        """
        logger.debug(f"Context: Merging task parameters for module '{module_name}'")
        
        try:
            # SecureContext.create_from_input handles the actual merging logic
            context = SecureContext.create_from_input(
                base=self._base_context,
                module_name=module_name,
                params=params,
                connect_str=connect_str
            )
            logger.debug(f"Context: SecureContext for '{module_name}' successfully prepared.")
            return context
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
        module_data = self._loader.get_module(context.module_name)
        if not module_data:
            logger.error(f"Pipeline Error: Data for module '{context.module_name}' is empty.")
            return False

        # Step 2: XSD Validation (Step 0 Security check)
        logger.debug("Step 2: Performing XML structural validation against XSD.")
        if not self._validator.validate(module_data):
             logger.error(f"Pipeline Error: XML validation failed for '{context.module_name}'.")
             return False

        # Step 3: Argument Resolution
        logger.debug("Step 3: Resolving placeholders and extracting ISAPI metadata.")
        method, url, payload = self._resolver.resolve(module_data, context.params)
        
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