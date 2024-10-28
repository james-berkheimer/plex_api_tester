import logging
import time
from pprint import pprint

from . import utils
from .plex.api_client import PlexAPIClient

logger = utils.create_logger(level=logging.INFO)

client = PlexAPIClient()


def main():
    title1 = "test_audio_playlist_2"
    title2 = "test_video_playlist_1"
    # title3 = "Charity"
    # title4 = "Car songs"

    run1 = call_api(title1)
    run2 = call_api(title2)

    print(run1)
    print(run2)


def call_api(title):
    start_time = time.time()
    playlist_key = client.get_playlist_ratingKey(title)
    print(f"Playlist ratingKey: {playlist_key}")
    playlist_data = client.get_playlist_items(playlist_key)
    sorted_data = client.parse_playlist_data(playlist_data)
    pprint(sorted_data)

    end_time = time.time()
    plex_api_duration = end_time - start_time

    return f"Plex API call duration: {plex_api_duration:.4f} seconds"
