"""Similarity engine for audio-based track matching."""

from spotify_mcp.similarity.engine import (
    average_features,
    get_audio_features_for_tracks,
    get_candidate_tracks,
    get_source_features,
    get_source_genres,
    get_track_genres,
)
from spotify_mcp.similarity.strategies import (
    calculate_genre_similarity,
    calculate_similarity,
    normalize_audio_features,
)

__all__ = [
    "calculate_similarity",
    "calculate_genre_similarity",
    "normalize_audio_features",
    "get_audio_features_for_tracks",
    "get_candidate_tracks",
    "get_source_features",
    "get_source_genres",
    "get_track_genres",
    "average_features",
]
