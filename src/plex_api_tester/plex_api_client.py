import logging
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from . import utils

logger = utils.create_logger(level=logging.INFO)


class PlexAPIClient:
    def __init__(self):
        self.plex_base_url = os.getenv("PLEX_BASEURL")
        if not self.plex_base_url:
            raise ValueError("PLEX_BASEURL environment variable not set")

        self.api_key = os.getenv("PLEX_TOKEN")
        if not self.api_key:
            raise ValueError("PLEX_TOKEN environment variable not set")

        self.headers = {"X-Plex-Token": self.api_key}

    def _get(self, endpoint: str) -> Optional[ET.Element]:
        """
        Make a GET request to the Plex API and return the XML root.

        :param endpoint: The API endpoint to fetch.
        :return: The root XML element or None on error.
        """
        url = f"{self.plex_base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return ET.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Plex API: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"Error parsing XML response: {e}")
            return None

    def _post(self, endpoint: str, data: dict) -> Optional[requests.Response]:
        """
        Send a POST request to the specified Plex API endpoint.

        Constructs the URL, sets headers, and sends the request with the provided data.
        Logs any errors and returns the response if successful.

        :param endpoint: API endpoint to send the request to.
        :param data: Data to include in the POST request.
        :return: Response object on success, None on failure.
        """
        url = f"{self.plex_base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, params=data)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending POST request to Plex API: {e}")
            return None

    def _delete(self, endpoint: str) -> Optional[requests.Response]:
        """
        Send a DELETE request to the specified Plex API endpoint.

        Constructs the URL, sends the request, and logs any errors. Returns the response
        on success, or None on failure.

        :param endpoint: API endpoint to send the request to.
        :return: Response object on success, None on failure.
        """
        url = f"{self.plex_base_url}{endpoint}"
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending DELETE request to Plex API: {e}")
            return None

    def fetch_playlists(self) -> Optional[ET.Element]:
        """Fetch playlists and return XML root."""
        return self._get("/playlists")

    def fetch_playlist_metadata(self, playlist_url: str) -> Optional[ET.Element]:
        """Fetch metadata for a playlist using the unified _get method."""
        return self._get(playlist_url)

    def fetch_playlist_items(self, playlist_key: str) -> Optional[ET.Element]:
        """Fetch items from a specific playlist."""
        return self._get(playlist_key)


class PlexPlaylistParser:
    @staticmethod
    def extract_playlists(root: ET.Element) -> List[Tuple[str, str, str]]:
        """Parse XML root and return a list of tuples (key, title, type)."""
        if root is None:
            return []

        return [
            (playlist.get("ratingKey"), playlist.get("title"), playlist.get("playlistType"))
            for playlist in root.findall(".//Playlist")
            if playlist.get("ratingKey") and playlist.get("title") and playlist.get("playlistType")
        ]

    @staticmethod
    def extract_playlist_items(root: ET.Element, playlist_type: str) -> List[Dict[str, Any]]:
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
        "key": _safe_get(track, "key"),
        "title": _safe_get(track, "title"),
        "duration": _safe_get(track, "duration"),
        "index": _safe_get(track, "index"),
        "type": _safe_get(track, "type"),
        "parentTitle": _safe_get(track, "parentTitle"),
        "grandparentTitle": _safe_get(track, "grandparentTitle"),
        "grandparentThumb": _safe_get(track, "grandparentThumb"),
        "playlistItemID": _safe_get(track, "playlistItemID"),
    }


def _extract_video_data(video: ET.Element) -> Dict[str, str]:
    """Extract data from a video item, either episode or movie."""
    item_type = _safe_get(video, "type")
    if item_type == "episode":
        return {
            "key": _safe_get(video, "key"),
            "title": _safe_get(video, "title"),
            "duration": _safe_get(video, "duration"),
            "index": _safe_get(video, "index"),
            "type": item_type,
            "parentTitle": _safe_get(video, "parentTitle"),
            "grandparentTitle": _safe_get(video, "grandparentTitle"),
            "grandparentThumb": _safe_get(video, "grandparentThumb"),
            "playlistItemID": _safe_get(video, "playlistItemID"),
        }
    elif item_type == "movie":
        return {
            "key": _safe_get(video, "key"),
            "title": _safe_get(video, "title"),
            "type": item_type,
            "duration": _safe_get(video, "duration"),
            "year": _safe_get(video, "year"),
            "thumb": _safe_get(video, "thumb"),
            "playlistItemID": _safe_get(video, "playlistItemID"),
        }


def _extract_photo_data(photo: ET.Element) -> Dict[str, str]:
    """Extract data from a photo item."""
    return {
        "key": _safe_get(photo, "key"),
        "title": _safe_get(photo, "title"),
        "type": _safe_get(photo, "type"),
        "thumb": _safe_get(photo, "thumb"),
        "playlistItemID": _safe_get(photo, "playlistItemID"),
        "file": _safe_get(photo.find(".//Part"), "file") if photo.find(".//Part") is not None else None,
    }


def _safe_get(element: Optional[ET.Element], attribute: str) -> Optional[str]:
    """
    Safely get an attribute value from an XML element.

    Returns None if the element or attribute is missing.
    """
    return element.get(attribute) if element is not None else None


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
        "type": media_type,
        "title": title,
        "uri": uri_param,
    }

    response = client._post("/playlists", data)

    if response is not None and response.status_code == 201:
        logger.info(f"Playlist '{title}' created successfully.")
        return response.json()
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

    endpoint = f"/playlists/{playlist_ratingKey}"

    try:
        response = requests.delete(f"{client.plex_base_url}{endpoint}", headers=client.headers)

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

    playlists = PlexPlaylistParser.extract_playlists(root)
    result = next((item for item in playlists if item[1] == playlist_title), None)

    if result:
        ratingKey, _, _ = result
        return ratingKey
    else:
        logger.error(f"Playlist titled '{playlist_title}' not found.")
        return None


