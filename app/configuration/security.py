# File: security.py
# Path: app/engine/security.py
# Context: Security Context
# Version: 1.0.0 Frozen

import logging
from dataclasses import dataclass, replace
from typing import Optional, Any, Dict

# Initialize module-level logger
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SecureContext:
    """
    Secure context for storing device credentials and network parameters.
    
    Uses frozen=True to ensure Immutability.
    Once initialized, no component can accidentally or intentionally 
    modify the host, user, password, or timeout.
    """
    host: str
    user: str
    password: str
    port: int = 80
    timeout: int = 10
    scheme: str = "http"
    
    # Extension for execution context (Orchestrator)
    module_name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """
        Post-initialization hook for logging instance creation.
        """
        logger.debug(f"SecureContext instance created for host: {self.host}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecureContext":
        """
        Factory method to assemble SecureContext from a dictionary.
        Centralizes parsing and validation logic.
        
        :param data: Input data (usually from CLI or config).
        :return: Initialized and frozen SecureContext.
        :raises ValueError: If mandatory parameters are missing.
        """
        logger.info("Assembling SecureContext from input data dictionary")
        
        # Mapping input keys to context fields
        context_data = {
            "host": data.get("host"),
            "user": data.get("user"),
            "password": data.get("password"),
            "port": int(data.get("port", 80)),
            "timeout": int(data.get("timeout", 10)),
            "scheme": data.get("scheme", "http"),
            "module_name": data.get("module"),
            "params": data.get("params", {})
        }
        
        # Mandatory fields validation
        if not all([context_data["host"], context_data["user"], context_data["password"]]):
            logger.error("Mandatory connection parameters missing in assembly dict")
            raise ValueError("Host, user, and password are required for SecureContext")
            
        return cls(**context_data)

    def with_task(self, module_name: str, params: Optional[Dict[str, Any]] = None) -> "SecureContext":
        """
        Clones existing context with a specific task attached.
        Maintains credentials while updating execution targets.
        
        :param module_name: Target ISAPI module name.
        :param params: Execution parameters.
        :return: New instance of SecureContext.
        """
        logger.debug(f"Branching context for task: {module_name}")
        return replace(self, module_name=module_name, params=params or {})

    def get_auth(self) -> tuple[str, str]:
        """
        Helper for retrieving credentials for network clients.
        
        :return: Tuple containing (username, password).
        """
        logger.debug(f"Accessing auth credentials for host: {self.host}")
        return (self.user, self.password)

    def __repr__(self) -> str:
        """
        Security-focused string representation.
        Protects the password from being leaked in logs or tracebacks.
        """
        pwd_mask = "***" if self.password else "None"
        return (f"SecureContext(host='{self.host}', user='{self.user}', "
                f"password='{pwd_mask}', port={self.port}, "
                f"module='{self.module_name}')")