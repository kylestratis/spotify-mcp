"""Similarity calculation strategies for audio features."""

import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SimilarityStrategy(str, Enum):
    """Algorithm for calculating track similarity."""

    EUCLIDEAN = "euclidean"
    WEIGHTED = "weighted"
    COSINE = "cosine"
    MANHATTAN = "manhattan"
    ENERGY_MATCH = "energy_match"
    MOOD_MATCH = "mood_match"
    RHYTHM_MATCH = "rhythm_match"
    GENRE_MATCH = "genre_match"


class FeatureWeights(BaseModel):
    """Weights for audio features in similarity calculation."""

    model_config = ConfigDict(validate_assignment=True)

    acousticness: float = Field(default=1.0, ge=0.0, le=10.0)
    danceability: float = Field(default=1.0, ge=0.0, le=10.0)
    energy: float = Field(default=1.0, ge=0.0, le=10.0)
    instrumentalness: float = Field(default=1.0, ge=0.0, le=10.0)
    liveness: float = Field(default=1.0, ge=0.0, le=10.0)
    loudness: float = Field(default=1.0, ge=0.0, le=10.0)
    speechiness: float = Field(default=1.0, ge=0.0, le=10.0)
    valence: float = Field(default=1.0, ge=0.0, le=10.0)
    tempo: float = Field(default=1.0, ge=0.0, le=10.0)


def normalize_audio_features(features: dict[str, Any]) -> dict[str, float]:
    """Normalize audio features to 0-1 range for similarity calculations.

    Args:
        features: Raw audio features from Spotify API

    Returns:
        Normalized features in 0-1 range
    """
    normalized = {}

    # Already in 0-1 range
    for key in [
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "speechiness",
        "valence",
    ]:
        normalized[key] = features.get(key, 0.0)

    # Normalize loudness (typically -60 to 0 dB)
    loudness = features.get("loudness", -30.0)
    normalized["loudness"] = (loudness + 60.0) / 60.0  # Map to 0-1

    # Normalize tempo (typically 50-200 BPM)
    tempo = features.get("tempo", 120.0)
    normalized["tempo"] = (tempo - 50.0) / 150.0  # Map to 0-1

    return normalized


