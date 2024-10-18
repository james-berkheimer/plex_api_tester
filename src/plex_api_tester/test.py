import logging
import time
from pprint import pprint

from plex_api_client import PlexAPI

from . import utils
from .plex.server import get_server
from .plex_api_data import get_playlist_items, get_playlist_ratingKey
from .plex_python_api_data import get_playlist_data

plex_server = get_server()
logger = utils.create_logger(level=logging.INFO)


def test1():
    s = PlexAPI(
        access_token="<YOUR_API_KEY_HERE>",
        client_id="3381b62b-9ab7-4e37-827b-203e9809eb58",
        client_name="Plex for Roku",
        client_version="2.4.1",
        platform="Roku",
        device_nickname="Roku 3",
    )

    res = s.playlists.get_playlists()
    print(res)


def test2():
    # title = "test_audio_playlist_1"
    title = "Car songs"
    # Timing the Plex API call
    start_time = time.time()
    _plex_api_data = plex_api_call(title)
    end_time = time.time()
    plex_api_duration = end_time - start_time
    # pprint(_plex_api_data)

    # Timing the Plex Python API call
    start_time = time.time()
    _plex_python_api_call_data = plex_python_api_call(title)
    end_time = time.time()
    plex_python_api_duration = end_time - start_time
    # pprint(plex_python_api_call_data)

    print(f"Plex API call duration: {plex_api_duration:.4f} seconds")
    print(f"Plex Python API call duration: {plex_python_api_duration:.4f} seconds")


def plex_api_call(title):
    rating_key = get_playlist_ratingKey(title)
    playlist_data = get_playlist_items(rating_key)
    return playlist_data


def plex_python_api_call(title):
    playlist_data = get_playlist_data(title)
    return playlist_data
