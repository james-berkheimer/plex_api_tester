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

    def fetch_playlists(self) -> Optional[ET.Element]:
        """Fetch playlists and return XML root."""
        return self._get("/playlists")

    def fetch_playlist_items(self, playlist_key: str) -> Optional[ET.Element]:
        """Fetch items from a specific playlist."""
        return self._get(playlist_key)


class PlexPlaylistParser:
    @staticmethod
    def parse_playlists(root: ET.Element) -> List[Tuple[str, str, str]]:
        """Parse XML root and return a list of tuples (key, title, type)."""
        if root is None:
            return []

        return [
            (playlist.get("key"), playlist.get("title"), playlist.get("playlistType"))
            for playlist in root.findall(".//Playlist")
            if playlist.get("key") and playlist.get("title") and playlist.get("playlistType")
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


# Helper functions for data extraction


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


# Public interface functions


def get_playlist_key(playlist_title: str) -> Optional[Tuple[str, str]]:
    """Find and return the key and type of a specific playlist title."""
    client = PlexAPIClient()
    root = client.fetch_playlists()
    if root is None:
        return None

    playlists = PlexPlaylistParser.parse_playlists(root)
    result = next((item for item in playlists if item[1] == playlist_title), None)

    if result:
        key, title, playlist_type = result
        return key, playlist_type
    else:
        logger.info(f"Playlist titled '{playlist_title}' not found.")
        return None


def get_playlist_items(playlist_key: str, playlist_type: str) -> List[Dict[str, Any]]:
    """Fetch and process playlist items based on their type."""
    client = PlexAPIClient()
    root = client.fetch_playlist_items(playlist_key)
    return PlexPlaylistParser.parse_playlist_items(root, playlist_type)
