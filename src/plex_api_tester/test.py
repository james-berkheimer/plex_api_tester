import logging
import time
import xml.etree.ElementTree as ET
from platform import uname
from pprint import pprint

import requests

from . import utils

# from .plex_api_client import (
#     get_playlist_items,
#     get_playlist_ratingKey,
#     get_playlists,
#     remove_playlist_items,
# )
from .plex.api_client import (
    get_playlist_items,
    get_playlist_ratingKey,
    get_playlists,
    remove_playlist_items,
)
from .plex.authentication import PlexAuthentication

logger = utils.create_logger(level=logging.INFO)


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
    playlists = get_playlists()
    pprint(playlists)


def plex_api_call(title):
    rating_key = get_playlist_ratingKey(title)
    playlist_data = get_playlist_items(rating_key)
    return playlist_data


def test3():
    # base_url = os.getenv("PLEX_BASEURL")
    # api_key = os.getenv("PLEX_TOKEN")
    # headers = {"X-Plex-Token": api_key}
    # session = requests.Session()
    playlist_ratingKey = "367250"
    playlistItemIDs = ["44097"]
    remove_playlist_items(playlist_ratingKey, playlistItemIDs)

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
    # url = "https://plex.tv/api/v2/users/signin"
    # headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # # response = requests.request("POST", url, headers=headers)
    # # print(response.text)

    # payload = {"login": "berkyjay@gmail.com", "password": "()jayBERKY1plex2[]", "rememberMe": False}

    # response = requests.post(url, headers=headers, data=payload)
    # print(response.text)

    login = "james.berkheimer@gmail.com"
    # login = "berkyjay@gmail.com"
    # login = "berkyjay"
    # login = "Berkyjay"
    password = "()jayBERKY1plex2[]"

    result = get_user_sign_in_data(login, password, remember_me=False)
    print(result)


def get_user_sign_in_data(username, password, remember_me=False):
    url = "https://plex.tv/users/sign_in"
    # url = "https://plex.tv/sign_in"
    # headers = {"Content-Type": "application/x-www-form-urlencoded"}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    }
    data = {
        "login": username,
        "password": password,
        "rememberMe": str(remember_me).lower(),  # 'true' or 'false'
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 201:
        return response.json()  # Returns user data including the authentication token
    else:
        return f"Error: {response.status_code} - {response.text}"


# Example usage:
# result = get_user_sign_in_data('<your_username>', '<your_password>', remember_me=True)
# print(result)


def test6():
    login = "james.berkheimer@gmail.com"
    password = "()jayBERKY1plex2[]"

    start_time = time.time()
    token = get_plex_auth_token(login, password)
    print(f"Authentication Token: {token}")
    end_time = time.time()
    plex_api_auth = end_time - start_time

    start_time = time.time()
    token = authenticate_plex(login, password)
    print(f"Authentication Token: {token}")
    end_time = time.time()
    internal_duration = end_time - start_time

    start_time = time.time()
    plex_auth = PlexAuthentication()
    plex_auth.ensure_authenticated(username=login, password=password)
    print(f"Authenticated with url: {plex_auth.baseurl}")
    print(f"Authenticated with token: {plex_auth.token}")
    end_time = time.time()
    authentucation_duration = end_time - start_time

    print(f"Plex API call duration: {plex_api_auth:.4f} seconds")
    print(f"Internal call duration: {internal_duration:.4f} seconds")
    print(f"Authentication call duration: {authentucation_duration:.4f} seconds")


def get_plex_auth_token(username, password):
    from plexapi.myplex import MyPlexAccount

    try:
        # Login to MyPlex account
        account = MyPlexAccount(username, password)

        # Retrieve authentication token
        auth_token = account.authenticationToken
        return auth_token
    except Exception as e:
        return f"Error: {str(e)}"


def authenticate_plex(username, password):
    import uuid

    url = "https://plex.tv/users/sign_in.json"
    headers1 = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "PlexClient/1.0"}
    headers2 = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    }

    # Generate a unique client identifier (UUID)
    client_identifier = str(uuid.uuid4())

    headers3 = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Plex-Client-Identifier": client_identifier,  # Unique client ID
        "X-Plex-Product": "MyPlexApp",  # Name of your app
        "X-Plex-Version": "1.0",  # Version of your app
        "X-Plex-Device": "PC",  # Device type
        "X-Plex-Platform": "Windows",  # Operating system/platform
        "X-Plex-Platform-Version": "10.0",  # OS version
        "X-Plex-Device-Name": "MyPC",  # Friendly device name
        "User-Agent": "Plex Client",  # User-Agent header
    }
    data = {"user[login]": username, "user[password]": password}

    # Sending the POST request to Plex to authenticate
    response = requests.post(url, headers=headers3, data=data)

    # Check for successful authentication (201 status code)
    if response.status_code == 201:
        user_data = response.json()
        auth_token = user_data["user"]["authToken"]  # Extracting the authentication token
        return auth_token
    else:
        return f"Error: {response.status_code} - {response.text}"
