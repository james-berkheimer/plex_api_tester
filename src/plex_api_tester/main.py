import logging
from pprint import pprint

from . import utils
from .plex_data import get_playlist_items, get_playlist_key

logger = utils.create_logger(level=logging.INFO)

URL = "http://192.168.1.42:32400"


def main():
    title = "test_video_playlist_1"
    key, playlist_type = get_playlist_key(title)
    playlist_data = get_playlist_items(key, playlist_type)
    pprint(playlist_data)