def get_playlist_items(playlist_ratingKey: str) -> List[Dict[str, Any]]:
    """
    Fetch and process playlist items based on the playlist type.

    :param playlist_ratingKey: The unique key of the playlist.
    :return: A list of playlist items, where each item is represented as a dictionary.
    """
    if playlist_ratingKey is None:
        logger.error("Playlist ratingKey cannot be None.")
        return None

    playlist_metadata_url = f"/playlists/{playlist_ratingKey}"
    client = PlexAPIClient()

    metadata_root = client.fetch_playlist_metadata(playlist_metadata_url)

    playlist_element = metadata_root.find(".//Playlist")

    if playlist_element is not None:
        playlist_type = playlist_element.get("playlistType")
    else:
        raise ValueError("Playlist metadata not found")

    playlist_items_url = f"/playlists/{playlist_ratingKey}/items"
    root = client.fetch_playlist_items(playlist_items_url)
    return PlexPlaylistParser.extract_playlist_items(root, playlist_type)


def parse_playlist_data(
    data: List[Dict[str, Any]],
) -> Dict[str, Union[Dict[str, Dict[str, List[Tuple[str, int, str]]]], Dict[str, Dict[str, str]]]]:
    """
    Parse and organize playlist data into a nested dictionary structure.

    The function processes different types of playlist items (track, photo, episode, movie)
    and organizes them into a nested dictionary structure.

    :param data: A list of playlist items, where each item is represented as a dictionary.
    :return: A nested dictionary with the following structure:
             {
                 "tracks": {
                     "artist_name": {
                         "album_name": [
                             ("track_title", track_index, "playlistItemID"),
                             ...
                         ],
                         ...
                     },
                     ...
                 },
                 "photos": {
                     "photo_title": {
                         "file": "file_url",
                         "thumb": "thumb_url",
                         "playlistItemID": "playlistItemID"
                     },
                     ...
                 },
                 "episodes": {
                     "show_name": {
                         "season_name": [
                             ("episode_title", episode_index, "playlistItemID"),
                             ...
                         ],
                         ...
                     },
                     ...
                 },
                 "movies": {
                     "movie_title": {
                         "year": "year",
                         "duration": "duration",
                         "playlistItemID": "playlistItemID"
                     },
                     ...
                 }
             }
    """
    sorted_data = {
        "tracks": {},
        "photos": {},
        "episodes": {},
        "movies": {},
    }
    plex_base_url = os.getenv("PLEX_BASEURL")

    for item in data:
        try:
            item_type = item.get("type")

            if item_type == "track":
                artist = item.get("grandparentTitle")
                album = item.get("parentTitle")
                track = [item.get("title"), item.get("index"), item.get("playlistItemID")]

                if not artist or not album or not track:
                    logger.warning(f"Missing data in track item: {item}")
                    continue

                artist_data = sorted_data["tracks"].setdefault(artist, {})
                album_data = artist_data.setdefault(album, [])
                album_data.append(track)

            elif item_type == "photo":
                title = item.get("title")
                if not title:
                    logger.warning(f"Missing title in photo item: {item}")
                    continue

                sorted_data["photos"][title] = {
                    "file": f"{plex_base_url}/{item.get('file')}",
                    "thumb": f"{plex_base_url}/{item.get('thumb')}",
                    "playlistItemID": item.get("playlistItemID"),
                }

            elif item_type == "episode":
                show = item.get("grandparentTitle")
                season = item.get("parentTitle")
                episode = [item.get("title"), item.get("index"), item.get("playlistItemID")]

                if not show or not season or not episode:
                    logger.warning(f"Missing data in episode item: {item}")
                    continue

                show_data = sorted_data["episodes"].setdefault(show, {})
                season_data = show_data.setdefault(season, [])
                season_data.append(episode)

            elif item_type == "movie":
                title = item.get("title")
                if not title:
                    logger.warning(f"Missing title in movie item: {item}")
                    continue

                sorted_data["movies"][title] = {
                    "year": item.get("year"),
                    "duration": item.get("duration"),
                    "playlistItemID": item.get("playlistItemID"),
                }

            else:
                logger.warning(f"Unknown item type: {item_type} in item: {item}")

        except Exception as e:
            logger.error(f"Error processing item: {item}, error: {e}")

    return sorted_data


def remove_playlist_items(playlist_ratingKey: str, playlistItemIDs: List[str]) -> bool:
    """
    Remove items from a playlist in Plex.

    :param playlist_ratingKey: The key (or ratingKey) of the playlist.
    :param playlistItemIDs: A list of playlistItemIDs to remove from the playlist.
    :return: True if the items were successfully removed, False otherwise.
    """
    client = PlexAPIClient()

    for playlistItemID in playlistItemIDs:
        endpoint = f"/playlists/{playlist_ratingKey}/items/{playlistItemID}"
        response = client._delete(endpoint)

        if response is not None and response.status_code in [200, 204]:
            logger.info(f"Item removed from playlist with key '{playlist_ratingKey}' successfully.")
        else:
            if response is None:
                logger.error("Failed to remove item from playlist. No response received.")
            else:
                logger.error(f"Failed to remove item from playlist. Status code: {response.status_code}")
            return False

    return True
