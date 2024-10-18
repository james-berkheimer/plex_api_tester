import logging
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import requests

from . import utils

logger = utils.create_logger(level=logging.INFO)


class PlexAPIClient:
    def __init__(self):
        self.base_url = os.getenv("PLEX_BASEURL")
        self.api_key = os.getenv("PLEX_TOKEN")
        self.headers = {"X-Plex-Token": self.api_key}

    def _get(self, endpoint: str) -> Optional[ET.Element]:
        """Make a GET request to the Plex API and return the XML root."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return ET.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Plex API: {e}")
            return None
        except ET.ParseError:
            logger.error("Error parsing the XML response.")
            return None

    def _post(self, endpoint: str, data: dict) -> requests.Response:
        """Make a POST request to the Plex API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, params=data)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending POST request to Plex API: {e}")
            return None

    def fetch_playlists(self) -> Optional[ET.Element]:
        """Fetch playlists and return XML root."""
        return self._get("/playlists")

    def fetch_playlist_items(self, playlist_key: str) -> Optional[ET.Element]:
        """Fetch items from a specific playlist."""
        return self._get(playlist_key)

    def fetch_playlist_metadata(self, playlist_url: str) -> Optional[ET.Element]:
        """
        Fetch metadata for a given playlist.

        :param playlist_url: The URL path to the playlist.
        :return: The root of the XML metadata response.
        """
        try:
            response = requests.get(f"{self.base_url}{playlist_url}", headers=self.headers)
            response.raise_for_status()
            return ET.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching playlist metadata: {e}")
            return None
        except ET.ParseError:
            logger.error("Error parsing the XML response.")
            return None


class PlexPlaylistParser:
    @staticmethod
    def parse_playlists(root: ET.Element) -> List[Tuple[str, str, str]]:
        """Parse XML root and return a list of tuples (key, title, type)."""
        if root is None:
            return []

        return [
            (playlist.get("ratingKey"), playlist.get("title"), playlist.get("playlistType"))
            for playlist in root.findall(".//Playlist")
            if playlist.get("ratingKey") and playlist.get("title") and playlist.get("playlistType")
        ]

    @staticmethod
    def parse_playlist_items(root: ET.Element, playlist_type: str) -> List[Dict[str, Any]]:
        """Parse and extract data from playlist items based on the playlist type."""
        items = []
        if root is None:
            return items

        if playlist_type == "audio":
            items = [_extract_audio_data(track) for track in root.findall(".//Track")]
        elif playlist_type == "video":
            items = [_extract_video_data(video) for video in root.findall(".//Video")]
        elif playlist_type == "photo":
            items = [_extract_photo_data(photo) for photo in root.findall(".//Photo")]

        return items


##
# Helper functions for data extraction
##


def _extract_audio_data(track: ET.Element) -> Dict[str, str]:
    """Extract data from an audio track."""
    return {
        "key": track.get("key"),
        "title": track.get("title"),
        "duration": track.get("duration"),
        "index": track.get("index"),
        "type": track.get("type"),
        "parentTitle": track.get("parentTitle"),
        "grandparentTitle": track.get("grandparentTitle"),
        "grandparentThumb": track.get("grandparentThumb"),
    }


def _extract_video_data(video: ET.Element) -> Dict[str, str]:
    """Extract data from a video item, either episode or movie."""
    item_type = video.get("type")
    if item_type == "episode":
        return {
            "key": video.get("key"),
            "title": video.get("title"),
            "duration": video.get("duration"),
            "index": video.get("index"),
            "parentTitle": video.get("parentTitle"),
            "grandparentTitle": video.get("grandparentTitle"),
            "grandparentThumb": video.get("grandparentThumb"),
        }
    elif item_type == "movie":
        return {
            "key": video.get("key"),
            "title": video.get("title"),
            "type": video.get("type"),
            "duration": video.get("duration"),
            "year": video.get("year"),
            "thumb": video.get("thumb"),
        }


def _extract_photo_data(photo: ET.Element) -> Dict[str, str]:
    """Extract data from a photo item."""
    return {
        "key": photo.get("key"),
        "title": photo.get("title"),
        "type": photo.get("type"),
        "thumb": photo.get("thumb"),
        "file": photo.find(".//Part").get("file") if photo.find(".//Part") is not None else None,
    }


##
# Public interface functions
##


