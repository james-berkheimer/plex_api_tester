import logging
import time
import xml.etree.ElementTree as ET
from platform import uname
from pprint import pprint

import requests

from . import utils
from .plex.api_client import PlexAPIClient
from .plex.authentication import PlexAuthentication

logger = utils.create_logger(level=logging.INFO)

client = PlexAPIClient()


def test1():
    import plexapi

    start_time = time.time()
    print(plexapi.X_PLEX_VERSION)
    print(plexapi.X_PLEX_PLATFORM)
    print(plexapi.X_PLEX_DEVICE_NAME)
    print(plexapi.X_PLEX_PLATFORM_VERSION)
    print()
    end_time = time.time()
    plex = end_time - start_time

    start_time = time.time()
    url = "http://192.168.1.42:32400/identity"
    # url = "https://plex.tv/identity"
    response = requests.request("GET", url)
    parsed_response = ET.fromstring(response.content)
    print(parsed_response.get("version"))
    print(uname()[0])
    print(uname()[1])
    print(uname()[2])
    print()
    end_time = time.time()
    local = end_time - start_time

    print(f"Plex: {plex:.4f} seconds")
    print(f"Local: {local:.4f} seconds")


def test2():
    playlists = client.get_playlists()
    pprint(playlists)


def plex_api_call(title):
    rating_key = client.get_playlist_ratingKey(title)
    playlist_data = client.get_playlist_items(rating_key)
    return playlist_data


def test3():
    # base_url = os.getenv("PLEX_BASEURL")
    # api_key = os.getenv("PLEX_TOKEN")
    # headers = {"X-Plex-Token": api_key}
    # session = requests.Session()
    playlist_ratingKey = "367250"
    playlistItemIDs = ["44097"]
    client.remove_playlist_items(playlist_ratingKey, playlistItemIDs)

    # endpoint = f"/playlists/367250/items/{playlistItemID}"
    # item_key = f"{base_url}{endpoint}"
    # requests.delete(item_key, headers=headers)


def test4():
    print(uname())
    print(uname()[0])
    print(uname()[1])
    print(uname()[2])
    print(uname()[3])


def test5():
    pass


def test6():
    pass
