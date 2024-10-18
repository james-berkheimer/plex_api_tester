import os


class PlexConfig:
    CRED_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests/.plex_cred/credentials.json"
    )