def create_playlist(title: str, media_type: str, item_uris: List[str]) -> Optional[Dict[str, Any]]:
    """
    Create a playlist in Plex.

    :param title: The name of the new playlist.
    :param media_type: The type of media ('audio', 'video', or 'photo').
    :param item_uris: A list of media URIs (ratingKeys) to add to the playlist.
    :return: JSON response from the API if successful, None if failed.
    """
    client = PlexAPIClient()

    # Plex expects media URIs to be passed as a single string, separated by commas.
    uri_param = ",".join([f"library://{uri}" for uri in item_uris])

    data = {
        "type": media_type,  # "audio", "video", or "photo"
        "title": title,
        "uri": uri_param,
    }

    response = client._post("/playlists", data)

    if response is not None and response.status_code == 201:
        logger.info(f"Playlist '{title}' created successfully.")
        return response.json()  # Assuming the API responds with JSON.
    else:
        logger.error(f"Failed to create playlist '{title}'.")
        return None


def delete_playlist(playlist_ratingKey: str) -> bool:
    """
    Delete a playlist in Plex.

    :param playlist_key: The key (or ratingKey) of the playlist to be deleted.
    :return: True if the playlist was successfully deleted, False otherwise.
    """
    client = PlexAPIClient()

    # The DELETE endpoint to remove a playlist
    endpoint = f"/playlists/{playlist_ratingKey}"

    try:
        response = requests.delete(f"{client.base_url}{endpoint}", headers=client.headers)

        if response.status_code in [200, 204]:
            logger.info(f"Playlist with key '{playlist_ratingKey}' deleted successfully.")
            return True
        else:
            logger.error(f"Failed to delete playlist. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error deleting playlist: {e}")
        return False


def get_playlists() -> Dict[str, List[Dict[str, str]]]:
    """
    Fetch all Plex playlists and categorize them by playlist type.

    :return: A dictionary where the keys are playlist types ('audio', 'video', 'photo'),
             and the values are lists of playlist details (key, title, type).
    """
    client = PlexAPIClient()
    root = client._get("/playlists")
    if root is None:
        return {}

    playlists_by_type = {}
    for playlist in root.findall(".//Playlist"):
        playlist_type = playlist.get("playlistType")
        playlist_data = {
            "ratingKey": playlist.get("ratingKey"),
            "title": playlist.get("title"),
            "playlistType": playlist_type,
        }
        # Group playlists by their type
        if playlist_type not in playlists_by_type:
            playlists_by_type[playlist_type] = []
        playlists_by_type[playlist_type].append(playlist_data)

    return playlists_by_type


def get_playlist_ratingKey(playlist_title: str) -> Optional[Tuple[str, str]]:
    """
    Find and return the key and type of a specific playlist by title.

    :param playlist_title: The title of the playlist to search for.
    :return: A tuple of (playlist key, playlist type) if found, None otherwise.
    """
    client = PlexAPIClient()
    root = client.fetch_playlists()
    if root is None:
        return None

    playlists = PlexPlaylistParser.parse_playlists(root)
    result = next((item for item in playlists if item[1] == playlist_title), None)

    if result:
        ratingKey, _, _ = result
        return ratingKey
    else:
        logger.info(f"Playlist titled '{playlist_title}' not found.")
        return None


def get_playlist_items(playlist_ratingKey: str) -> List[Dict[str, Any]]:
    """
    Fetch and process playlist items based on the playlist type.

    :param playlist_ratingKey: The unique key of the playlist.
    :return: A list of playlist items, where each item is represented as a dictionary.
    """
    # Fetch the metadata for the playlist to get the playlist type
    playlist_metadata_url = f"/playlists/{playlist_ratingKey}"
    client = PlexAPIClient()

    # Fetch the playlist metadata
    metadata_root = client.fetch_playlist_metadata(playlist_metadata_url)

    # Find the Playlist element inside the MediaContainer
    playlist_element = metadata_root.find(".//Playlist")

    if playlist_element is not None:
        playlist_type = playlist_element.get("playlistType")
    else:
        raise ValueError("Playlist metadata not found")

    # Now use the playlist type to fetch and process playlist items
    playlist_items_url = f"/playlists/{playlist_ratingKey}/items"
    root = client.fetch_playlist_items(playlist_items_url)
    return PlexPlaylistParser.parse_playlist_items(root, playlist_type)
