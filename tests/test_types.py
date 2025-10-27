"""Tests for spotify_mcp/types.py Pydantic models."""

import pytest
from pydantic import ValidationError

from spotify_mcp.similarity.engine import SearchScope
from spotify_mcp.similarity.strategies import FeatureWeights, SimilarityStrategy
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


class TestResponseFormat:
    """Tests for ResponseFormat enum."""

    def test_values(self):
        """Test ResponseFormat enum values."""
        assert ResponseFormat.MARKDOWN == "markdown"
        assert ResponseFormat.JSON == "json"


class TestSimilarityAction:
    """Tests for SimilarityAction enum."""

    def test_values(self):
        """Test SimilarityAction enum values."""
        assert SimilarityAction.RETURN_TRACKS == "return_tracks"
        assert SimilarityAction.CREATE_PLAYLIST == "create_playlist"
        assert SimilarityAction.ADD_TO_PLAYLIST == "add_to_playlist"


class TestGetRecommendationsInput:
    """Tests for GetRecommendationsInput model."""

    def test_valid_input(self):
        """Test valid recommendations input."""
        data = GetRecommendationsInput(
            seed_tracks=["track1", "track2"],
            limit=20,
            target_energy=0.8,
        )
        assert data.seed_tracks == ["track1", "track2"]
        assert data.limit == 20
        assert data.target_energy == 0.8

    def test_defaults(self):
        """Test default values."""
        data = GetRecommendationsInput(seed_tracks=["track1"])
        assert data.limit == 20
        assert data.response_format == ResponseFormat.MARKDOWN

    def test_seed_limit_validation(self):
        """Test that >5 seeds raises validation error."""
        with pytest.raises(ValidationError):
            GetRecommendationsInput(seed_tracks=["t1", "t2", "t3", "t4", "t5", "t6"])

    def test_limit_range_validation(self):
        """Test limit range validation."""
        # Valid limits
        GetRecommendationsInput(seed_tracks=["track1"], limit=1)
        GetRecommendationsInput(seed_tracks=["track1"], limit=100)

        # Invalid limits
        with pytest.raises(ValidationError):
            GetRecommendationsInput(seed_tracks=["track1"], limit=0)

        with pytest.raises(ValidationError):
            GetRecommendationsInput(seed_tracks=["track1"], limit=101)

    def test_audio_feature_range_validation(self):
        """Test audio feature range validation (0.0-1.0)."""
        # Valid
        GetRecommendationsInput(seed_tracks=["track1"], target_energy=0.0)
        GetRecommendationsInput(seed_tracks=["track1"], target_energy=1.0)

        # Invalid
        with pytest.raises(ValidationError):
            GetRecommendationsInput(seed_tracks=["track1"], target_energy=-0.1)

        with pytest.raises(ValidationError):
            GetRecommendationsInput(seed_tracks=["track1"], target_energy=1.1)


class TestCreatePlaylistInput:
    """Tests for CreatePlaylistInput model."""

    def test_valid_input(self):
        """Test valid playlist creation input."""
        data = CreatePlaylistInput(
            name="My Playlist", description="Test description", public=True
        )
        assert data.name == "My Playlist"
        assert data.description == "Test description"
        assert data.public is True

    def test_defaults(self):
        """Test default values."""
        data = CreatePlaylistInput(name="Test")
        assert data.public is True
        assert data.collaborative is False
        assert data.description is None

    def test_name_length_validation(self):
        """Test playlist name length validation."""
        # Valid
        CreatePlaylistInput(name="A")  # Min length 1
        CreatePlaylistInput(name="X" * 100)  # Max length 100

        # Invalid
        with pytest.raises(ValidationError):
            CreatePlaylistInput(name="")  # Too short

        with pytest.raises(ValidationError):
            CreatePlaylistInput(name="X" * 101)  # Too long

    def test_description_length_validation(self):
        """Test description length validation."""
        # Valid
        CreatePlaylistInput(name="Test", description="X" * 300)  # Max 300

        # Invalid
        with pytest.raises(ValidationError):
            CreatePlaylistInput(name="Test", description="X" * 301)


