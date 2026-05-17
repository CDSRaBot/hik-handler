"""
File: resolver.py
Path: app/engine/resolver.py
Context Name: ArgumentResolver
Version: v.1.1.0 (Security Hardened)

Module for resolving (substituting) arguments and extracting ISAPI metadata from XML templates.
Uses string.Template for safe substitution and defusedxml.ElementTree for secure structural parsing.
Note: Switched to defusedxml to provide protection against XXE (XML External Entity) attacks.
"""
import logging
import defusedxml.ElementTree as ET
from string import Template
from typing import Any, Dict


# Initialize logger for the module
logger = logging.getLogger(f"hik_handler.{__name__}")


class ArgumentResolver:
    """
    Class for processing dynamic parameters and extracting command metadata.
    """

    def resolve(self, template: str, arguments: Dict[str, Any]) -> str:
        """
        Classic string substitution using ${key} syntax.

        Args:
            template: String with placeholders.
            arguments: Key-value pairs for substitution.

        Returns:
            Resolved string.
        """
        logger.debug("Resolving string template: %d chars", len(template))
        return Template(template).substitute(arguments)

    def resolve_command(self, xml_content: str, arguments: Dict[str, Any]) -> Dict[str, str]:
        """
        Extracts metadata (method, uri) from XML root attributes and resolves templates.
        
        Expected XML root format: <Command method="PUT" uri="/ISAPI/...">...</Command>

        Args:
            xml_content: The XML template string.
            arguments: Arguments for substitution.

        Returns:
            Dictionary containing 'method', 'url', and 'body'.
            
        Raises:
            ValueError: If metadata is missing or XML is malformed.
            KeyError: If required arguments are missing.
        """
        logger.debug("Starting command resolution and metadata extraction")
        
        try:
            # Parse XML to find metadata in attributes
            # Using defusedxml for secure parsing (XXE protection)
            root = ET.fromstring(xml_content)
            
            # Extract method and URI from root attributes
            raw_method = root.get('method', 'GET').upper()
            raw_uri = root.get('uri', '')
            
            if not raw_uri:
                logger.warning("No 'uri' attribute found in XML module")

            # Resolve templates for both URL and Body
            resolved_url = self.resolve(raw_uri, arguments)
            resolved_body = self.resolve(xml_content, arguments)
            
            logger.info("Command metadata resolved: %s %s", raw_method, resolved_url)
            
            return {
                "method": raw_method,
                "url": resolved_url,
                "body": resolved_body
            }

        except ET.ParseError as e:
            error_msg = f"Failed to parse XML module structure: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
            
        except KeyError as e:
            missing_key = e.args[0]
            error_msg = f"Resolver error: Missing argument '${missing_key}'"
            logger.error(error_msg)
            raise KeyError(error_msg) from e
            
        except Exception as e:
            logger.error(f"Unexpected error in resolve_command: {e}")
            raise