#!/usr/bin/env python3
"""
MCP Server for Spotify Web API.

This server provides tools to interact with Spotify's Web API, including
playlist management, track search, music recommendations, and audio-based
similarity analysis for finding sonically similar tracks.
"""

import json

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Import from local packages
from spotify_mcp.similarity import (
    calculate_genre_similarity,
    calculate_similarity,
    get_audio_features_for_tracks,
    get_candidate_tracks,
    get_source_features,
    get_source_genres,
    get_track_genres,
)
from spotify_mcp.similarity.engine import SearchScope
from spotify_mcp.similarity.strategies import SimilarityStrategy
from spotify_mcp.types import (
    AddTracksToPlaylistInput,
    CreatePlaylistInput,
    FindSimilarTracksInput,
    GetAudioFeaturesInput,
    GetPlaylistTracksInput,
    GetRecommendationsInput,
    GetTrackInput,
    GetUserPlaylistsInput,
    ResponseFormat,
    SearchTracksInput,
    SimilarityAction,
)
from spotify_mcp.utils import (
    add_tracks_to_playlist_helper,
    check_character_limit,
    create_playlist_helper,
    format_track_markdown,
    handle_spotify_error,
    make_spotify_request,
)

# Load environment variables
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("spotify_mcp")


# Tool definitions
@mcp.tool(
    name="spotify_get_recommendations",
    annotations={
        "title": "Get Spotify Track Recommendations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def spotify_get_recommendations(params: GetRecommendationsInput) -> str:
    """Get track recommendations from Spotify based on seed tracks, artists, or genres.

    Generates personalized recommendations using up to 5 seeds (any combination) with
    tunable audio features (energy, danceability, valence, tempo).

    Args:
        - seed_tracks/seed_artists/seed_genres: Up to 5 total seeds (track IDs, artist IDs, or genre names)
        - limit: Results to return, 1-100 (default: 20)
        - min/max/target audio features: Energy, danceability, valence (0.0-1.0), tempo (BPM)
        - response_format: 'markdown' (formatted) or 'json' (structured data)

    Returns:
        Markdown: Numbered list with track details (name, artists, album, duration, ID, popularity)
        JSON: {"total": N, "tracks": [{id, name, artists, album, duration_ms, popularity, uri, external_urls}]}

    Examples:
        - "Find energetic workout music" -> seed_genres=['electronic'], target_energy=0.9
        - "Songs like this track" -> seed_tracks=['track_id']
        - "Happy danceable songs" -> target_valence=0.8, target_danceability=0.8

    Errors: Returns error for no seeds, >5 seeds, auth failure (401), rate limits (429), or no results.
    """
    try:
        # Validate at least one seed is provided
        total_seeds = (
            len(params.seed_tracks or [])
            + len(params.seed_artists or [])
            + len(params.seed_genres or [])
        )
        if total_seeds == 0:
            return (
                "Error: At least one seed (track, artist, or genre) must be provided."
            )
        if total_seeds > 5:
            return "Error: Maximum of 5 seeds total allowed across all seed types."

        # Build query parameters
        query_params: dict = {"limit": params.limit}

        if params.seed_tracks:
            query_params["seed_tracks"] = ",".join(params.seed_tracks)
        if params.seed_artists:
            query_params["seed_artists"] = ",".join(params.seed_artists)
        if params.seed_genres:
            query_params["seed_genres"] = ",".join(params.seed_genres)

        # Add tunable attributes
        for attr in [
            "min_energy",
            "max_energy",
            "target_energy",
            "min_danceability",
            "max_danceability",
            "target_danceability",
            "min_valence",
            "max_valence",
            "target_valence",
            "min_tempo",
            "max_tempo",
            "target_tempo",
        ]:
            value = getattr(params, attr)
            if value is not None:
                query_params[attr] = value

        # Make API request
        data = await make_spotify_request("recommendations", params=query_params)

        tracks = data.get("tracks", [])

        if not tracks:
            return "No recommendations found for the provided seeds and parameters."

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Spotify Track Recommendations\n"]

            for i, track in enumerate(tracks, 1):
                lines.append(f"## {i}. {format_track_markdown(track)}\n")

            result = "\n".join(lines)
            truncation_msg = check_character_limit(result, tracks)
            if truncation_msg:
                tracks = tracks[: len(tracks) // 2]
                lines = ["# Spotify Track Recommendations\n", truncation_msg]
                for i, track in enumerate(tracks, 1):
                    lines.append(f"## {i}. {format_track_markdown(track)}\n")
                result = "\n".join(lines)

            return result
        else:
            # JSON format
            return json.dumps(
                {"total": len(tracks), "tracks": tracks},
                indent=2,
            )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_create_playlist",
    annotations={
        "title": "Create Spotify Playlist",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def spotify_create_playlist(params: CreatePlaylistInput) -> str:
    """Create a new empty Spotify playlist for the authenticated user.

    Creates an empty playlist in the user's library. Use spotify_add_tracks_to_playlist
    to add tracks after creation.

    Args:
        - name: Playlist name, 1-100 characters
        - description: Optional description, max 300 characters
        - public: Whether playlist is public (default: True)
        - collaborative: Whether others can modify (default: False, cannot be True if public is True)

    Returns:
        JSON: {"success": true, "playlist_id": "...", "name": "...", "url": "...", "message": "..."}

    Examples:
        - "Create a new workout playlist" -> name="Workout Mix"
        - "Make a private playlist" -> name="My Mix", public=False
        - "Create collaborative playlist" -> collaborative=True, public=False

    Errors: Returns error for collaborative+public, auth failure (401), missing scopes (403), rate limits (429).
    """
    try:
        data = await create_playlist_helper(
            name=params.name,
            description=params.description,
            public=params.public,
            collaborative=params.collaborative,
        )

        return json.dumps(
            {
                "success": True,
                "playlist_id": data["id"],
                "name": data["name"],
                "url": data["external_urls"]["spotify"],
                "message": f"Successfully created playlist '{data['name']}'",
            },
            indent=2,
        )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_add_tracks_to_playlist",
    annotations={
        "title": "Add Tracks to Spotify Playlist",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def spotify_add_tracks_to_playlist(params: AddTracksToPlaylistInput) -> str:
    """Add tracks to an existing Spotify playlist.

    Adds 1-100 tracks to a playlist. Tracks can be inserted at a specific position or
    appended to the end. Playlist must be owned by user or be collaborative.

    Args:
        - playlist_id: Spotify playlist ID (not URI)
        - track_uris: List of track URIs, 1-100 (format: "spotify:track:ID", not just IDs)
        - position: Optional 0-indexed position to insert (default: append to end)

    Returns:
        JSON: {"success": true, "snapshot_id": "...", "tracks_added": N, "message": "..."}

    Examples:
        - "Add this track to my playlist" -> track_uris=["spotify:track:ID"], playlist_id="..."
        - "Add 10 songs to workout mix" -> track_uris=[list of URIs]
        - "Insert at the beginning" -> position=0

    Errors: Returns error for invalid playlist (404), no permission (403), auth failure (401), rate limits (429).
    """
    try:
        data = await add_tracks_to_playlist_helper(
            playlist_id=params.playlist_id,
            track_uris=params.track_uris,
            position=params.position,
        )

        return json.dumps(
            {
                "success": True,
                "snapshot_id": data.get("snapshot_id"),
                "tracks_added": len(params.track_uris),
                "message": f"Successfully added {len(params.track_uris)} track(s) to playlist",
            },
            indent=2,
        )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_get_user_playlists",
    annotations={
        "title": "Get User's Spotify Playlists",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def spotify_get_user_playlists(params: GetUserPlaylistsInput) -> str:
    """Get a list of the current user's Spotify playlists.

    Retrieves all playlists owned by or followed by the authenticated user. Results are
    paginated. Use to browse playlists or find playlist IDs.

    Args:
        - limit: Number of playlists to return, 1-50 (default: 20)
        - offset: Starting position for pagination (default: 0)
        - response_format: 'markdown' or 'json'

    Returns:
        Markdown: List with playlist name, ID, track count, public status, description, URL
        JSON: {"total": N, "count": N, "offset": N, "playlists": [{id, name, description, public, collaborative, tracks, owner, external_urls}], "has_more": bool}

    Examples:
        - "Show me my playlists" -> List all user playlists
        - "Find my workout playlist" -> Browse to find specific one
        - Need playlist ID -> Get ID from the list

    Errors: Returns "No playlists found." if none exist, or error for auth failure (401), missing scopes (403), rate limits (429).
    """
    try:
        query_params = {"limit": params.limit, "offset": params.offset}

        data = await make_spotify_request("me/playlists", params=query_params)

        playlists = data.get("items", [])
        total = data.get("total", 0)

        if not playlists:
            return "No playlists found."

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                "# Your Spotify Playlists\n",
                f"Showing {len(playlists)} of {total} playlists\n",
            ]

            for playlist in playlists:
                lines.append(f"## {playlist['name']}")
                lines.append(f"- Playlist ID: `{playlist['id']}`")
                lines.append(f"- Tracks: {playlist.get('tracks', {}).get('total', 0)}")
                lines.append(f"- Public: {playlist.get('public', False)}")
                if playlist.get("description"):
                    lines.append(f"- Description: {playlist['description']}")
                lines.append(f"- URL: {playlist['external_urls']['spotify']}\n")

            has_more = total > params.offset + len(playlists)
            if has_more:
                next_offset = params.offset + len(playlists)
                lines.append(
                    f"\n*More playlists available. Use offset={next_offset} to see more.*"
                )

            return "\n".join(lines)
        else:
            # JSON format
            return json.dumps(
                {
                    "total": total,
                    "count": len(playlists),
                    "offset": params.offset,
                    "playlists": playlists,
                    "has_more": total > params.offset + len(playlists),
                },
                indent=2,
            )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_get_playlist_tracks",
    annotations={
        "title": "Get Tracks from Spotify Playlist",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def spotify_get_playlist_tracks(params: GetPlaylistTracksInput) -> str:
    """Get tracks from a specific Spotify playlist.

    Retrieves tracks from a playlist with detailed information (artists, album, duration, IDs).
    Results are paginated for large playlists.

    Args:
        - playlist_id: Spotify playlist ID (get from spotify_get_user_playlists or playlist URL)
        - limit: Number of tracks to return, 1-50 (default: 20)
        - offset: Starting position for pagination (default: 0)
        - response_format: 'markdown' or 'json'

    Returns:
        Markdown: Numbered list with track details (name, artists, album, duration, ID, URI, popularity)
        JSON: {"total": N, "count": N, "offset": N, "tracks": [{id, name, artists, album, duration_ms, popularity, uri, external_urls}], "has_more": bool}

    Examples:
        - "Show me what's in my workout playlist" -> View playlist contents
        - "Get track IDs from this playlist" -> Extract IDs for operations

    Errors: Returns "No tracks found" if empty, or error for invalid playlist (404), auth failure (401), rate limits (429).
    """
    try:
        query_params = {"limit": params.limit, "offset": params.offset}

        data = await make_spotify_request(
            f"playlists/{params.playlist_id}/tracks", params=query_params
        )

        items = data.get("items", [])
        total = data.get("total", 0)

        if not items:
            return "No tracks found in this playlist."

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Playlist Tracks\n", f"Showing {len(items)} of {total} tracks\n"]

            for i, item in enumerate(items, 1):
                track = item.get("track")
                if track:
                    lines.append(f"## {i}. {format_track_markdown(track)}\n")

            has_more = total > params.offset + len(items)
            if has_more:
                next_offset = params.offset + len(items)
                lines.append(
                    f"\n*More tracks available. Use offset={next_offset} to see more.*"
                )

            return "\n".join(lines)
        else:
            # JSON format
            tracks = [item.get("track") for item in items if item.get("track")]
            return json.dumps(
                {
                    "total": total,
                    "count": len(tracks),
                    "offset": params.offset,
                    "tracks": tracks,
                    "has_more": total > params.offset + len(items),
                },
                indent=2,
            )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_search_tracks",
    annotations={
        "title": "Search Spotify Tracks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def spotify_search_tracks(params: SearchTracksInput) -> str:
    """Search for tracks on Spotify by name, artist, album, or keywords.

    Searches Spotify's entire catalog using intelligent matching. Results ranked by relevance.

    Args:
        - query: Search text, 1-200 chars (e.g., "Bohemian Rhapsody", "artist:Queen", "album:...", or keywords)
        - limit: Results to return, 1-50 (default: 20)
        - offset: Starting position for pagination (default: 0)
        - response_format: 'markdown' or 'json'

    Returns:
        Markdown: Search results with track details (name, artists, album, duration, ID, URI, popularity)
        JSON: {"total": N, "count": N, "offset": N, "tracks": [{id, name, artists, album, duration_ms, popularity, uri, external_urls}], "has_more": bool}

    Examples:
        - "Find Bohemian Rhapsody by Queen" -> query="Bohemian Rhapsody Queen"
        - "Search for songs by Taylor Swift" -> query="artist:Taylor Swift"
        - "Look for indie rock songs" -> query="indie rock"

    Errors: Returns "No tracks found" if no results, or error for auth failure (401), rate limits (429). Truncates if exceeds character limit.
    """
    try:
        query_params = {
            "q": params.query,
            "type": "track",
            "limit": params.limit,
            "offset": params.offset,
        }

        data = await make_spotify_request("search", params=query_params)

        tracks = data.get("tracks", {}).get("items", [])
        total = data.get("tracks", {}).get("total", 0)

        if not tracks:
            return f"No tracks found matching '{params.query}'"

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                f"# Search Results: '{params.query}'\n",
                f"Found {total} tracks (showing {len(tracks)})\n",
            ]

            for i, track in enumerate(tracks, 1):
                lines.append(f"## {i}. {format_track_markdown(track)}\n")

            has_more = total > params.offset + len(tracks)
            if has_more:
                next_offset = params.offset + len(tracks)
                lines.append(
                    f"\n*More results available. Use offset={next_offset} to see more.*"
                )

            result = "\n".join(lines)
            truncation_msg = check_character_limit(result, tracks)
            if truncation_msg:
                tracks = tracks[: len(tracks) // 2]
                lines = [
                    f"# Search Results: '{params.query}'\n",
                    truncation_msg,
                    f"Found {total} tracks (showing {len(tracks)})\n",
                ]
                for i, track in enumerate(tracks, 1):
                    lines.append(f"## {i}. {format_track_markdown(track)}\n")
                result = "\n".join(lines)

            return result
        else:
            # JSON format
            return json.dumps(
                {
                    "total": total,
                    "count": len(tracks),
                    "offset": params.offset,
                    "tracks": tracks,
                    "has_more": total > params.offset + len(tracks),
                },
                indent=2,
            )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_get_track",
    annotations={
        "title": "Get Spotify Track Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def spotify_get_track(params: GetTrackInput) -> str:
    """Get detailed information about a specific Spotify track by ID.

    Retrieves comprehensive metadata for a single track including artists, album, duration,
    popularity, URIs, and external URLs.

    Args:
        - track_id: Spotify track ID (not URI), extract from URIs or search results
        - response_format: 'markdown' or 'json'

    Returns:
        Markdown: Track details (name, artists, album, duration, ID, URI, popularity)
        JSON: Full API response (id, name, artists, album, duration_ms, popularity, uri, external_urls, preview_url, track_number, disc_number, explicit, available_markets)

    Examples:
        - "Get details for track ID 4u7EnebtmKWzUH433cf5Qv" -> Retrieve track info
        - "Show me info about this track" -> When you have the track ID

    Errors: Returns error for invalid track (404), auth failure (401), rate limits (429).
    """
    try:
        data = await make_spotify_request(f"tracks/{params.track_id}")

        if params.response_format == ResponseFormat.MARKDOWN:
            return f"# Track Details\n\n{format_track_markdown(data)}"
        else:
            # JSON format
            return json.dumps(data, indent=2)

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_get_audio_features",
    annotations={
        "title": "Get Spotify Audio Features",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def spotify_get_audio_features(params: GetAudioFeaturesInput) -> str:
    """Get detailed audio analysis features for one or more Spotify tracks.

    Retrieves sonic characteristics (energy, tempo, danceability, valence, acousticness, etc.)
    that power the similarity engine. Supports batch processing of up to 100 tracks.

    Args:
        - track_ids: List of Spotify track IDs, 1-100 tracks
        - response_format: 'markdown' or 'json' (default: JSON)

    Returns:
        Markdown: Per-track audio features (acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, valence, tempo, key, mode, time_signature)
        JSON: {"track_count": N, "features": [{id, acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, valence, tempo, key, mode, time_signature, duration_ms, analysis_url, track_href, type, uri}]}

    Examples:
        - "Analyze the audio features of this track" -> Get sonic characteristics
        - "What's the tempo and energy of these songs?" -> Extract specific features

    Errors: Returns "No audio features available" if not found, or error for auth failure (401), rate limits (429). Note: Audio features endpoint deprecated for NEW apps (Nov 2024), but existing apps with extended mode access can still use it.
    """
    try:
        features_map = await get_audio_features_for_tracks(params.track_ids)

        if not features_map:
            return "No audio features available for the provided track IDs."

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Audio Features\n"]

            for track_id, features in features_map.items():
                lines.append(f"## Track: {track_id}")
                lines.append(
                    f"- **Acousticness**: {features.get('acousticness', 0):.3f}"
                )
                lines.append(
                    f"- **Danceability**: {features.get('danceability', 0):.3f}"
                )
                lines.append(f"- **Energy**: {features.get('energy', 0):.3f}")
                lines.append(
                    f"- **Instrumentalness**: {features.get('instrumentalness', 0):.3f}"
                )
                lines.append(f"- **Liveness**: {features.get('liveness', 0):.3f}")
                lines.append(f"- **Loudness**: {features.get('loudness', 0):.1f} dB")
                lines.append(f"- **Speechiness**: {features.get('speechiness', 0):.3f}")
                lines.append(f"- **Valence**: {features.get('valence', 0):.3f}")
                lines.append(f"- **Tempo**: {features.get('tempo', 0):.1f} BPM")
                lines.append(f"- **Key**: {features.get('key', -1)}")
                lines.append(
                    f"- **Mode**: {'Major' if features.get('mode') == 1 else 'Minor'}"
                )
                lines.append(
                    f"- **Time Signature**: {features.get('time_signature', 4)}/4\n"
                )

            return "\n".join(lines)
        else:
            # JSON format
            return json.dumps(
                {
                    "track_count": len(features_map),
                    "features": list(features_map.values()),
                },
                indent=2,
            )

    except Exception as e:
        return handle_spotify_error(e)


@mcp.tool(
    name="spotify_find_similar_tracks",
    annotations={
        "title": "Find Similar Tracks Using Audio Features",
        "readOnlyHint": False,  # Can create playlists
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def spotify_find_similar_tracks(params: FindSimilarTracksInput) -> str:
    """Find tracks similar to a track, artist, or playlist using audio analysis or genre matching.

    Centerpiece of the similarity engine. Supports 8 strategies, custom weighting, and automated
    playlist creation. For curated playlists, music discovery, and mood-based mixes.

    Args:
        Source (one required): track_id, artist_id, or playlist_id

        Strategy (default: euclidean): euclidean, weighted (needs weights), cosine, manhattan,
        energy_match (workout), mood_match (relaxation), rhythm_match (running), genre_match (non-catalog scope only)

        Scope (default: catalog): catalog (recommendations API), playlist (needs scope_id),
        artist (needs scope_id), album (needs scope_id), saved_tracks

        Action (default: return_tracks): return_tracks, create_playlist (needs playlist_name),
        add_to_playlist (needs target_playlist_id)

        - limit: Results to return, 1-100 (default: 20)
        - min_similarity: Optional threshold, 0.0-1.0
        - weights: Optional custom weights for 'weighted' strategy (e.g., {"energy": 5.0, "danceability": 5.0})
        - response_format: 'markdown' or 'json'

    Returns:
        return_tracks: List with similarity scores (Markdown or JSON: {"strategy": "...", "scope": "...", "count": N, "tracks": [{track, similarity}]})
        create_playlist: {"success": true, "action": "create_playlist", "playlist_id": "...", "playlist_name": "...", "playlist_url": "...", "tracks_added": N, "message": "..."}
        add_to_playlist: {"success": true, "action": "add_to_playlist", "playlist_id": "...", "tracks_added": N, "message": "..."}

    Examples:
        - "Find songs similar to this track" -> track_id, catalog scope
        - "Create workout playlist like this" -> track_id, energy_match, create_playlist
        - "Filter playlist by genre" -> track_id, genre_match, playlist scope
        - "Custom similarity for energy/dance" -> weighted strategy, custom weights

    Errors: Returns errors for missing source, missing scope_id, missing action params, genre_match with catalog, no genres, no matches, auth (401), permissions (403), rate limits (429).
    """
    try:
        # Validate source
        if not params.track_id and not params.artist_id and not params.playlist_id:
            return "Error: At least one of track_id, artist_id, or playlist_id must be provided."

        # Validate scope_id for non-catalog scopes
        if params.scope != SearchScope.CATALOG and not params.scope_id:
            return f"Error: scope_id is required for scope '{params.scope.value}'"

        # Validate action parameters
        if (
            params.action == SimilarityAction.CREATE_PLAYLIST
            and not params.playlist_name
        ):
            return "Error: playlist_name is required for 'create_playlist' action"
        if (
            params.action == SimilarityAction.ADD_TO_PLAYLIST
            and not params.target_playlist_id
        ):
            return "Error: target_playlist_id is required for 'add_to_playlist' action"

        similar_tracks = []

        # Handle GENRE_MATCH strategy separately (uses artist genres instead of audio features)
        if params.strategy == SimilarityStrategy.GENRE_MATCH:
            # Genre matching requires a specific scope (not catalog)
            if params.scope == SearchScope.CATALOG:
                return "Error: GENRE_MATCH strategy requires a specific scope (playlist, artist, album, or saved_tracks), not catalog"

            # Get source genres
            source_genres = await get_source_genres(
                params.track_id, params.artist_id, params.playlist_id
            )

            if not source_genres:
                return "Error: No genres found for the source track/artist/playlist"

            # Get candidate tracks from specified scope
            candidate_tracks = await get_candidate_tracks(
                params.scope, params.scope_id, limit=500
            )

            # Calculate genre similarity for each track
            for track in candidate_tracks:
                # Get genres for this track
                target_genres = await get_track_genres(track)

                if target_genres:
                    similarity = calculate_genre_similarity(
                        source_genres, target_genres
                    )

                    # Apply minimum similarity filter
                    if (
                        params.min_similarity is None
                        or similarity >= params.min_similarity
                    ):
                        similar_tracks.append(
                            {
                                "track": track,
                                "similarity": similarity,
                                "genres": target_genres,
                            }
                        )

        else:
            # Audio feature-based matching
            # Get source audio features
            source_features = await get_source_features(
                params.track_id, params.artist_id, params.playlist_id
            )

            if params.scope == SearchScope.CATALOG:
                # Use recommendations API for catalog search
                seed_params = {}
                if params.track_id:
                    seed_params["seed_tracks"] = params.track_id
                elif params.artist_id:
                    seed_params["seed_artists"] = params.artist_id

                # Use source features as targets for recommendations
                seed_params["limit"] = params.limit
                seed_params["target_acousticness"] = source_features.get("acousticness")
                seed_params["target_danceability"] = source_features.get("danceability")
                seed_params["target_energy"] = source_features.get("energy")
                seed_params["target_instrumentalness"] = source_features.get(
                    "instrumentalness"
                )
                seed_params["target_valence"] = source_features.get("valence")
                seed_params["target_tempo"] = source_features.get("tempo")

                data = await make_spotify_request("recommendations", params=seed_params)
                candidate_tracks = data.get("tracks", [])

            else:
                # Get candidate tracks from specified scope
                candidate_tracks = await get_candidate_tracks(
                    params.scope, params.scope_id, limit=500
                )

            # Get audio features for candidate tracks
            candidate_ids = [track["id"] for track in candidate_tracks]
            features_map = await get_audio_features_for_tracks(candidate_ids)

            # Calculate similarity scores
            for track in candidate_tracks:
                track_id = track["id"]
                if track_id in features_map:
                    target_features = features_map[track_id]
                    similarity = calculate_similarity(
                        source_features,
                        target_features,
                        params.strategy,
                        params.weights,
                    )

                    # Apply minimum similarity filter
                    if (
                        params.min_similarity is None
                        or similarity >= params.min_similarity
                    ):
                        similar_tracks.append(
                            {
                                "track": track,
                                "similarity": similarity,
                                "features": target_features,
                            }
                        )

        # Sort by similarity (descending for similarity scores)
        similar_tracks.sort(key=lambda x: x["similarity"], reverse=True)

        # Limit results
        similar_tracks = similar_tracks[: params.limit]

        if not similar_tracks:
            return "No similar tracks found matching the criteria."

        # Execute action
        if params.action == SimilarityAction.CREATE_PLAYLIST:
            # Create new playlist with similar tracks
            playlist_data = await create_playlist_helper(
                name=params.playlist_name,
                description=f"Similar tracks found using {params.strategy.value} strategy",
                public=False,
            )

            # Add tracks to playlist
            track_uris = [item["track"]["uri"] for item in similar_tracks]
            await add_tracks_to_playlist_helper(
                playlist_id=playlist_data["id"],
                track_uris=track_uris,
            )

            return json.dumps(
                {
                    "success": True,
                    "action": "create_playlist",
                    "playlist_id": playlist_data["id"],
                    "playlist_name": playlist_data["name"],
                    "playlist_url": playlist_data["external_urls"]["spotify"],
                    "tracks_added": len(track_uris),
                    "message": f"Created playlist '{params.playlist_name}' with {len(track_uris)} similar tracks",
                },
                indent=2,
            )

        elif params.action == SimilarityAction.ADD_TO_PLAYLIST:
            # Add tracks to existing playlist
            track_uris = [item["track"]["uri"] for item in similar_tracks]
            await add_tracks_to_playlist_helper(
                playlist_id=params.target_playlist_id,
                track_uris=track_uris,
            )

            return json.dumps(
                {
                    "success": True,
                    "action": "add_to_playlist",
                    "playlist_id": params.target_playlist_id,
                    "tracks_added": len(track_uris),
                    "message": f"Added {len(track_uris)} similar tracks to playlist",
                },
                indent=2,
            )

        else:
            # Return tracks
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# Similar Tracks\n"]
                lines.append(f"Strategy: {params.strategy.value}")
                lines.append(f"Scope: {params.scope.value}")
                lines.append(f"Found {len(similar_tracks)} similar tracks\n")

                for i, item in enumerate(similar_tracks, 1):
                    track = item["track"]
                    similarity = item["similarity"]
                    lines.append(f"## {i}. {format_track_markdown(track)}")
                    lines.append(f"- **Similarity Score**: {similarity:.3f}\n")

                return "\n".join(lines)
            else:
                # JSON format
                return json.dumps(
                    {
                        "strategy": params.strategy.value,
                        "scope": params.scope.value,
                        "count": len(similar_tracks),
                        "tracks": [
                            {
                                "track": item["track"],
                                "similarity": item["similarity"],
                            }
                            for item in similar_tracks
                        ],
                    },
                    indent=2,
                )

    except Exception as e:
        return handle_spotify_error(e)


if __name__ == "__main__":
    mcp.run()
