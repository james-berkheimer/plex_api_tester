import json
import logging
from pprint import pprint

# from .config import PlexConfig
from .plex import PlexAuthentication
from .plex import config_instance as plex_config

logger = logging.getLogger("app_logger")

credential_path = "/home/james/code/plex_api_tester/tests/.plex_cred/credentials.json"


try:
    with open(credential_path, "r") as f:
        data = json.load(f)
        plex_credentials = data.get("plex", {})
        username = plex_credentials.get("username", "")
        password = plex_credentials.get("password", "")
        server_ip = plex_credentials.get("server_ip", "")
        server_port = plex_credentials.get("server_port", "")
        plex_config.set_baseurl(server_ip, server_port)

        plex_headers = plex_config.get_x_plex_headers()
        plex_auth = PlexAuthentication(config_instance=plex_config)
        plex_auth.verify_authentication(username=username, password=password)
        logger.debug("Loaded Plex credentials")

except FileNotFoundError as e:
    raise RuntimeError("Failed to load Plex credentials") from e
