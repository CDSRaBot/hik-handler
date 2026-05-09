"""
File: app/network/session.py
Path: app/network/session.py
Code name: Network Session Manager
Version: v.1.0.1 Frozen

Network interaction module (Network Session).
Implements the ISAPI transport layer with Digest authentication support.
This version is frozen and serves as the reference implementation for the network layer.
"""

import logging
import requests
import urllib3
from typing import Optional
from requests.auth import HTTPDigestAuth
from app.configuration.security import SecureContext


logger = logging.getLogger(__name__)

# Suppress warnings about self-signed certificates for HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HikvisionNetworkError(Exception):
    """Base exception for Hik-handler network errors."""
    pass


class HikvisionClient:
    """
    Client for ISAPI (Network Session Manager).
    Implements the Context Manager pattern to manage session lifetime.
    """

    def __init__(self, context: SecureContext):
        """
        Initializes the client with a given secure context.
        
        Args:
            context: SecureContext with connection and authorization parameters.
        """
        logger.debug("Initializing HikvisionClient for host: %s", context.host)
        self._ctx = context
        self._session: Optional[requests.Session] = None
        self._base_url = f"{self._ctx.scheme}://{self._ctx.host}:{self._ctx.port}"
        logger.info("Client initialized for %s", self._base_url)

    def __enter__(self):
        """
        Opens a network session with Digest authentication.
        """
        logger.debug("Entering context: opening session.")
        self._session = requests.Session()
        self._session.auth = HTTPDigestAuth(self._ctx.user, self._ctx.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the network session.
        """
        logger.debug("Exiting context: closing session.")
        if self._session:
            self._session.close()
            self._session = None

    def execute(self, method: str, url_path: str, payload: Optional[str] = None, headers: Optional[dict] = None) -> str:
        """
        Executes an HTTP request to the device.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            url_path: API endpoint path (e.g., /ISAPI/System/deviceInfo).
            payload: XML data as a string to send in the request body.
            headers: Optional dictionary of HTTP headers.

        Returns:
            str: The response body as text.

        Raises:
            HikvisionNetworkError: In case of connection issues or protocol errors.
        """
        logger.debug("Preparing to execute method: %s. Path: %s", method, url_path)
        
        if not self._session:
            logger.error("Attempted to execute request without initializing a session.")
            raise HikvisionNetworkError("Session not initialized. Use 'with' statement.")

        full_url = f"{self._base_url}{url_path}"
        
        # Apply passed headers or use default XML content-type
        request_headers = headers if headers else {'Content-Type': 'application/xml'}
        
        logger.info("Sending %s request to device...", method)
        logger.debug("Request details: URL=%s, Headers=%s", full_url, request_headers)
        
        try:
            # Note: payload must be a string or None at this stage
            response = self._session.request(
                method=method,
                url=full_url,
                data=payload.encode('utf-8') if payload else None,
                timeout=self._ctx.timeout,
                headers=request_headers,
                verify=False  # Disable SSL verification for local cameras
            )
            
            # Check for HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            logger.debug("Request executed successfully. Status: %s", response.status_code)
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error("Error during request execution: %s", str(e))
            raise HikvisionNetworkError(f"Network request failed: {e}")