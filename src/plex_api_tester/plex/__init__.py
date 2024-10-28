# src/plex_api_tester/plex/__init__.py

"""
__init__.py for Plex API Module

This file initializes configuration and authentication modules for the Plex API.
"""

from .authentication import PlexAuthentication
from .config import PlexConfig

# Singleton instance for Plex configuration, accessible across modules.
config_instance = PlexConfig()

__all__ = ["PlexAuthentication", "config_instance"]