class TestAddTracksToPlaylistInput:
    """Tests for AddTracksToPlaylistInput model."""

    def test_valid_input(self):
        """Test valid input."""
        data = AddTracksToPlaylistInput(
            playlist_id="playlist123",
            track_uris=["spotify:track:abc", "spotify:track:def"],
            position=0,
        )
        assert data.playlist_id == "playlist123"
        assert len(data.track_uris) == 2
        assert data.position == 0

    def test_track_uris_validation(self):
        """Test track URIs list validation."""
        # Valid
        AddTracksToPlaylistInput(playlist_id="p1", track_uris=["uri1"])  # Min 1
        AddTracksToPlaylistInput(
            playlist_id="p1", track_uris=["uri" + str(i) for i in range(100)]
        )  # Max 100

        # Invalid
        with pytest.raises(ValidationError):
            AddTracksToPlaylistInput(playlist_id="p1", track_uris=[])  # Too few

        with pytest.raises(ValidationError):
            AddTracksToPlaylistInput(
                playlist_id="p1", track_uris=["uri" + str(i) for i in range(101)]
            )  # Too many

    def test_position_validation(self):
        """Test position validation."""
        # Valid
        AddTracksToPlaylistInput(
            playlist_id="p1", track_uris=["uri1"], position=0
        )  # Min 0

        # Invalid
        with pytest.raises(ValidationError):
            AddTracksToPlaylistInput(
                playlist_id="p1", track_uris=["uri1"], position=-1
            )  # Negative


class TestGetUserPlaylistsInput:
    """Tests for GetUserPlaylistsInput model."""

    def test_valid_input(self):
        """Test valid input."""
        data = GetUserPlaylistsInput(limit=20, offset=0)
        assert data.limit == 20
        assert data.offset == 0

    def test_defaults(self):
        """Test default values."""
        data = GetUserPlaylistsInput()
        assert data.limit == 20
        assert data.offset == 0
        assert data.response_format == ResponseFormat.MARKDOWN

    def test_limit_range_validation(self):
        """Test limit range validation."""
        # Valid
        GetUserPlaylistsInput(limit=1)  # Min 1
        GetUserPlaylistsInput(limit=50)  # Max 50

        # Invalid
        with pytest.raises(ValidationError):
            GetUserPlaylistsInput(limit=0)

        with pytest.raises(ValidationError):
            GetUserPlaylistsInput(limit=51)

    def test_offset_validation(self):
        """Test offset validation."""
        # Valid
        GetUserPlaylistsInput(offset=0)  # Min 0
        GetUserPlaylistsInput(offset=1000)  # Any positive number

        # Invalid
        with pytest.raises(ValidationError):
            GetUserPlaylistsInput(offset=-1)


class TestGetPlaylistTracksInput:
    """Tests for GetPlaylistTracksInput model."""

    def test_valid_input(self):
        """Test valid input."""
        data = GetPlaylistTracksInput(playlist_id="playlist123", limit=20, offset=0)
        assert data.playlist_id == "playlist123"
        assert data.limit == 20

    def test_defaults(self):
        """Test default values."""
        data = GetPlaylistTracksInput(playlist_id="playlist123")
        assert data.limit == 20
        assert data.offset == 0


class TestSearchTracksInput:
    """Tests for SearchTracksInput model."""

    def test_valid_input(self):
        """Test valid input."""
        data = SearchTracksInput(query="Bohemian Rhapsody", limit=20)
        assert data.query == "Bohemian Rhapsody"
        assert data.limit == 20

    def test_query_length_validation(self):
        """Test query length validation."""
        # Valid
        SearchTracksInput(query="A")  # Min 1
        SearchTracksInput(query="X" * 200)  # Max 200

        # Invalid
        with pytest.raises(ValidationError):
            SearchTracksInput(query="")  # Too short

        with pytest.raises(ValidationError):
            SearchTracksInput(query="X" * 201)  # Too long


