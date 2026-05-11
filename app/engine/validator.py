# validator.py
# path: hik-handler/data_plane/validator.py
# context: XML Validation Service
# version: 1.0.0 (Frozen)

import logging
import os
from lxml import etree
from defusedxml import lxml as safe_lxml

# Initialize module logger for tracking validation operations
logger = logging.getLogger(f"hik_handler.{__name__}")


class XMLValidator:
    """
    Service class for validating XML documents against an XSD schema.
    Provides caching of the compiled schema to improve performance 
    during mass processing of modules.
    """

    def __init__(self, xsd_path: str):
        """
        Initializes the validator instance and prepares the schema.
        
        :param xsd_path: Path to the XSD schema file.
        """
        self._xsd_path = xsd_path
        self._schema = None
        
        # Initial schema compilation
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """
        Internal method for loading and compiling the XSD schema.
        Executed once during instance creation to provide caching.
        """
        logger.debug(f"Validating XSD path: {self._xsd_path}")
        
        # Ensure the schema file actually exists
        if not os.path.exists(self._xsd_path):
            logger.error(f"XSD schema not found: {self._xsd_path}")
            self._schema = None
            return

        try:
            logger.debug(f"Compiling XSD schema from {self._xsd_path}")
            with open(self._xsd_path, 'rb') as f:
                schema_root = etree.XML(f.read())
                self._schema = etree.XMLSchema(schema_root)
            logger.info("XSD schema successfully compiled and cached in memory")
        except Exception as e:
            logger.error(f"Critical failure during schema initialization: {e}")
            self._schema = None

    def validate(self, xml_path: str) -> tuple[bool, str]:
        """
        Validates an XML file against the cached XSD schema.
        
        :param xml_path: Full path to the XML module to be checked.
        :return: Tuple (is_valid, error_message).
        """
        logger.info(f"Starting validation for: {xml_path}")
        
        # Check if service is ready
        if not self._schema:
            logger.error("Validation rejected: Schema not initialized")
            return False, "Validator state error: missing schema"

        try:
            # Safe XML parsing with XXE protection
            logger.debug("Executing safe XML parse")
            tree = safe_lxml.parse(xml_path)

            # Perform schema validation
            self._schema.assertValid(tree)
            
            logger.info(f"Validation successful for {xml_path}")
            return True, ""

        except (etree.XMLSyntaxError, etree.DocumentInvalid) as e:
            # Handle malformed XML or schema violations
            error_msg = f"XML/XSD mismatch in {xml_path}: {str(e)}"
            logger.debug(f"Validation details: {error_msg}")
            return False, error_msg

        except FileNotFoundError:
            # Handle missing XML file
            error_msg = f"Target XML file not found: {xml_path}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            # General system exceptions
            error_msg = f"Internal error during validation: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg