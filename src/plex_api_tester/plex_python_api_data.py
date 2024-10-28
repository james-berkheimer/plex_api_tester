import re
from typing import Dict, List, Union

from plexapi.audio import Track
from plexapi.base import MediaContainer
from plexapi.photo import Photo
from plexapi.server import PlexServer
from plexapi.video import Episode, Movie

from .plex import AuthenticationError, PlexAuthentication

try:
    plex_auth = PlexAuthentication()
    plex_server = PlexServer(baseurl=plex_auth.baseurl, token=plex_auth.token)
except AuthenticationError as e:
    raise RuntimeError("Failed to initialize Plex server") from e


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


###################################################


def _get_sorted_artists(playlist_items):
    artists = {}
    for item in playlist_items:
        if type(item).__name__ == "Track":
            cleaned_name = re.sub(r"\W+", "", item.grandparentTitle).lower()
            artists[cleaned_name] = item.grandparentTitle
    sorted_artists = [artists[artist] for artist in sorted(artists.keys())]
    return sorted_artists


def _playlist_audio_data(playlist_title):
    data = {}
    playlist = plex_server.playlist(playlist_title)
    sorted_artists = _get_sorted_artists(playlist.items())
    for artist_name in sorted_artists:
        if artist_name not in data:
            data[artist_name] = {}
        for item in playlist.items():
            if type(item).__name__ == "Track" and item.grandparentTitle.strip() == artist_name:
                album_title = item.parentTitle.strip()
                if album_title not in data[artist_name]:
                    data[artist_name][album_title] = []
                track_title = item.title.strip()
                track_number = item.trackNumber
                data[artist_name][album_title].append([track_title, track_number])
    return data


def _playlist_audio_details(playlist_title):
    details_dict = {}
    playlist = plex_server.playlist(playlist_title)
    details_dict["title"] = playlist.title
    details_dict["total_items"] = len(playlist.items())

    days = playlist.duration // (24 * 3600 * 1000)
    hours = (playlist.duration % (24 * 3600 * 1000)) // (3600 * 1000)
    minutes = (playlist.duration % (3600 * 1000)) // 60000
    seconds = (playlist.duration % 60000) // 1000
    details_dict["duration"] = f"{days}:{hours}:{minutes}:{seconds}"

    return details_dict


def _playlist_photo_details(playlist_title):
    pass


def _playlist_video_details(playlist_title):
    pass


def _get_sorted_titles(playlist_items):
    titles = {}
    for item in playlist_items:
        item_type = type(item).__name__
        if item_type == "Episode":
            cleaned_title = re.sub(r"\W+", "", item.grandparentTitle).lower()
            titles[cleaned_title] = item.grandparentTitle
        elif item_type == "Movie":
            cleaned_title = re.sub(r"\W+", "", item.title).lower()
            titles[cleaned_title] = item.title
    sorted_titles = [titles[title] for title in sorted(titles.keys())]
    return sorted_titles


def _playlist_video_data(playlist_title):
    data = {"Episode": {}, "Movie": {}}
    playlist = plex_server.playlist(playlist_title)
    sorted_titles = _get_sorted_titles(playlist.items())
    for title in sorted_titles:
        for item in playlist.items():
            item_type = type(item).__name__
            if item_type == "Episode" and item.grandparentTitle.strip() == title:
                if title not in data[item_type]:
                    data[item_type][title] = {}

                season_title = item.parentTitle.strip()
                if season_title not in data[item_type][title]:
                    data[item_type][title][season_title] = []

                episode_title = item.title.strip()
                episode_number = item.index
                data[item_type][title][season_title].append([episode_title, episode_number])

            elif item_type == "Movie" and item.title.strip() == title:
                movie_year = item.year
                data[item_type][title] = movie_year

    return data


def _playlist_photo_data(playlist_title):
    data = {}
    plex_server_ip = "192.168.1.42"
    plex_server_port = 32400
    playlist = plex_server.playlist(playlist_title)

    for item in playlist.items():
        if type(item).__name__ == "Photo":
            photo_title = item.title.strip()
            thumb_url = f"http://{plex_server_ip}:{plex_server_port}{item.thumb}"
            data[photo_title] = thumb_url

    return data


def playlist_data(playlist_type, playlist_title):
    if playlist_type == "audio":
        return _playlist_audio_data(playlist_title)
    if playlist_type == "video":
        return _playlist_video_data(playlist_title)
    if playlist_type == "photo":
        return _playlist_photo_data(playlist_title)
    return None


def playlist_details(playlist_type, playlist_title):
    if playlist_type == "audio":
        return _playlist_audio_details(playlist_title)
    if playlist_type == "video":
        return _playlist_video_details(playlist_title)
    if playlist_type == "photo":
        return _playlist_photo_details(playlist_title)
    return None