class TestGetTrackInput:
    """Tests for GetTrackInput model."""

    def test_valid_input(self):
        """Test valid input."""
        data = GetTrackInput(track_id="track123")
        assert data.track_id == "track123"
        assert data.response_format == ResponseFormat.MARKDOWN

    def test_track_id_length_validation(self):
        """Test track ID length validation."""
        # Valid
        GetTrackInput(track_id="a")  # Min 1
        GetTrackInput(track_id="x" * 100)  # Max 100

        # Invalid
        with pytest.raises(ValidationError):
            GetTrackInput(track_id="")

        with pytest.raises(ValidationError):
            GetTrackInput(track_id="x" * 101)


class TestGetAudioFeaturesInput:
    """Tests for GetAudioFeaturesInput model."""

    def test_valid_input(self):
        """Test valid input."""
        data = GetAudioFeaturesInput(track_ids=["track1", "track2"])
        assert len(data.track_ids) == 2
        assert data.response_format == ResponseFormat.JSON  # Default for this model

    def test_track_ids_validation(self):
        """Test track IDs list validation."""
        # Valid
        GetAudioFeaturesInput(track_ids=["track1"])  # Min 1
        GetAudioFeaturesInput(
            track_ids=["track" + str(i) for i in range(100)]
        )  # Max 100

        # Invalid
        with pytest.raises(ValidationError):
            GetAudioFeaturesInput(track_ids=[])  # Too few

        with pytest.raises(ValidationError):
            GetAudioFeaturesInput(
                track_ids=["track" + str(i) for i in range(101)]
            )  # Too many


class TestFindSimilarTracksInput:
    """Tests for FindSimilarTracksInput model."""

    def test_valid_input_with_track_id(self):
        """Test valid input with track_id."""
        data = FindSimilarTracksInput(
            track_id="track123",
            strategy=SimilarityStrategy.EUCLIDEAN,
            scope=SearchScope.CATALOG,
            limit=20,
        )
        assert data.track_id == "track123"
        assert data.strategy == SimilarityStrategy.EUCLIDEAN
        assert data.scope == SearchScope.CATALOG
        assert data.limit == 20

    def test_defaults(self):
        """Test default values."""
        data = FindSimilarTracksInput(track_id="track123")
        assert data.strategy == SimilarityStrategy.EUCLIDEAN
        assert data.scope == SearchScope.CATALOG
        assert data.limit == 20
        assert data.action == SimilarityAction.RETURN_TRACKS
        assert data.response_format == ResponseFormat.MARKDOWN

    def test_limit_range_validation(self):
        """Test limit range validation."""
        # Valid
        FindSimilarTracksInput(track_id="t1", limit=1)  # Min 1
        FindSimilarTracksInput(track_id="t1", limit=100)  # Max 100

        # Invalid
        with pytest.raises(ValidationError):
            FindSimilarTracksInput(track_id="t1", limit=0)

        with pytest.raises(ValidationError):
            FindSimilarTracksInput(track_id="t1", limit=101)

    def test_min_similarity_range_validation(self):
        """Test min_similarity range validation."""
        # Valid
        FindSimilarTracksInput(track_id="t1", min_similarity=0.0)
        FindSimilarTracksInput(track_id="t1", min_similarity=1.0)

        # Invalid
        with pytest.raises(ValidationError):
            FindSimilarTracksInput(track_id="t1", min_similarity=-0.1)

        with pytest.raises(ValidationError):
            FindSimilarTracksInput(track_id="t1", min_similarity=1.1)

    def test_with_custom_weights(self):
        """Test input with custom weights for weighted strategy."""
        weights = FeatureWeights(energy=5.0, danceability=5.0)
        data = FindSimilarTracksInput(
            track_id="t1", strategy=SimilarityStrategy.WEIGHTED, weights=weights
        )
        assert data.weights.energy == 5.0
        assert data.weights.danceability == 5.0

    def test_multiple_strategies(self):
        """Test different strategy values."""
        for strategy in SimilarityStrategy:
            data = FindSimilarTracksInput(track_id="t1", strategy=strategy)
            assert data.strategy == strategy

    def test_multiple_scopes(self):
        """Test different scope values."""
        for scope in SearchScope:
            data = FindSimilarTracksInput(track_id="t1", scope=scope)
            assert data.scope == scope

    def test_multiple_actions(self):
        """Test different action values."""
        for action in SimilarityAction:
            data = FindSimilarTracksInput(track_id="t1", action=action)
            assert data.action == action
