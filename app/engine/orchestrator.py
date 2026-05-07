# File name: orchestrator.py
# path: app/engine/orchestrator.py
# Internal name: Orchestrator
# Version: v.0.3.9.0

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
    System core. Coordinates work across all layers: 
    loading, validation, and command execution.
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
        
        -- loader: Component for searching and loading modules.
        -- validator: Component for XSD validation of XML commands.
        -- resolver: Component for processing command arguments.
        -- client: Network client for hardware communication.
        -- base_context: Base security context from configuration.
        """
        logger.debug("Orchestrator initialization: start")
        self._loader = loader
        self._validator = validator
        self._resolver = resolver
        self._client = client
        self._base_context = base_context
        self._version = "0.3.9.0"
        logger.info("Orchestrator successfully initialized.")

    @classmethod
    def bootstrap(cls, base_context: SecureContext) -> "Orchestrator":
        """
        Factory method for dependency assembly (Composition Root).
        Initializes all subsystems and returns a ready-to-use Orchestrator.
        """
        logger.debug("Bootstrap factory method called: assembling components")
        
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
        Executes a command in automatic mode (without interactive terminal).
        """
        logger.info(f"Headless: request for module '{module_name}'")
        logger.debug(f"Headless parameters: {params}")

        if connect_str:
            logger.debug("Parsing custom credentials via string methods")
            credentials, separator, host = connect_str.rpartition('@')
            user, colon, password = credentials.partition(':')
            
            if not (separator and colon and host and user and password):
                logger.error("Invalid --connect format. Expected user:password@host")
                return False
        else:
            host = self._base_context.host
            user = self._base_context.user
            password = self._base_context.password

        context = SecureContext(
            host=host,
            user=user,
            password=password,
            timeout=self._base_context.timeout,
            module_name=module_name,
            params=params
        )

        return self.run_command(context)

    def run_command(self, context: SecureContext) -> bool:
        """
        Main method for command execution. Updated to support new Resolver contract.
        """
        logger.debug(f"Executing command: {context.module_name}")
        
        # Load the module by name
        module_data = self._loader.get_module(context.module_name)
        if not module_data:
            logger.error(f"Module {context.module_name} not found")
            return False

        # Validate module structure against XSD
        if not self._validator.validate(module_data):
             logger.error(f"Module {context.module_name} failed validation")
             return False

        # Resolve command metadata and prepare final payload
        # Expected return: (http_method, isapi_url, xml_body)
        method, url, payload = self._resolver.resolve(module_data, context.params)
        
        # Dispatch request with explicit HTTP method and URL
        response = self._client.send(
            method=method,
            url=url,
            payload=payload,
            context=context
        )
        
        return response is not None

    def discover_modules(self) -> List[str]:
        """
        Scans directory for new XML modules.
        """
        logger.info("Searching for new modules in the system...")
        modules = self._loader.discover_modules()
        logger.debug(f"Modules found: {len(modules)}")
        return modules

    def reload_modules(self) -> bool:
        """
        Forced reload of the module list.
        """
        logger.info("Module reload initiated...")
        result = self._loader.reload_modules()
        if result:
            logger.info("Modules successfully reloaded.")
        return result

    def get_status(self) -> Dict[str, str]:
        """
        Returns current version and system readiness state.
        """
        logger.debug("System status request")
        return {
            "version": self._version,
            "status": "ready"
        }