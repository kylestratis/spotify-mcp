"""Type definitions and Pydantic models for Spotify MCP Server."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from spotify_mcp.similarity.engine import SearchScope
from spotify_mcp.similarity.strategies import FeatureWeights, SimilarityStrategy


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class SimilarityAction(str, Enum):
    """Action to take with similar tracks."""

    RETURN_TRACKS = "return_tracks"
    CREATE_PLAYLIST = "create_playlist"
    ADD_TO_PLAYLIST = "add_to_playlist"


class GetRecommendationsInput(BaseModel):
    """Input model for getting track recommendations."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    seed_tracks: list[str] | None = Field(
        default=None,
        description="List of Spotify track IDs to use as seeds (e.g., ['3n3Ppam7vgaVa1iaRUc9Lp'])",
        max_length=5,
    )
    seed_artists: list[str] | None = Field(
        default=None,
        description="List of Spotify artist IDs to use as seeds (e.g., ['4NHQUGzhtTLFvgF5SZesLK'])",
        max_length=5,
    )
    seed_genres: list[str] | None = Field(
        default=None,
        description="List of genre names to use as seeds (e.g., ['pop', 'rock'])",
        max_length=5,
    )
    limit: int | None = Field(
        default=20,
        description="Number of recommendations to return",
        ge=1,
        le=100,
    )
    min_energy: float | None = Field(
        default=None, description="Minimum energy (0.0-1.0)", ge=0.0, le=1.0
    )
    max_energy: float | None = Field(
        default=None, description="Maximum energy (0.0-1.0)", ge=0.0, le=1.0
    )
    target_energy: float | None = Field(
        default=None, description="Target energy (0.0-1.0)", ge=0.0, le=1.0
    )
    min_danceability: float | None = Field(
        default=None, description="Minimum danceability (0.0-1.0)", ge=0.0, le=1.0
    )
    max_danceability: float | None = Field(
        default=None, description="Maximum danceability (0.0-1.0)", ge=0.0, le=1.0
    )
    target_danceability: float | None = Field(
        default=None, description="Target danceability (0.0-1.0)", ge=0.0, le=1.0
    )
    min_valence: float | None = Field(
        default=None, description="Minimum valence/positivity (0.0-1.0)", ge=0.0, le=1.0
    )
    max_valence: float | None = Field(
        default=None, description="Maximum valence/positivity (0.0-1.0)", ge=0.0, le=1.0
    )
    target_valence: float | None = Field(
        default=None, description="Target valence/positivity (0.0-1.0)", ge=0.0, le=1.0
    )
    min_tempo: float | None = Field(
        default=None, description="Minimum tempo in BPM", ge=0.0
    )
    max_tempo: float | None = Field(
        default=None, description="Maximum tempo in BPM", ge=0.0
    )
    target_tempo: float | None = Field(
        default=None, description="Target tempo in BPM", ge=0.0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )

    @field_validator("seed_tracks", "seed_artists", "seed_genres")
    @classmethod
    def validate_seeds(cls, v: list[str] | None) -> list[str] | None:
        """Validate seed lists."""
        if v is not None and len(v) > 5:
            raise ValueError("Maximum 5 seeds allowed per type")
        return v


class CreatePlaylistInput(BaseModel):
    """Input model for creating a playlist."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name: str = Field(
        ..., description="Name of the playlist", min_length=1, max_length=100
    )
    description: str | None = Field(
        default=None, description="Description of the playlist", max_length=300
    )
    public: bool = Field(
        default=True, description="Whether the playlist should be public"
    )
    collaborative: bool = Field(
        default=False,
        description="Whether others can modify the playlist (cannot be true if public is true)",
    )


class AddTracksToPlaylistInput(BaseModel):
    """Input model for adding tracks to a playlist."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    playlist_id: str = Field(
        ..., description="Spotify playlist ID", min_length=1, max_length=100
    )
    track_uris: list[str] = Field(
        ...,
        description="List of Spotify track URIs to add (e.g., ['spotify:track:4iV5W9uYEdYUVa79Axb7Rh'])",
        min_length=1,
        max_length=100,
    )
    position: int | None = Field(
        default=None, description="Position to insert tracks (0-indexed)", ge=0
    )


