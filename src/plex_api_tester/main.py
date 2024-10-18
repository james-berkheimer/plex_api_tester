import logging
import time
from pprint import pprint

from . import utils
from .plex.server import get_server
from .plex_api_data import delete_playlist, get_playlist_ratingKey, get_playlists

plex_server = get_server()
logger = utils.create_logger(level=logging.INFO)


def main():
    title = "test_audio_playlist_3"

    start_time = time.time()
    playlist_key = get_playlist_ratingKey(title)
    print(f"Playlist ratingKey: {playlist_key}")
    delete_playlist(playlist_key)
    pprint(get_playlists())
    end_time = time.time()
    plex_api_duration = end_time - start_time

    print(f"Plex API call duration: {plex_api_duration:.4f} seconds")
