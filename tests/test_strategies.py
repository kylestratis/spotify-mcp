"""Tests for spotify_mcp/similarity/strategies.py"""

import pytest

from spotify_mcp.similarity.strategies import (
    FeatureWeights,
    SimilarityStrategy,
    calculate_cosine_similarity,
    calculate_euclidean_distance,
    calculate_genre_similarity,
    calculate_manhattan_distance,
    calculate_similarity,
    normalize_audio_features,
)


class TestNormalizeAudioFeatures:
    """Tests for normalize_audio_features function."""

    def test_features_already_normalized(self, sample_audio_features):
        """Test features that are already in 0-1 range."""
        result = normalize_audio_features(sample_audio_features)

        # These should remain unchanged
        assert result["acousticness"] == sample_audio_features["acousticness"]
        assert result["danceability"] == sample_audio_features["danceability"]
        assert result["energy"] == sample_audio_features["energy"]
        assert result["instrumentalness"] == sample_audio_features["instrumentalness"]
        assert result["liveness"] == sample_audio_features["liveness"]
        assert result["speechiness"] == sample_audio_features["speechiness"]
        assert result["valence"] == sample_audio_features["valence"]

    def test_loudness_normalization(self):
        """Test loudness normalization from -60 to 0 dB."""
        test_cases = [
            (-60.0, 0.0),  # Minimum
            (0.0, 1.0),  # Maximum
            (-30.0, 0.5),  # Middle
            (-6.0, 0.9),  # Typical loud track
        ]

        for loudness, expected in test_cases:
            features = {"loudness": loudness}
            result = normalize_audio_features(features)
            assert abs(result["loudness"] - expected) < 0.01

    def test_tempo_normalization(self):
        """Test tempo normalization from 50 to 200 BPM."""
        test_cases = [
            (50.0, 0.0),  # Minimum
            (200.0, 1.0),  # Maximum
            (125.0, 0.5),  # Middle
            (120.0, 0.4667),  # Typical pop tempo
        ]

        for tempo, expected in test_cases:
            features = {"tempo": tempo}
            result = normalize_audio_features(features)
            assert abs(result["tempo"] - expected) < 0.01

    def test_missing_features(self):
        """Test handling of missing features."""
        features = {}
        result = normalize_audio_features(features)

        # Should use defaults
        assert result["acousticness"] == 0.0
        assert result["danceability"] == 0.0
        assert result["energy"] == 0.0
        assert "loudness" in result
        assert "tempo" in result


class TestCalculateEuclideanDistance:
    """Tests for calculate_euclidean_distance function."""

    def test_identical_features(self, sample_audio_features):
        """Test distance between identical feature sets."""
        normalized = normalize_audio_features(sample_audio_features)
        distance = calculate_euclidean_distance(normalized, normalized)

        assert distance == 0.0

    def test_different_features(self):
        """Test distance between different feature sets."""
        features1 = {"a": 0.0, "b": 0.0}
        features2 = {"a": 1.0, "b": 1.0}
        distance = calculate_euclidean_distance(features1, features2)

        # Distance should be sqrt(1^2 + 1^2) = sqrt(2) ≈ 1.414
        assert abs(distance - 1.414) < 0.01

    def test_with_weights(self):
        """Test weighted Euclidean distance."""
        features1 = {"a": 0.0, "b": 0.0}
        features2 = {"a": 1.0, "b": 1.0}
        weights = {"a": 4.0, "b": 1.0}  # Weight 'a' more heavily

        distance = calculate_euclidean_distance(features1, features2, weights)

        # Distance should be sqrt(4*1^2 + 1*1^2) = sqrt(5) ≈ 2.236
        assert abs(distance - 2.236) < 0.01

    def test_partial_overlap(self):
        """Test features with partial key overlap."""
        features1 = {"a": 1.0, "b": 2.0, "c": 3.0}
        features2 = {"a": 1.5, "b": 2.5}  # Missing 'c'

        distance = calculate_euclidean_distance(features1, features2)

        # Should only calculate distance for 'a' and 'b'
        # Distance = sqrt(0.5^2 + 0.5^2) = sqrt(0.5) ≈ 0.707
        assert abs(distance - 0.707) < 0.01


class TestCalculateCosineSimilarity:
    """Tests for calculate_cosine_similarity function."""

    def test_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        features = {"a": 1.0, "b": 2.0, "c": 3.0}
        similarity = calculate_cosine_similarity(features, features)

        assert similarity == 1.0

    def test_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        features1 = {"a": 1.0, "b": 0.0}
        features2 = {"a": 0.0, "b": 1.0}
        similarity = calculate_cosine_similarity(features1, features2)

        assert similarity == 0.0

    def test_opposite_vectors(self):
        """Test cosine similarity of opposite vectors."""
        features1 = {"a": 1.0, "b": 1.0}
        features2 = {"a": -1.0, "b": -1.0}
        similarity = calculate_cosine_similarity(features1, features2)

        # Use approximate comparison for floating point
        assert abs(similarity - (-1.0)) < 0.001

    def test_zero_magnitude(self):
        """Test handling of zero magnitude vectors."""
        features1 = {"a": 0.0, "b": 0.0}
        features2 = {"a": 1.0, "b": 1.0}
        similarity = calculate_cosine_similarity(features1, features2)

        assert similarity == 0.0

    def test_similar_vectors(self):
        """Test cosine similarity of similar but not identical vectors."""
        features1 = {"a": 1.0, "b": 2.0}
        features2 = {"a": 2.0, "b": 4.0}  # Scaled version
        similarity = calculate_cosine_similarity(features1, features2)

        # Should be 1.0 (same direction, different magnitude)
        assert abs(similarity - 1.0) < 0.01


class TestCalculateManhattanDistance:
    """Tests for calculate_manhattan_distance function."""

    def test_identical_features(self):
        """Test Manhattan distance of identical features."""
        features = {"a": 1.0, "b": 2.0, "c": 3.0}
        distance = calculate_manhattan_distance(features, features)

        assert distance == 0.0

    def test_simple_distance(self):
        """Test Manhattan distance calculation."""
        features1 = {"a": 0.0, "b": 0.0}
        features2 = {"a": 1.0, "b": 1.0}
        distance = calculate_manhattan_distance(features1, features2)

        assert distance == 2.0  # |1-0| + |1-0| = 2

    def test_mixed_differences(self):
        """Test Manhattan distance with mixed differences."""
        features1 = {"a": 1.0, "b": 5.0, "c": 3.0}
        features2 = {"a": 2.0, "b": 2.0, "c": 4.0}
        distance = calculate_manhattan_distance(features1, features2)

        # |2-1| + |2-5| + |4-3| = 1 + 3 + 1 = 5
        assert distance == 5.0


class TestCalculateSimilarity:
    """Tests for calculate_similarity function."""

    def test_euclidean_strategy(self, sample_audio_features, sample_audio_features_2):
        """Test Euclidean distance strategy."""
        similarity = calculate_similarity(
            sample_audio_features,
            sample_audio_features_2,
            SimilarityStrategy.EUCLIDEAN,
        )

        # Should return a value between 0 and 1
        assert 0.0 <= similarity <= 1.0
        # Similar features should have high similarity (close to 1)
        assert similarity > 0.5

    def test_weighted_strategy(self, sample_audio_features, sample_audio_features_2):
        """Test weighted strategy with custom weights."""
        weights = FeatureWeights(energy=5.0, danceability=5.0, tempo=0.1)
        similarity = calculate_similarity(
            sample_audio_features,
            sample_audio_features_2,
            SimilarityStrategy.WEIGHTED,
            weights,
        )

        assert 0.0 <= similarity <= 1.0

    def test_cosine_strategy(self, sample_audio_features, sample_audio_features_2):
        """Test cosine similarity strategy."""
        similarity = calculate_similarity(
            sample_audio_features,
            sample_audio_features_2,
            SimilarityStrategy.COSINE,
        )

        assert 0.0 <= similarity <= 1.0

    def test_manhattan_strategy(self, sample_audio_features, sample_audio_features_2):
        """Test Manhattan distance strategy."""
        similarity = calculate_similarity(
            sample_audio_features,
            sample_audio_features_2,
            SimilarityStrategy.MANHATTAN,
        )

        assert 0.0 <= similarity <= 1.0

    def test_energy_match_strategy(self):
        """Test energy match strategy."""
        features1 = {"energy": 0.9, "danceability": 0.8}
        features2 = {"energy": 0.85, "danceability": 0.75}
        similarity = calculate_similarity(
            features1, features2, SimilarityStrategy.ENERGY_MATCH
        )

        # Both features close -> high similarity
        assert similarity > 0.9

    def test_mood_match_strategy(self):
        """Test mood match strategy."""
        features1 = {"valence": 0.8, "acousticness": 0.3}
        features2 = {"valence": 0.75, "acousticness": 0.35}
        similarity = calculate_similarity(
            features1, features2, SimilarityStrategy.MOOD_MATCH
        )

        assert similarity > 0.9

    def test_rhythm_match_strategy(self):
        """Test rhythm match strategy."""
        features1 = {"tempo": 120.0}
        features2 = {"tempo": 122.0}
        similarity = calculate_similarity(
            features1, features2, SimilarityStrategy.RHYTHM_MATCH
        )

        # Similar tempos -> high similarity
        assert similarity > 0.95

    def test_genre_match_raises_error(
        self, sample_audio_features, sample_audio_features_2
    ):
        """Test that genre match strategy raises error with audio features."""
        with pytest.raises(ValueError, match="GENRE_MATCH strategy requires genre data"):
            calculate_similarity(
                sample_audio_features,
                sample_audio_features_2,
                SimilarityStrategy.GENRE_MATCH,
            )


