"""
File: orchestrator.py
Path: app/engine/orchestrator.py
Codename: Orchestrator
Version: v.1.0.0 (Frozen)

Description:
    Central coordination engine for the Hik-handler utility. 
    Manages the lifecycle of a command execution by orchestrating 
    loading, validation, resolution, and transmission.
"""

import logging
from typing import Any, Dict, List, Optional

# Internal system component imports
# Note: SecureContext.create_from_input is expected to be implemented in security.py
from app.configuration.security import SecureContext
from app.engine.loader import ModuleManager
from app.engine.validator import XMLValidator
from app.engine.resolver import ArgumentResolver
from app.communication.session import HikvisionClient

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
            client (HikvisionClient): Handles network communication with devices.
            base_context (SecureContext): Global/Default connection settings.
        """
        logger.debug("Orchestrator: constructor call (DEBUG)")
        self._loader = loader
        self._validator = validator
        self._resolver = resolver
        self._client = client
        self._base_context = base_context
        self._version = "1.0.0"
        logger.info(f"Orchestrator engine v{self._version} is now frozen and active.")

    @classmethod
    def bootstrap(cls, base_context: SecureContext) -> "Orchestrator":
        """
        Factory method (Composition Root) to assemble the orchestrator 
        with all necessary subsystems.
        """
        logger.debug("Orchestrator: bootstrapping subsystems")
        
        return cls(
            loader=ModuleManager(),
            validator=XMLValidator(),
            resolver=ArgumentResolver(),
            client=HikvisionClient(),
            base_context=base_context
        )

    def execute_headless(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        connect_str: Optional[str] = None
    ) -> bool:
        """
        Executes a specific module without an interactive shell.
        
        Args:
            module_name (str): Name of the XML module to run.
            params (dict): Key-value pairs for template resolution.
            connect_str (str, optional): Custom connection string 'user:pass@host'.
            
        Returns:
            bool: Success status of the command execution.
        """
        logger.info(f"Headless Execution: Starting for '{module_name}'")
        logger.debug(f"Input Parameters: {params}")

        # Delegation of context preparation
        context = self._prepare_context(module_name, params, connect_str)
        
        if not context:
            logger.error(f"Execution Aborted: Could not finalize context for '{module_name}'")
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
        Uses the factory contract in the security module.
        """
        logger.debug("Orchestrator: requesting SecureContext from factory (Data Plane)")
        
        try:
            # Assumes SecureContext.create_from_input handles defaults and parsing
            context = SecureContext.create_from_input(
                base=self._base_context,
                module_name=module_name,
                params=params,
                connect_str=connect_str
            )
            logger.debug("Orchestrator: context object successfully received")
            return context
        except Exception as e:
            logger.error(f"Context Factory failure: {str(e)}")
            return None

    def run_command(self, context: SecureContext) -> bool:
        """
        The main sequential pipeline for command execution.
        
        Flow: Index Check -> Load -> Validate -> Resolve -> Dispatch.
        """
        logger.info(f"Pipeline: Running lifecycle for module '{context.module_name}'")
        
        # Step 0: Warm Cache Validation
        # Check against indexed modules in memory to prevent invalid disk hits
        available = self.get_available_modules()
        if context.module_name not in available:
            logger.error(f"Lifecycle Error: Module '{context.module_name}' is not indexed.")
            return False

        # Step 1: Load Module (Disk I/O)
        logger.debug(f"Pipeline Step 1: Reading XML content for '{context.module_name}'")
        module_data = self._loader.get_module(context.module_name)
        if not module_data:
            logger.error(f"Lifecycle Error: Module data for '{context.module_name}' is empty.")
            return False

        # Step 2: XSD Validation
        logger.debug("Pipeline Step 2: Structural validation against schema")
        if not self._validator.validate(module_data):
             logger.error(f"Lifecycle Error: XML validation failed for '{context.module_name}'")
             return False

        # Step 3: Argument Resolution and Metadata Extraction
        # Returns: (http_method, path_url, rendered_body)
        logger.debug("Pipeline Step 3: Resolving placeholders and ISAPI metadata")
        method, url, payload = self._resolver.resolve(module_data, context.params)
        
        # Step 4: Network Dispatch
        logger.info(f"Pipeline Step 4: Sending {method} request to '{url}'")
        response = self._client.send(
            method=method,
            url=url,
            payload=payload,
            context=context
        )
        
        if response is not None:
            logger.info(f"Lifecycle Success: Command '{context.module_name}' finished.")
            return True
            
        logger.error(f"Lifecycle Failure: No response for '{context.module_name}'")
        return False

    def get_available_modules(self) -> List[str]:
        """
        Returns a list of modules currently indexed in the memory cache.
        Does not perform a disk scan.
        """
        logger.debug("Orchestrator: fetching indexed modules from cache")
        return self._loader.get_available_modules()

    def discover_modules(self) -> List[str]:
        """
        Performs a full scan of the modules directory and updates the index.
        """
        logger.info("Orchestrator: performing full disk discovery of modules")
        return self._loader.discover_modules()

    def reload_modules(self) -> bool:
        """
        Forced refresh of the module indexing system.
        """
        logger.info("Orchestrator: manual module reload triggered")
        return self._loader.reload_modules()

    def get_status(self) -> Dict[str, Any]:
        """
        Returns system metadata and health metrics.
        """
        logger.debug("Orchestrator: gathering system status report")
        
        return {
            "version": self._version,
            "engine": "hik-handler-core",
            "status": "frozen",
            "metrics": {
                "indexed_modules": len(self.get_available_modules())
            }
        }