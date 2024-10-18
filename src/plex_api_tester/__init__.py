import json
import logging
import os

from .config import PlexConfig

logger = logging.getLogger("app_logger")

try:
    with open(PlexConfig.CRED_PATH, "r") as f:
        data = json.load(f)
        plex_data = data.get("plex", {})
        os.environ["PLEX_BASEURL"] = plex_data.get("baseurl", "")
        os.environ["PLEX_TOKEN"] = plex_data.get("token", "")
        logger.debug("Loaded Plex credentials")

except FileNotFoundError as e:
    raise RuntimeError("Failed to load Plex credentials") from e