def calculate_euclidean_distance(
    features1: dict[str, float],
    features2: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    """Calculate Euclidean distance between two feature sets.

    Args:
        features1: First feature set
        features2: Second feature set
        weights: Optional feature weights

    Returns:
        Euclidean distance
    """
    weights = weights or {}
    distance_squared = 0.0

    for key in features1.keys():
        if key in features2:
            weight = weights.get(key, 1.0)
            diff = features1[key] - features2[key]
            distance_squared += weight * (diff**2)

    return math.sqrt(distance_squared)


def calculate_cosine_similarity(
    features1: dict[str, float], features2: dict[str, float]
) -> float:
    """Calculate cosine similarity between two feature sets.

    Args:
        features1: First feature set
        features2: Second feature set

    Returns:
        Cosine similarity (0-1)
    """
    dot_product = sum(
        features1[k] * features2[k] for k in features1.keys() if k in features2
    )
    magnitude1 = math.sqrt(sum(v**2 for v in features1.values()))
    magnitude2 = math.sqrt(sum(v**2 for v in features2.values()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def calculate_manhattan_distance(
    features1: dict[str, float], features2: dict[str, float]
) -> float:
    """Calculate Manhattan distance between two feature sets.

    Args:
        features1: First feature set
        features2: Second feature set

    Returns:
        Manhattan distance
    """
    return sum(
        abs(features1[k] - features2[k]) for k in features1.keys() if k in features2
    )


def calculate_similarity(
    source_features: dict[str, float],
    target_features: dict[str, float],
    strategy: SimilarityStrategy,
    weights: FeatureWeights | None = None,
) -> float:
    """Calculate similarity score based on strategy.

    Args:
        source_features: Source track audio features
        target_features: Target track audio features
        strategy: Similarity algorithm to use
        weights: Optional feature weights (for weighted strategy)

    Returns:
        Similarity score (0-1, higher = more similar)
    """
    # Normalize features
    source_norm = normalize_audio_features(source_features)
    target_norm = normalize_audio_features(target_features)

    if strategy == SimilarityStrategy.EUCLIDEAN:
        # Lower distance = more similar, invert to 0-1 similarity score
        distance = calculate_euclidean_distance(source_norm, target_norm)
        return 1.0 / (1.0 + distance)

    elif strategy == SimilarityStrategy.WEIGHTED:
        # Use custom weights
        weight_dict = {}
        if weights:
            weight_dict = {
                "acousticness": weights.acousticness,
                "danceability": weights.danceability,
                "energy": weights.energy,
                "instrumentalness": weights.instrumentalness,
                "liveness": weights.liveness,
                "loudness": weights.loudness,
                "speechiness": weights.speechiness,
                "valence": weights.valence,
                "tempo": weights.tempo,
            }
        distance = calculate_euclidean_distance(source_norm, target_norm, weight_dict)
        return 1.0 / (1.0 + distance)

    elif strategy == SimilarityStrategy.COSINE:
        # Cosine similarity is already 0-1
        return calculate_cosine_similarity(source_norm, target_norm)

    elif strategy == SimilarityStrategy.MANHATTAN:
        # Lower distance = more similar
        distance = calculate_manhattan_distance(source_norm, target_norm)
        return 1.0 / (1.0 + distance)

    elif strategy == SimilarityStrategy.ENERGY_MATCH:
        # Focus on energy and danceability
        energy_diff = abs(source_features["energy"] - target_features["energy"])
        dance_diff = abs(
            source_features["danceability"] - target_features["danceability"]
        )
        return 1.0 - ((energy_diff + dance_diff) / 2.0)

    elif strategy == SimilarityStrategy.MOOD_MATCH:
        # Focus on valence and acousticness
        valence_diff = abs(source_features["valence"] - target_features["valence"])
        acoustic_diff = abs(
            source_features["acousticness"] - target_features["acousticness"]
        )
        return 1.0 - ((valence_diff + acoustic_diff) / 2.0)

    elif strategy == SimilarityStrategy.RHYTHM_MATCH:
        # Focus on tempo (normalize to percentage difference)
        tempo1 = source_features["tempo"]
        tempo2 = target_features["tempo"]
        tempo_diff = abs(tempo1 - tempo2) / max(tempo1, tempo2, 1.0)
        return 1.0 - min(tempo_diff, 1.0)

    elif strategy == SimilarityStrategy.GENRE_MATCH:
        # Genre matching is handled separately - this shouldn't be called
        raise ValueError(
            "GENRE_MATCH strategy requires genre data, not audio features. "
            "Use calculate_genre_similarity() instead."
        )

    return 0.0


def calculate_genre_similarity(
    source_genres: list[str], target_genres: list[str]
) -> float:
    """Calculate similarity based on genre overlap.

    Uses exact and partial matching with weighted scoring:
    - Exact genre match: 1.0 points
    - Partial match (substring): 0.5 points

    Args:
        source_genres: List of genre strings for source track/artist
        target_genres: List of genre strings for target track/artist

    Returns:
        Similarity score (0-1, higher = more similar)
    """
    if not source_genres or not target_genres:
        return 0.0

    # Normalize genres to lowercase for comparison
    source_lower = [g.lower() for g in source_genres]
    target_lower = [g.lower() for g in target_genres]

    total_score = 0.0
    max_possible_score = len(source_lower)

    for source_genre in source_lower:
        # Check for exact match
        if source_genre in target_lower:
            total_score += 1.0
        else:
            # Check for partial matches (substring)
            for target_genre in target_lower:
                if source_genre in target_genre or target_genre in source_genre:
                    total_score += 0.5
                    break  # Only count first partial match

    # Normalize to 0-1 range
    if max_possible_score > 0:
        return min(total_score / max_possible_score, 1.0)

    return 0.0
