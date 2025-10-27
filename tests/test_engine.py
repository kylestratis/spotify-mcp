"""Tests for spotify_mcp/similarity/engine.py (pure functions only)."""

import pytest

from spotify_mcp.similarity.engine import average_features


class TestAverageFeatures:
    """Tests for average_features function."""

    def test_single_feature_set(self, sample_audio_features):
        """Test averaging a single feature set."""
        result = average_features([sample_audio_features])

        # Should return the same values
        assert result["acousticness"] == sample_audio_features["acousticness"]
        assert result["danceability"] == sample_audio_features["danceability"]
        assert result["energy"] == sample_audio_features["energy"]
        assert result["instrumentalness"] == sample_audio_features["instrumentalness"]
        assert result["liveness"] == sample_audio_features["liveness"]
        assert result["loudness"] == sample_audio_features["loudness"]
        assert result["speechiness"] == sample_audio_features["speechiness"]
        assert result["valence"] == sample_audio_features["valence"]
        assert result["tempo"] == sample_audio_features["tempo"]

    def test_two_feature_sets(self, sample_audio_features, sample_audio_features_2):
        """Test averaging two feature sets."""
        result = average_features([sample_audio_features, sample_audio_features_2])

        # Should return averages
        expected_acousticness = (
            sample_audio_features["acousticness"]
            + sample_audio_features_2["acousticness"]
        ) / 2
        expected_energy = (
            sample_audio_features["energy"] + sample_audio_features_2["energy"]
        ) / 2

        assert abs(result["acousticness"] - expected_acousticness) < 0.001
        assert abs(result["energy"] - expected_energy) < 0.001

    def test_multiple_feature_sets(self):
        """Test averaging multiple feature sets."""
        features_list = [
            {"acousticness": 0.1, "energy": 0.9, "tempo": 120.0},
            {"acousticness": 0.3, "energy": 0.7, "tempo": 130.0},
            {"acousticness": 0.2, "energy": 0.8, "tempo": 125.0},
        ]
        result = average_features(features_list)

        # Average acousticness: (0.1 + 0.3 + 0.2) / 3 = 0.2
        # Average energy: (0.9 + 0.7 + 0.8) / 3 = 0.8
        # Average tempo: (120 + 130 + 125) / 3 = 125
        assert abs(result["acousticness"] - 0.2) < 0.001
        assert abs(result["energy"] - 0.8) < 0.001
        assert abs(result["tempo"] - 125.0) < 0.001

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot average empty features list"):
            average_features([])

    def test_missing_features(self):
        """Test handling of missing features (uses default 0.0)."""
        features_list = [
            {"acousticness": 0.5},  # Missing other features
            {"acousticness": 0.3, "energy": 0.8},
        ]
        result = average_features(features_list)

        # Acousticness: (0.5 + 0.3) / 2 = 0.4
        # Energy: (0.0 + 0.8) / 2 = 0.4 (first dict has 0.0 default)
        assert abs(result["acousticness"] - 0.4) < 0.001
        assert abs(result["energy"] - 0.4) < 0.001

    def test_all_numeric_keys_present(self):
        """Test that all expected numeric keys are present in result."""
        features_list = [
            {
                "acousticness": 0.1,
                "danceability": 0.2,
                "energy": 0.3,
                "instrumentalness": 0.4,
                "liveness": 0.5,
                "loudness": -10.0,
                "speechiness": 0.6,
                "valence": 0.7,
                "tempo": 120.0,
            }
        ]
        result = average_features(features_list)

        expected_keys = [
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

        for key in expected_keys:
            assert key in result

    def test_extreme_values(self):
        """Test averaging extreme values."""
        features_list = [
            {
                "acousticness": 0.0,
                "energy": 0.0,
                "loudness": -60.0,
                "tempo": 50.0,
            },
            {"acousticness": 1.0, "energy": 1.0, "loudness": 0.0, "tempo": 200.0},
        ]
        result = average_features(features_list)

        assert abs(result["acousticness"] - 0.5) < 0.001
        assert abs(result["energy"] - 0.5) < 0.001
        assert abs(result["loudness"] - (-30.0)) < 0.001
        assert abs(result["tempo"] - 125.0) < 0.001
