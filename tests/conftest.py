"""Shared pytest fixtures for Spotify MCP Server tests."""

import pytest


@pytest.fixture
def sample_track():
    """Sample track data from Spotify API."""
    return {
        "id": "4u7EnebtmKWzUH433cf5Qv",
        "name": "Bohemian Rhapsody",
        "artists": [{"id": "1dfeR4HaWDbWqFHLkxsg1d", "name": "Queen"}],
        "album": {
            "id": "6i6folBtxKV28WX3msQ4FE",
            "name": "Bohemian Rhapsody (The Original Soundtrack)",
        },
        "duration_ms": 354000,
        "popularity": 87,
        "uri": "spotify:track:4u7EnebtmKWzUH433cf5Qv",
    }


@pytest.fixture
def sample_audio_features():
    """Sample audio features from Spotify API."""
    return {
        "acousticness": 0.123,
        "danceability": 0.567,
        "energy": 0.890,
        "instrumentalness": 0.001,
        "liveness": 0.234,
        "loudness": -5.2,
        "speechiness": 0.045,
        "valence": 0.678,
        "tempo": 120.5,
        "key": 0,
        "mode": 1,
        "time_signature": 4,
    }


@pytest.fixture
def sample_audio_features_2():
    """Second sample audio features for comparison tests."""
    return {
        "acousticness": 0.150,
        "danceability": 0.600,
        "energy": 0.850,
        "instrumentalness": 0.002,
        "liveness": 0.200,
        "loudness": -6.0,
        "speechiness": 0.050,
        "valence": 0.700,
        "tempo": 125.0,
        "key": 2,
        "mode": 1,
        "time_signature": 4,
    }


@pytest.fixture
def sample_genres():
    """Sample genre list for testing genre matching."""
    return ["rock", "classic rock", "hard rock"]


@pytest.fixture
def sample_genres_2():
    """Second sample genre list for testing genre matching."""
    return ["rock", "alternative rock", "indie rock"]
