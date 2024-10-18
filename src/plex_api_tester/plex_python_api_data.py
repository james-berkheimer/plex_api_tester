from typing import Dict, List, Union

from plexapi.audio import Track
from plexapi.base import MediaContainer
from plexapi.photo import Photo
from plexapi.video import Episode, Movie

from .plex.server import get_server

plex_server = get_server()


def get_playlist_data(title: str) -> List[Dict[str, str]]:
    """Fetch and parse the items of a playlist by title.

    Args:
        title (str): The title of the playlist.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing parsed playlist item data.
    """
    playlist = plex_server.playlist(title)
    playlist_items = playlist.items()
    playlist_type = playlist.playlistType
    return parse_playlist_data(playlist_items, playlist_type)


def parse_playlist_data(playlist_items: MediaContainer, playlist_type: str):
    """Parse the items of a playlist."""
    parsed_items = []
    for playlist_item in playlist_items:
        if playlist_type == "audio":
            audio_data = _extract_audio_data(playlist_item)
            parsed_items.append(audio_data)
        elif playlist_type == "video":
            video_data = _extract_video_data(playlist_item)
            parsed_items.append(video_data)
        elif playlist_type == "photo":
            photo_data = _extract_photo_data(playlist_item)
            parsed_items.append(photo_data)

    return parsed_items


def _extract_audio_data(track: Track) -> Dict[str, str]:
    """Extract data from an audio track."""
    return {
        "key": track.key,
        "title": track.title,
        "duration": track.duration,
        "index": track.index,
        "type": track.type,
        "parentTitle": track.parentTitle,
        "grandparentTitle": track.grandparentTitle,
        "grandparentThumb": track.grandparentThumb,
    }


def _extract_video_data(video: Union[Episode, Movie]) -> Dict[str, str]:
    """Extract data from a video item, either episode or movie."""
    item_type = video.type
    if item_type == "episode":
        return {
            "key": video.key,
            "title": video.title,
            "duration": video.duration,
            "index": video.index,
            "parentTitle": video.parentTitle,
            "grandparentTitle": video.grandparentTitle,
            "grandparentThumb": video.grandparentThumb,
        }
    elif item_type == "movie":
        return {
            "key": video.key,
            "title": video.title,
            "type": video.type,
            "duration": video.duration,
            "year": video.year,
            "thumb": video.thumb,
        }


def _extract_photo_data(photo: Photo) -> Dict[str, str]:
    """Extract data from a photo item."""
    return {
        "key": photo.key,
        "title": photo.title,
        "type": photo.type,
        "thumb": photo.thumb,
    }
