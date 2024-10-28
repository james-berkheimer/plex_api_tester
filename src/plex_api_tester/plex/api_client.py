# src/plex_api_tester/plex/api_client.py

"""
api_client.py for Plex API Module

This module contains the main client class for interacting with the Plex server API
and utility methods for parsing playlist data.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree

import requests

from .. import utils
from . import config_instance

logger = utils.create_logger(level=logging.INFO)


class PlexAPIClient:
    def __init__(self):
        self.plex_base_url = config_instance.baseurl
        if not self.plex_base_url:
            raise ValueError("PLEX_BASEURL variable not set")

        self.api_key = config_instance.token
        if not self.api_key:
            raise ValueError("PLEX_TOKEN variable not set")

        self.headers = {"X-Plex-Token": self.api_key}

    def _request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> Optional[Union[ElementTree.Element, requests.Response]]:
        """
        Unified request handler for GET, POST, and DELETE methods.

        :param method: The HTTP method ("GET", "POST", or "DELETE").
        :param endpoint: The API endpoint to access.
        :param data: Optional data to send with the request (for POST requests).
        :return: XML Element for GET requests, Response object for POST/DELETE, None on failure.
        """
        url = f"{self.plex_base_url}{endpoint}"
        try:
            response = requests.request(
                method, url, headers=self.headers, params=data, timeout=config_instance.TIMEOUT
            )
            response.raise_for_status()
            return ElementTree.fromstring(response.content) if method == "GET" else response
        except requests.RequestException as e:
            logger.error(f"Error with {method} request to {url}: {e}")
            return None
        except ElementTree.ParseError as e:
            logger.error(f"Error parsing XML response from {url}: {e}")
            return None

    def create_playlist(
        self, title: str, media_type: str, item_uris: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new playlist in Plex.

        :param title: The title of the playlist.
        :param media_type: The type of media in the playlist.
        :param item_uris: A list of item URIs to include in the playlist.
        :return: The response JSON if the playlist was created successfully, None otherwise.
        """
        uri_param = ",".join([f"library://{uri}" for uri in item_uris])
        data = {"type": media_type, "title": title, "uri": uri_param}
        response = self._request("POST", "/playlists", data)
        if response is not None and response.status_code == 201:
            logger.info(f"Playlist '{title}' created successfully.")
            return response.json()
        else:
            logger.error(f"Failed to create playlist '{title}'.")
            return None

    def delete_playlist(self, playlist_ratingKey: str) -> bool:
        """
        Delete a playlist in Plex.

        :param playlist_ratingKey: The key (or ratingKey) of the playlist to delete.
        :return: True if the playlist was successfully deleted, False otherwise.
        """
        response = self._request("DELETE", f"/playlists/{playlist_ratingKey}")
        if response is not None and response.status_code in [200, 204]:
            logger.info(f"Playlist with key '{playlist_ratingKey}' deleted successfully.")
            return True
        else:
            logger.error(f"Failed to delete playlist with key '{playlist_ratingKey}'.")
            return False

    def get_playlists(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Retrieve all playlists from Plex.

        :return: A dictionary of playlists categorized by their type.
        """
        root = self.fetch_playlists()
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

    def get_playlist_ratingKey(self, playlist_title: str) -> Optional[Tuple[str, str]]:
        """
        Retrieve the ratingKey of a playlist by its title.

        :param playlist_title: The title of the playlist.
        :return: The ratingKey of the playlist if found, None otherwise.
        """
        root = self.fetch_playlists()
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

    def get_playlist_items(self, playlist_ratingKey: str) -> List[Dict[str, Any]]:
        """
        Retrieve items from a specific playlist.

        :param playlist_ratingKey: The key (or ratingKey) of the playlist.
        :return: A list of items in the playlist.
        """
        metadata_root = self.fetch_playlist_metadata(f"/playlists/{playlist_ratingKey}")
        playlist_element = metadata_root.find(".//Playlist") if metadata_root else None
        if playlist_element is None:
            logger.error("Playlist metadata not found.")
            return []

        playlist_type = playlist_element.get("playlistType")
        items_root = self.fetch_playlist_items(f"/playlists/{playlist_ratingKey}/items")
        return PlexPlaylistParser.extract_playlist_items(items_root, playlist_type)

    def fetch_playlists(self) -> Optional[ElementTree.Element]:
        """
        Fetch playlists and return XML root.

        :return: The XML root element of the playlists.
        """
        return self._request("GET", "/playlists")

    def fetch_playlist_metadata(self, playlist_url: str) -> Optional[ElementTree.Element]:
        """
        Fetch metadata for a playlist.

        :param playlist_url: The URL of the playlist metadata.
        :return: The XML root element of the playlist metadata.
        """
        return self._request("GET", playlist_url)

    def fetch_playlist_items(self, playlist_key: str) -> Optional[ElementTree.Element]:
        """
        Fetch items from a specific playlist.

        :param playlist_key: The key (or ratingKey) of the playlist.
        :return: The XML root element of the playlist items.
        """
        return self._request("GET", playlist_key)

    def parse_playlist_data(
        self, data: List[Dict[str, Any]]
    ) -> Dict[str, Union[Dict[str, Dict[str, List[Tuple[str, int, str]]]], Dict[str, Dict[str, str]]]]:
        """
        Parse playlist data into a structured format.

        :param data: A list of dictionaries containing playlist data.
        :return: A dictionary of parsed playlist data categorized by media type.
        """
        sorted_data = {
            "tracks": {},
            "photos": {},
            "episodes": {},
            "movies": {},
        }
        plex_base_url = self.plex_base_url

        for item in data:
            try:
                item_type = item.get("type")
                if item_type == "track":
                    PlexPlaylistParser.parse_track_item(item, sorted_data)
                elif item_type == "photo":
                    PlexPlaylistParser.parse_photo_item(item, sorted_data, plex_base_url)
                elif item_type == "episode":
                    PlexPlaylistParser.parse_episode_item(item, sorted_data)
                elif item_type == "movie":
                    PlexPlaylistParser.parse_movie_item(item, sorted_data)
            except Exception as e:
                logger.error(f"Error processing item: {item}, error: {e}")

        return sorted_data

    def remove_playlist_items(self, playlist_ratingKey: str, playlistItemIDs: List[str]) -> bool:
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
                    logger.error(
                        f"Failed to remove item from playlist. Status code: {response.status_code}"
                    )
                return False

        return True


class PlexPlaylistParser:
    @staticmethod
    def extract_playlists(root: ElementTree.Element) -> List[Tuple[str, str, str]]:
        """
        Parse XML root and return a list of tuples (key, title, type) for each playlist.

        :param root: XML root element containing playlist data.
        :return: List of tuples with (ratingKey, title, playlistType).
        """
        if root is None:
            return []

        return [
            (playlist.get("ratingKey"), playlist.get("title"), playlist.get("playlistType"))
            for playlist in root.findall(".//Playlist")
            if playlist.get("ratingKey") and playlist.get("title") and playlist.get("playlistType")
        ]

    @staticmethod
    def extract_playlist_items(root: ElementTree.Element, playlist_type: str) -> List[Dict[str, Any]]:
        """
        Parse and extract data from playlist items based on the playlist type.

        :param root: XML root element containing playlist item data.
        :param playlist_type: Type of playlist ('audio', 'video', or 'photo').
        :return: List of dictionaries containing parsed item data.
        """
        items = []
        if root is None:
            return items

        if playlist_type == "audio":
            items = [PlexPlaylistParser._extract_audio_data(track) for track in root.findall(".//Track")]
        elif playlist_type == "video":
            items = [PlexPlaylistParser._extract_video_data(video) for video in root.findall(".//Video")]
        elif playlist_type == "photo":
            items = [PlexPlaylistParser._extract_photo_data(photo) for photo in root.findall(".//Photo")]

        return items

    @staticmethod
    def _extract_audio_data(track: ElementTree.Element) -> Dict[str, str]:
        """
        Extract data from an audio track element.

        :param track: XML element representing an audio track.
        :return: Dictionary with track details.
        """
        return {
            "key": PlexPlaylistParser._safe_get(track, "key"),
            "title": PlexPlaylistParser._safe_get(track, "title"),
            "duration": PlexPlaylistParser._safe_get(track, "duration"),
            "index": PlexPlaylistParser._safe_get(track, "index"),
            "type": PlexPlaylistParser._safe_get(track, "type"),
            "parentTitle": PlexPlaylistParser._safe_get(track, "parentTitle"),
            "grandparentTitle": PlexPlaylistParser._safe_get(track, "grandparentTitle"),
            "grandparentThumb": PlexPlaylistParser._safe_get(track, "grandparentThumb"),
            "playlistItemID": PlexPlaylistParser._safe_get(track, "playlistItemID"),
        }

    @staticmethod
    def _extract_video_data(video: ElementTree.Element) -> Dict[str, str]:
        """
        Extract data from a video element, either episode or movie.

        :param video: XML element representing a video item.
        :return: Dictionary with video details.
        """
        item_type = PlexPlaylistParser._safe_get(video, "type")
        if item_type == "episode":
            return {
                "key": PlexPlaylistParser._safe_get(video, "key"),
                "title": PlexPlaylistParser._safe_get(video, "title"),
                "duration": PlexPlaylistParser._safe_get(video, "duration"),
                "index": PlexPlaylistParser._safe_get(video, "index"),
                "type": item_type,
                "parentTitle": PlexPlaylistParser._safe_get(video, "parentTitle"),
                "grandparentTitle": PlexPlaylistParser._safe_get(video, "grandparentTitle"),
                "grandparentThumb": PlexPlaylistParser._safe_get(video, "grandparentThumb"),
                "playlistItemID": PlexPlaylistParser._safe_get(video, "playlistItemID"),
            }
        elif item_type == "movie":
            return {
                "key": PlexPlaylistParser._safe_get(video, "key"),
                "title": PlexPlaylistParser._safe_get(video, "title"),
                "type": item_type,
                "duration": PlexPlaylistParser._safe_get(video, "duration"),
                "year": PlexPlaylistParser._safe_get(video, "year"),
                "thumb": PlexPlaylistParser._safe_get(video, "thumb"),
                "playlistItemID": PlexPlaylistParser._safe_get(video, "playlistItemID"),
            }

    @staticmethod
    def _extract_photo_data(photo: ElementTree.Element) -> Dict[str, str]:
        """
        Extract data from a photo element.

        :param photo: XML element representing a photo item.
        :return: Dictionary with photo details.
        """
        return {
            "key": PlexPlaylistParser._safe_get(photo, "key"),
            "title": PlexPlaylistParser._safe_get(photo, "title"),
            "type": PlexPlaylistParser._safe_get(photo, "type"),
            "thumb": PlexPlaylistParser._safe_get(photo, "thumb"),
            "playlistItemID": PlexPlaylistParser._safe_get(photo, "playlistItemID"),
            "file": PlexPlaylistParser._safe_get(photo.find(".//Part"), "file")
            if photo.find(".//Part") is not None
            else None,
        }

    @staticmethod
    def parse_track_item(item: Dict[str, Any], sorted_data: Dict[str, Any]) -> None:
        artist = item.get("grandparentTitle")
        album = item.get("parentTitle")
        track = (item.get("title"), int(item.get("index") or 0), item.get("playlistItemID"))

        if artist and album:
            artist_data = sorted_data["tracks"].setdefault(artist, {})
            album_data = artist_data.setdefault(album, [])
            album_data.append(track)

    @staticmethod
    def parse_photo_item(item: Dict[str, Any], sorted_data: Dict[str, Any], plex_base_url: str) -> None:
        title = item.get("title")
        if title:
            sorted_data["photos"][title] = {
                "file": f"{plex_base_url}/{item.get('file')}",
                "thumb": f"{plex_base_url}/{item.get('thumb')}",
                "playlistItemID": item.get("playlistItemID"),
            }

    @staticmethod
    def parse_episode_item(item: Dict[str, Any], sorted_data: Dict[str, Any]) -> None:
        show = item.get("grandparentTitle")
        season = item.get("parentTitle")
        episode = (item.get("title"), int(item.get("index") or 0), item.get("playlistItemID"))

        if show and season:
            show_data = sorted_data["episodes"].setdefault(show, {})
            season_data = show_data.setdefault(season, [])
            season_data.append(episode)

    @staticmethod
    def parse_movie_item(item: Dict[str, Any], sorted_data: Dict[str, Any]) -> None:
        title = item.get("title")
        if title:
            sorted_data["movies"][title] = {
                "year": item.get("year"),
                "duration": item.get("duration"),
                "playlistItemID": item.get("playlistItemID"),
            }

    @staticmethod
    def _safe_get(element: Optional[ElementTree.Element], attribute: str) -> Optional[str]:
        """
        Safely get an attribute value from an XML element.

        :param element: XML element to retrieve attribute from.
        :param attribute: Attribute name to retrieve.
        :return: Attribute value as a string, or None if not found.
        """
        return element.get(attribute) if element is not None else None
