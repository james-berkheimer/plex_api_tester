import logging
import os
import time
import xml.etree.ElementTree as ET
from platform import uname
from pprint import pprint
from urllib.parse import urlencode

import requests

from . import utils
from .plex import config_instance
from .plex.api_client import PlexAPIClient
from .plex.exceptions import BadRequest

# from .plex.authentication import PlexAuthentication

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
    url = "https://plex.tv/api/v2/user"

    token = config_instance.token

    headers = {"X-Plex-Token": token}

    response = requests.request("GET", url, headers=headers)
    parsed_response = ET.fromstring(response.content)

    print(
        f"Username: {parsed_response.get('username')}\nEmail: {parsed_response.get('email')}\nID: {parsed_response.get('id')}"
    )


def test6():
    url = "https://plex.tv/api/v2/users/signin"

    password = os.getenv("PLEX_PASSWORD")
    email = os.getenv("PLEX_EMAIL")
    login = os.getenv("PLEX_USERNAME")

    payload = f"login={login}&password={password}&X-Plex-Client-Identifier=PlexAPITEst"
    # payload = f"login={email}&password={password}&X-Plex-Client-Identifier=PlexAPI"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request("POST", url, data=payload, headers=headers)
    # print(response.content)
    parsed_response = ET.fromstring(response.content)

    print(
        f"Token: {parsed_response.get('authToken')}\nUsername: {parsed_response.get('username')}\nEmail: {parsed_response.get('email')}\nUser ID: {parsed_response.get('id')}"
    )


def test7():
    url = "https://plex.tv/api/v2/pins"
    querystring = {
        "strong": "true",
        "X-Plex-Client-Identifier": "PlexAPI",
        "X-Plex-Product": "Playlist_Manager",
        "X-Plex-Device": "Linux",
        "X-Plex-Version": "1",
        "X-Plex-Platform": "Ubuntu",
    }

    response = requests.request("POST", url, params=querystring)
    parsed_response = ET.fromstring(response.content)

    print(f"Pin ID: {parsed_response.get("id")}")


def test8():
    print(os.path.expanduser("~/.config/plexapi/config.ini"))