class TestCalculateGenreSimilarity:
    """Tests for calculate_genre_similarity function."""

    def test_exact_match(self):
        """Test exact genre matches."""
        genres1 = ["rock", "indie"]
        genres2 = ["rock", "indie"]
        similarity = calculate_genre_similarity(genres1, genres2)

        assert similarity == 1.0

    def test_partial_match(self):
        """Test partial genre matches."""
        genres1 = ["rock"]
        genres2 = ["classic rock", "hard rock"]
        similarity = calculate_genre_similarity(genres1, genres2)

        # Should find partial match
        assert 0.0 < similarity < 1.0

    def test_no_match(self):
        """Test no genre overlap."""
        genres1 = ["rock", "metal"]
        genres2 = ["jazz", "blues"]
        similarity = calculate_genre_similarity(genres1, genres2)

        assert similarity == 0.0

    def test_empty_lists(self):
        """Test empty genre lists."""
        assert calculate_genre_similarity([], ["rock"]) == 0.0
        assert calculate_genre_similarity(["rock"], []) == 0.0
        assert calculate_genre_similarity([], []) == 0.0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        genres1 = ["Rock", "INDIE"]
        genres2 = ["rock", "indie"]
        similarity = calculate_genre_similarity(genres1, genres2)

        assert similarity == 1.0

    def test_substring_matching(self, sample_genres, sample_genres_2):
        """Test substring matching between genres."""
        similarity = calculate_genre_similarity(sample_genres, sample_genres_2)

        # Should find 'rock' exact match and partial matches
        assert similarity > 0.5

    def test_mixed_exact_and_partial(self):
        """Test combination of exact and partial matches."""
        genres1 = ["rock", "electronic"]
        genres2 = ["rock", "electronic dance"]
        similarity = calculate_genre_similarity(genres1, genres2)

        # One exact match (rock) + one partial match (electronic)
        # Score = (1.0 + 0.5) / 2 = 0.75
        assert abs(similarity - 0.75) < 0.01

    def test_multiple_partial_matches(self):
        """Test that only first partial match counts."""
        genres1 = ["rock"]
        genres2 = ["classic rock", "hard rock", "rock n roll"]
        similarity = calculate_genre_similarity(genres1, genres2)

        # Should only count first partial match
        assert similarity == 0.5


class TestFeatureWeights:
    """Tests for FeatureWeights Pydantic model."""

    def test_default_weights(self):
        """Test default weight values."""
        weights = FeatureWeights()

        assert weights.acousticness == 1.0
        assert weights.danceability == 1.0
        assert weights.energy == 1.0
        assert weights.instrumentalness == 1.0
        assert weights.liveness == 1.0
        assert weights.loudness == 1.0
        assert weights.speechiness == 1.0
        assert weights.valence == 1.0
        assert weights.tempo == 1.0

    def test_custom_weights(self):
        """Test setting custom weights."""
        weights = FeatureWeights(energy=5.0, danceability=3.0, valence=0.5)

        assert weights.energy == 5.0
        assert weights.danceability == 3.0
        assert weights.valence == 0.5
        assert weights.acousticness == 1.0  # Default

    def test_weight_validation_min(self):
        """Test weight minimum validation."""
        with pytest.raises(ValueError):
            FeatureWeights(energy=-1.0)

    def test_weight_validation_max(self):
        """Test weight maximum validation."""
        with pytest.raises(ValueError):
            FeatureWeights(energy=11.0)

    def test_weight_edge_values(self):
        """Test edge values for weights."""
        weights = FeatureWeights(energy=0.0, danceability=10.0)

        assert weights.energy == 0.0
        assert weights.danceability == 10.0
