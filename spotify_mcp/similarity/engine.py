"""Core similarity engine functions for track matching."""

from enum import Enum
from typing import Any

from spotify_mcp.utils import make_spotify_request


class SearchScope(str, Enum):
    """Scope for similarity search."""

    CATALOG = "catalog"
    PLAYLIST = "playlist"
    ARTIST = "artist"
    ALBUM = "album"
    SAVED_TRACKS = "saved_tracks"


async def get_audio_features_for_tracks(
    track_ids: list[str],
) -> dict[str, dict[str, Any]]:
    """Get audio features for multiple tracks.

    Args:
        track_ids: List of Spotify track IDs

    Returns:
        Dictionary mapping track IDs to their audio features
    """
    features_map = {}

    # Spotify API supports up to 100 tracks at once
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i : i + 100]
        ids_param = ",".join(batch)

        try:
            data = await make_spotify_request(f"audio-features?ids={ids_param}")
            audio_features_list = data.get("audio_features", [])

            for features in audio_features_list:
                if features:  # Skip None values for unavailable tracks
                    features_map[features["id"]] = features
        except Exception:
            # If batch fails, try individual requests
            for track_id in batch:
                try:
                    features = await make_spotify_request(f"audio-features/{track_id}")
                    features_map[track_id] = features
                except Exception:
                    pass  # Skip tracks that fail

    return features_map


