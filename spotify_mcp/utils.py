"""Shared utility functions for Spotify MCP Server."""

import os
from typing import Any

import httpx

# Constants
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
CHARACTER_LIMIT = 25000  # Maximum response size in characters


def get_access_token() -> str:
    """Get Spotify access token from environment variable."""
    token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "SPOTIFY_ACCESS_TOKEN not found in environment variables. "
            "Please set it in your .env file or environment."
        )
    return token


async def make_spotify_request(
    endpoint: str, method: str = "GET", **kwargs: Any
) -> dict[str, Any]:
    """Reusable function for all Spotify API calls.

    Args:
        endpoint: API endpoint path (without base URL)
        method: HTTP method (GET, POST, etc.)
        **kwargs: Additional arguments for httpx.request

    Returns:
        JSON response as dictionary

    Raises:
        httpx.HTTPStatusError: If request fails
    """
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{SPOTIFY_API_BASE_URL}/{endpoint}",
            headers=headers,
            timeout=30.0,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()


def handle_spotify_error(e: Exception) -> str:
    """Consistent error formatting across all tools.

    Args:
        e: Exception to format

    Returns:
        User-friendly error message
    """
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 401:
            return (
                "Error: Authentication failed. Please check your SPOTIFY_ACCESS_TOKEN "
                "is valid and not expired. You may need to refresh your token."
            )
        elif e.response.status_code == 403:
            return (
                "Error: Permission denied. Ensure your access token has the required "
                "scopes: playlist-modify-public, playlist-modify-private, playlist-read-private."
            )
        elif e.response.status_code == 404:
            return "Error: Resource not found. Please check the ID is correct."
        elif e.response.status_code == 429:
            return (
                "Error: Rate limit exceeded. Please wait before making more requests."
            )
        return f"Error: Spotify API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, ValueError):
        return f"Error: {str(e)}"
    return f"Error: Unexpected error occurred: {type(e).__name__} - {str(e)}"


def format_track_markdown(track: dict[str, Any]) -> str:
    """Format a track as Markdown.

    Args:
        track: Track object from Spotify API

    Returns:
        Markdown-formatted track information
    """
    artists = ", ".join([artist["name"] for artist in track.get("artists", [])])
    album = track.get("album", {}).get("name", "Unknown Album")
    duration_ms = track.get("duration_ms", 0)
    duration_min = duration_ms // 60000
    duration_sec = (duration_ms % 60000) // 1000

    lines = [
        f"**{track['name']}**",
        f"- Artists: {artists}",
        f"- Album: {album}",
        f"- Duration: {duration_min}:{duration_sec:02d}",
        f"- Spotify ID: `{track['id']}`",
        f"- URI: `{track['uri']}`",
    ]

    if track.get("popularity") is not None:
        lines.append(f"- Popularity: {track['popularity']}/100")

    return "\n".join(lines)


def check_character_limit(content: str, data_list: list[Any]) -> str:
    """Check character limit and return truncation message if needed.

    DEPRECATED: Use truncate_response_if_needed instead for actual truncation.

    Args:
        content: Content to check
        data_list: List of data items for calculating truncation

    Returns:
        Truncation message or empty string
    """
    if len(content) > CHARACTER_LIMIT:
        truncated_count = max(1, len(data_list) // 2)
        return (
            f"[Response truncated from {len(data_list)} to {truncated_count} items "
            f"due to character limit. Use pagination parameters to see more results.]\n"
        )
    return ""


def truncate_list_response(
    items: list[Any],
    format_func: Any,
    max_chars: int = CHARACTER_LIMIT,
) -> tuple[list[Any], bool]:
    """Truncate a list of items to fit within character limit.

    Progressively reduces the number of items until the formatted response
    fits within the character limit.

    Args:
        items: List of items to format
        format_func: Function that takes the items list and returns formatted string
        max_chars: Maximum character limit (default: CHARACTER_LIMIT)

    Returns:
        tuple: (truncated_items_list, was_truncated)
    """
    if not items:
        return items, False

    # Try with full list first
    formatted = format_func(items)
    if len(formatted) <= max_chars:
        return items, False

    # Binary search for the right number of items
    left, right = 1, len(items)
    best_count = 1

    while left <= right:
        mid = (left + right) // 2
        test_items = items[:mid]
        test_formatted = format_func(test_items)

        if len(test_formatted) <= max_chars:
            best_count = mid
            left = mid + 1
        else:
            right = mid - 1

    return items[:best_count], True


def format_truncation_message(
    original_count: int, truncated_count: int, response_type: str = "items"
) -> str:
    """Generate a truncation message for responses that were truncated.

    Args:
        original_count: Original number of items
        truncated_count: Number of items after truncation
        response_type: Type of items (e.g., "items", "tracks", "playlists")

    Returns:
        Formatted truncation message
    """
    return (
        f"\n\n[Response truncated from {original_count} to {truncated_count} {response_type} "
        f"due to {CHARACTER_LIMIT:,} character limit. Use 'offset' and 'limit' parameters "
        f"or add filters to see more results.]"
    )


async def create_playlist_helper(
    name: str,
    description: str | None = None,
    public: bool = True,
    collaborative: bool = False,
) -> dict[str, Any]:
    """Create a new Spotify playlist for the authenticated user.

    Args:
        name: Name of the playlist
        description: Optional description of the playlist
        public: Whether the playlist should be public
        collaborative: Whether others can modify the playlist

    Returns:
        Playlist data from Spotify API

    Raises:
        ValueError: If collaborative and public are both True
        httpx.HTTPStatusError: If the API request fails
    """
    if collaborative and public:
        raise ValueError("A playlist cannot be both collaborative and public")

    # Get current user ID
    user_data = await make_spotify_request("me")
    user_id = user_data["id"]

    # Create playlist
    payload = {
        "name": name,
        "public": public,
        "collaborative": collaborative,
    }
    if description:
        payload["description"] = description

    playlist_data = await make_spotify_request(
        f"users/{user_id}/playlists", method="POST", json=payload
    )

    return playlist_data


async def add_tracks_to_playlist_helper(
    playlist_id: str,
    track_uris: list[str],
    position: int | None = None,
) -> dict[str, Any]:
    """Add tracks to an existing Spotify playlist.

    Args:
        playlist_id: Spotify playlist ID
        track_uris: List of Spotify track URIs to add
        position: Optional position to insert tracks (0-indexed)

    Returns:
        Response data from Spotify API (includes snapshot_id)

    Raises:
        httpx.HTTPStatusError: If the API request fails
    """
    payload: dict = {"uris": track_uris}
    if position is not None:
        payload["position"] = position

    data = await make_spotify_request(
        f"playlists/{playlist_id}/tracks", method="POST", json=payload
    )

    return data
