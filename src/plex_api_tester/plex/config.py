# src/plex_api_tester/plex/config.py
"""
config.py for Plex API Module

This module sets up and manages configuration settings required for interacting with the Plex API.
"""

import re
import uuid
import xml.etree.ElementTree as ET
from platform import uname
from typing import Optional
from uuid import getnode

import requests


class PlexConfig:
    """
    Manages configuration settings for Plex API access, including server URLs, tokens, and headers.
    """

    SIGNIN_URL = "https://plex.tv/users/sign_in.json"
    TIMEOUT = 30

    X_PLEX_PROVIDES = "controller"
    X_PLEX_LANGUAGE = "en"

    def __init__(self) -> None:
        self._baseurl: Optional[str] = None
        self._token: Optional[str] = None
        self.X_PLEX_CLIENT_IDENTIFIER = str(uuid.uuid4())
        self.X_PLEX_IDENTIFIER = hex(getnode())
        self.X_PLEX_PLATFORM = None
        self.X_PLEX_PLATFORM_VERSION = None
        self.X_PLEX_PRODUCT = "PlexAPI"
        self.X_PLEX_VERSION = None
        self.X_PLEX_DEVICE = None
        self.X_PLEX_DEVICE_NAME = None

    def _fetch_pms_version(self) -> Optional[str]:
        """
        Fetch the Plex Media Server (PMS) version from the base URL.

        :return: Version as a string if found, or None if the request fails.
        :raises ValueError: If base URL is not set.
        """
        if not self._baseurl:
            raise ValueError("Base URL is not set. Please provide server IP and port.")

        url = f"{self._baseurl}/identity"
        print(f"Fetching PMS version from {url}...")
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            parsed_response = ET.fromstring(response.content)
            return parsed_response.get("version")
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch PMS version: {e}")
        except ET.ParseError:
            raise ValueError("Failed to parse the response for PMS version.")

    def _set_x_plex_headers(self) -> None:
        """
        Set the X-Plex headers based on system information and PMS version.

        :raises ValueError: If base URL is not set and PMS version cannot be fetched.
        """
        uname_info = uname()
        self.X_PLEX_PLATFORM = uname_info[0] or "Unknown Platform"
        self.X_PLEX_PLATFORM_VERSION = uname_info[3] or "Unknown Platform Version"
        self.X_PLEX_DEVICE = uname_info[0] or "Unknown Device"
        self.X_PLEX_DEVICE_NAME = uname_info[1] or "Unknown Device Name"

        if not self.X_PLEX_VERSION:
            try:
                self.X_PLEX_VERSION = self._fetch_pms_version()
            except ValueError:
                raise ValueError("Cannot set X-Plex headers without a valid base URL.")

    def get_x_plex_headers(self) -> dict:
        """
        Retrieve the configured X-Plex headers for authentication requests.

        :return: A dictionary of X-Plex headers.
        """
        self._set_x_plex_headers()
        return {
            "X-Plex-Provides": self.X_PLEX_PROVIDES,
            "X-Plex-Platform": self.X_PLEX_PLATFORM,
            "X-Plex-Platform-Version": self.X_PLEX_PLATFORM_VERSION,
            "X-Plex-Product": self.X_PLEX_PRODUCT,
            "X-Plex-Version": self.X_PLEX_VERSION,
            "X-Plex-Device": self.X_PLEX_DEVICE,
            "X-Plex-Device-Name": self.X_PLEX_DEVICE_NAME,
            "X-Plex-Identifier": self.X_PLEX_IDENTIFIER,
            "X-Plex-Client-Identifier": self.X_PLEX_CLIENT_IDENTIFIER,
            "X-Plex-Language": self.X_PLEX_LANGUAGE,
        }

    @property
    def baseurl(self) -> Optional[str]:
        """Get the base URL for the Plex server."""
        return self._baseurl

    def set_baseurl(self, server_ip: str, server_port: int) -> None:
        """
        Set the base URL for the Plex server.

        :param server_ip: IP address of the Plex server.
        :param server_port: Port number for the Plex server.
        :raises ValueError: If server_ip or server_port is empty.
        """
        if not server_ip or not server_port:
            raise ValueError("Server IP and port must be provided.")

        server_ip = re.sub(r"^https?://", "", server_ip)

        self._baseurl = f"http://{server_ip}:{server_port}"

    @property
    def token(self) -> Optional[str]:
        """Get the authentication token."""
        return self._token

    @token.setter
    def token(self, token: Optional[str]) -> None:
        """
        Set the authentication token.

        :param token: Plex authentication token.
        """
        self._token = token