async def get_candidate_tracks(
    scope: SearchScope,
    scope_id: str | None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get candidate tracks based on search scope.

    Args:
        scope: Search scope (playlist, artist, album, saved_tracks)
        scope_id: ID for the scope (required for non-catalog scopes)
        limit: Maximum number of tracks to return

    Returns:
        List of track objects

    Raises:
        ValueError: If scope requires scope_id but none provided
    """
    if scope == SearchScope.CATALOG:
        # For catalog, we'll use recommendations API later
        return []

    elif scope == SearchScope.PLAYLIST:
        if not scope_id:
            raise ValueError("scope_id (playlist_id) is required for playlist scope")

        tracks = []
        offset = 0
        while len(tracks) < limit:
            data = await make_spotify_request(
                f"playlists/{scope_id}/tracks",
                params={"limit": min(50, limit - len(tracks)), "offset": offset},
            )
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                if item.get("track"):
                    tracks.append(item["track"])

            offset += len(items)

        return tracks

    elif scope == SearchScope.ARTIST:
        if not scope_id:
            raise ValueError("scope_id (artist_id) is required for artist scope")

        # Get artist's top tracks
        data = await make_spotify_request(
            f"artists/{scope_id}/top-tracks", params={"market": "US"}
        )
        tracks = data.get("tracks", [])

        # Also get albums and their tracks
        albums_data = await make_spotify_request(
            f"artists/{scope_id}/albums",
            params={"limit": 20, "include_groups": "album,single"},
        )

        for album in albums_data.get("items", [])[:5]:  # Limit to first 5 albums
            album_tracks_data = await make_spotify_request(
                f"albums/{album['id']}/tracks", params={"limit": 50}
            )
            # Need to fetch full track details
            for track in album_tracks_data.get("items", []):
                if len(tracks) < limit:
                    full_track = await make_spotify_request(f"tracks/{track['id']}")
                    tracks.append(full_track)

        return tracks[:limit]

    elif scope == SearchScope.ALBUM:
        if not scope_id:
            raise ValueError("scope_id (album_id) is required for album scope")

        data = await make_spotify_request(
            f"albums/{scope_id}/tracks", params={"limit": 50}
        )
        track_items = data.get("items", [])

        # Fetch full track details
        tracks = []
        for track in track_items:
            full_track = await make_spotify_request(f"tracks/{track['id']}")
            tracks.append(full_track)

        return tracks

    elif scope == SearchScope.SAVED_TRACKS:
        tracks = []
        offset = 0
        while len(tracks) < limit:
            data = await make_spotify_request(
                "me/tracks",
                params={"limit": min(50, limit - len(tracks)), "offset": offset},
            )
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                if item.get("track"):
                    tracks.append(item["track"])

            offset += len(items)

        return tracks

    return []


async def get_source_features(
    track_id: str | None,
    artist_id: str | None,
    playlist_id: str | None,
) -> dict[str, Any]:
    """Get audio features for the source entity.

    Args:
        track_id: Spotify track ID
        artist_id: Spotify artist ID
        playlist_id: Spotify playlist ID

    Returns:
        Audio features dictionary

    Raises:
        ValueError: If no source provided
    """
    if track_id:
        # Direct track features
        return await make_spotify_request(f"audio-features/{track_id}")

    elif artist_id:
        # Get average features from artist's top tracks
        data = await make_spotify_request(
            f"artists/{artist_id}/top-tracks", params={"market": "US"}
        )
        top_tracks = data.get("tracks", [])[:10]
        track_ids = [track["id"] for track in top_tracks]

        features_map = await get_audio_features_for_tracks(track_ids)
        return average_features(list(features_map.values()))

    elif playlist_id:
        # Get average features from playlist tracks
        data = await make_spotify_request(
            f"playlists/{playlist_id}/tracks", params={"limit": 20}
        )
        tracks = [item["track"] for item in data.get("items", []) if item.get("track")]
        track_ids = [track["id"] for track in tracks]

        features_map = await get_audio_features_for_tracks(track_ids)
        return average_features(list(features_map.values()))

    raise ValueError(
        "At least one of track_id, artist_id, or playlist_id must be provided"
    )


def average_features(features_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate average audio features from a list of feature dicts.

    Args:
        features_list: List of audio feature dictionaries

    Returns:
        Dictionary with averaged feature values

    Raises:
        ValueError: If features_list is empty
    """
    if not features_list:
        raise ValueError("Cannot average empty features list")

    numeric_keys = [
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "loudness",
        "speechiness",
        "valence",
        "tempo",
    ]

    avg_features = {}
    for key in numeric_keys:
        values = [f.get(key, 0.0) for f in features_list]
        avg_features[key] = sum(values) / len(values)

    return avg_features


async def get_track_genres(track: dict[str, Any]) -> list[str]:
    """Get genres for a track from its artists.

    Args:
        track: Track object from Spotify API

    Returns:
        List of genre strings (may be empty if no genres found)
    """
    all_genres = []

    # Get full artist data for each artist on the track
    for artist in track.get("artists", []):
        try:
            artist_data = await make_spotify_request(f"artists/{artist['id']}")
            all_genres.extend(artist_data.get("genres", []))
        except Exception:
            # Skip artists that fail to fetch
            continue

    # Return unique genres
    return list(set(all_genres))


async def get_source_genres(
    track_id: str | None,
    artist_id: str | None,
    playlist_id: str | None,
) -> list[str]:
    """Get genres for the source entity.

    Args:
        track_id: Spotify track ID
        artist_id: Spotify artist ID
        playlist_id: Spotify playlist ID

    Returns:
        List of genre strings

    Raises:
        ValueError: If no source provided
    """
    if track_id:
        # Get track and extract artist genres
        track_data = await make_spotify_request(f"tracks/{track_id}")
        return await get_track_genres(track_data)

    elif artist_id:
        # Get artist genres directly
        artist_data = await make_spotify_request(f"artists/{artist_id}")
        return artist_data.get("genres", [])

    elif playlist_id:
        # Get genres from all artists in playlist (first 20 tracks)
        data = await make_spotify_request(
            f"playlists/{playlist_id}/tracks", params={"limit": 20}
        )
        tracks = [item["track"] for item in data.get("items", []) if item.get("track")]

        all_genres = []
        for track in tracks:
            genres = await get_track_genres(track)
            all_genres.extend(genres)

        # Return unique genres
        return list(set(all_genres))

    raise ValueError(
        "At least one of track_id, artist_id, or playlist_id must be provided"
    )