class GetUserPlaylistsInput(BaseModel):
    """Input model for getting user playlists."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    limit: int | None = Field(
        default=20, description="Number of playlists to return", ge=1, le=50
    )
    offset: int | None = Field(default=0, description="Offset for pagination", ge=0)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetPlaylistTracksInput(BaseModel):
    """Input model for getting playlist tracks."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    playlist_id: str = Field(
        ..., description="Spotify playlist ID", min_length=1, max_length=100
    )
    limit: int | None = Field(
        default=20, description="Number of tracks to return", ge=1, le=50
    )
    offset: int | None = Field(default=0, description="Offset for pagination", ge=0)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class SearchTracksInput(BaseModel):
    """Input model for searching tracks."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: str = Field(
        ..., description="Search query for tracks", min_length=1, max_length=200
    )
    limit: int | None = Field(
        default=20, description="Number of results to return", ge=1, le=50
    )
    offset: int | None = Field(default=0, description="Offset for pagination", ge=0)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetTrackInput(BaseModel):
    """Input model for getting track details."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    track_id: str = Field(
        ..., description="Spotify track ID", min_length=1, max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetAudioFeaturesInput(BaseModel):
    """Input model for getting audio features."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    track_ids: list[str] = Field(
        ...,
        description="List of Spotify track IDs (1-100)",
        min_length=1,
        max_length=100,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'",
    )


class FindSimilarTracksInput(BaseModel):
    """Input model for finding similar tracks."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Source track/entity
    track_id: str | None = Field(
        default=None,
        description="Spotify track ID to find similar tracks for",
    )
    artist_id: str | None = Field(
        default=None,
        description="Spotify artist ID to analyze their style",
    )
    playlist_id: str | None = Field(
        default=None,
        description="Playlist ID to analyze (uses average features of first 20 tracks)",
    )

    # Similarity configuration
    strategy: SimilarityStrategy = Field(
        default=SimilarityStrategy.EUCLIDEAN,
        description=(
            "Similarity algorithm: 'euclidean' (overall similarity), "
            "'weighted' (custom feature weights), 'cosine' (angular similarity), "
            "'manhattan' (city-block distance), 'energy_match' (energy/danceability focus), "
            "'mood_match' (valence/acousticness focus), 'rhythm_match' (tempo/time_signature focus), "
            "'genre_match' (artist genre matching)"
        ),
    )
    weights: FeatureWeights | None = Field(
        default=None,
        description="Feature weights (only used with 'weighted' strategy)",
    )

    # Search scope
    scope: SearchScope = Field(
        default=SearchScope.CATALOG,
        description=(
            "Search scope: 'catalog' (recommendations API), 'playlist' (within playlist), "
            "'artist' (artist's tracks), 'album' (within album), 'saved_tracks' (user's library)"
        ),
    )
    scope_id: str | None = Field(
        default=None,
        description="ID for scope (playlist_id, artist_id, or album_id) - required for non-catalog scopes",
    )

    # Result configuration
    limit: int = Field(
        default=20,
        description="Number of similar tracks to return",
        ge=1,
        le=100,
    )
    min_similarity: float | None = Field(
        default=None,
        description="Minimum similarity score (0.0-1.0, lower = more similar for distance metrics)",
        ge=0.0,
        le=1.0,
    )

    # Action configuration
    action: SimilarityAction = Field(
        default=SimilarityAction.RETURN_TRACKS,
        description=(
            "Action: 'return_tracks' (just return list), 'create_playlist' (create new playlist), "
            "'add_to_playlist' (add to existing playlist)"
        ),
    )
    playlist_name: str | None = Field(
        default=None,
        description="Playlist name (required for 'create_playlist' action)",
    )
    target_playlist_id: str | None = Field(
        default=None,
        description="Target playlist ID (required for 'add_to_playlist' action)",
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )

    @field_validator("track_id", "artist_id", "playlist_id")
    @classmethod
    def validate_source(cls, v: str | None, info) -> str | None:
        """Validate at least one source is provided."""
        return v
