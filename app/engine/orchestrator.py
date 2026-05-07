# File name: orchestrator.py
# path: app/engine/orchestrator.py
# Internal name: Orchestrator
# Version: v.0.5.2.0

import logging
from typing import Any, Dict, List, Optional

# Internal system component imports
from app.configuration.security import SecureContext
from app.engine.loader import ModuleManager
from app.engine.validator import XMLValidator
from app.engine.resolver import ArgumentResolver
from app.communication.session import HikvisionClient

# Logger configuration for the module
logger = logging.getLogger(__name__)

class Orchestrator:
    """
    System core orchestrator. 
    Coordinates data flow between loader, validator, resolver, and client.
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
        Initialize orchestrator via dependency injection.
        """
        logger.debug("Orchestrator initialization started (DEBUG)")
        self._loader = loader
        self._validator = validator
        self._resolver = resolver
        self._client = client
        self._base_context = base_context
        self._version = "0.5.2.0"
        logger.info(f"Orchestrator engine v{self._version} initialized successfully.")

    @classmethod
    def bootstrap(cls, base_context: SecureContext) -> "Orchestrator":
        """
        Composition Root. Assembles all subsystems into a functional Orchestrator.
        """
        logger.debug("Bootstrap: initializing subsystem instances")
        
        loader = ModuleManager()
        validator = XMLValidator()
        resolver = ArgumentResolver()
        client = HikvisionClient()
        
        return cls(
            loader=loader,
            validator=validator,
            resolver=resolver,
            client=client,
            base_context=base_context
        )

    def execute_headless(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        connect_str: Optional[str] = None
    ) -> bool:
        """
        High-level entry point for non-interactive command execution.
        """
        logger.info(f"Executing headless command for module: '{module_name}'")
        logger.debug(f"Parameters provided: {params}")

        context = self._prepare_context(module_name, params, connect_str)
        
        if not context:
            logger.error(f"Failed to prepare context for module '{module_name}'")
            return False

        return self.run_command(context)

    def _prepare_context(
        self, 
        module_name: str, 
        params: Dict[str, str], 
        connect_str: Optional[str]
    ) -> Optional[SecureContext]:
        """
        Internal wrapper for context creation.
        Delegates the complexity of parsing and merging to SecureContext factory.
        """
        logger.debug("Orchestrator delegating context creation to SecureContext factory")
        
        try:
            context = SecureContext.create_from_input(
                base=self._base_context,
                module_name=module_name,
                params=params,
                connect_str=connect_str
            )
            logger.debug("SecureContext successfully created via factory")
            return context
        except Exception as e:
            logger.error(f"Context factory error: {str(e)}")
            return None

    def run_command(self, context: SecureContext) -> bool:
        """
        Executes the full command cycle: Load -> Validate -> Resolve -> Send.
        Updated: Includes a memory-cache availability check before disk access.
        """
        logger.info(f"Running command lifecycle: {context.module_name}")
        
        # Step 0: Quick availability check using memory cache (cheap operation)
        if context.module_name not in self.get_available_modules():
            logger.error(f"Module '{context.module_name}' is not in the indexed library. Skipping execution.")
            return False

        # 1. Loading (Expensive disk read)
        logger.debug(f"Step 1: Loading module '{context.module_name}' content from disk")
        module_data = self._loader.get_module(context.module_name)
        if not module_data:
            logger.error(f"Module '{context.module_name}' content could not be read")
            return False

        # 2. Validation
        logger.debug("Step 2: Validating XML structure against schema")
        if not self._validator.validate(module_data):
             logger.error(f"Validation failed for module '{context.module_name}'")
             return False

        # 3. Resolution (Metadata + Body)
        logger.debug("Step 3: Resolving arguments and extracting ISAPI metadata")
        method, url, payload = self._resolver.resolve(module_data, context.params)
        
        # 4. Transmission
        logger.info(f"Step 4: Dispatching {method} request to {url}")
        response = self._client.send(
            method=method,
            url=url,
            payload=payload,
            context=context
        )
        
        if response is not None:
            logger.info(f"Command '{context.module_name}' executed successfully.")
            return True
            
        logger.error(f"Command '{context.module_name}' failed during transmission.")
        return False

    def get_available_modules(self) -> List[str]:
        """
        Returns a list of modules currently indexed in memory.
        Fast, non-blocking call for status checks and validation.
        """
        logger.debug("Retrieving available modules from memory cache")
        return self._loader.get_available_modules()

    def discover_modules(self) -> List[str]:
        """
        Performs a full scan of the module directory (expensive).
        Updates the index and cache.
        """
        logger.info("Performing full module discovery (disk scan)")
        return self._loader.discover_modules()

    def reload_modules(self) -> bool:
        """
        Triggers a fresh scan of the module directory.
        """
        logger.info("Forced module cache invalidation initiated")
        return self._loader.reload_modules()

    def get_status(self) -> Dict[str, Any]:
        """
        System diagnostics and versioning. 
        Uses cached data for performance metrics.
        """
        logger.debug("Gathering orchestrator status and metrics")
        
        # Using the fast cached method as requested by the architect
        available_modules = self.get_available_modules()
        
        return {
            "version": self._version,
            "engine": "hik-handler-core",
            "status": "operational",
            "metrics": {
                "modules_loaded": len(available_modules)
            }
        }