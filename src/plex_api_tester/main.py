import logging
import os
import xml.etree.ElementTree as ET
from xml.etree import ElementTree

import requests

from . import utils

logger = utils.create_logger(level=logging.INFO)


def main():
    get_playlist_data()


def get_playlist_data():
    url = "http://192.168.1.42:32400"
    playlists_url = url + "/playlists"

    api_key = os.getenv("PLEX_TOKEN")

    headers = {"X-Plex-Token": api_key}

    # playlist_response = requests.request("GET", playlists_url, headers=headers)
    playlist_response = requests.get(playlists_url, headers=headers)

    if playlist_response.status_code == 200:
        root = ET.fromstring(playlist_response.content)
        playlists = [
            (
                playlist.get("key"),
                playlist.get("title"),
                playlist.get("duration"),
                playlist.get("leafCount"),
                playlist.get("playlistType"),
            )
            for playlist in root.findall(".//Playlist")
        ]
        for key, title, duration, leaf_count, playlistType in playlists:
            if playlistType == "audio":
                print(f"Key: {key}, Title: {title}, Duration: {duration}, Leaf Count: {leaf_count}")
                items_response = requests.request("GET", url + key, headers=headers)
                if items_response.status_code == 200:
                    root = ET.fromstring(items_response.content)
                    items = [
                        (
                            item.get("key"),
                            item.get("title"),
                            item.get("duration"),
                            item.get("index"),
                            item.get("type"),
                            item.get("parentTitle"),
                            item.get("grandparentTitle"),
                        )
                        for item in root.findall(".//Track")
                    ]
                    for key, title, duration, index, item_type, parent_title, grandparent_title in items:
                        print(
                            f"\tKey: {key}, Type: {item_type}, Title: {grandparent_title}/{parent_title}/{title}, Index: {index}, Duration: {duration}"
                        )

    else:
        print(f"Failed to retrieve data: {playlist_response.status_code}")
