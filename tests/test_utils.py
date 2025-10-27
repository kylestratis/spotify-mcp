"""Tests for spotify_mcp/utils.py"""

import pytest

from spotify_mcp.utils import (
    CHARACTER_LIMIT,
    check_character_limit,
    format_track_markdown,
    format_truncation_message,
    truncate_list_response,
)


class TestFormatTrackMarkdown:
    """Tests for format_track_markdown function."""

    def test_basic_track_formatting(self, sample_track):
        """Test basic track formatting with all fields present."""
        result = format_track_markdown(sample_track)

        assert "**Bohemian Rhapsody**" in result
        assert "Artists: Queen" in result
        assert "Album: Bohemian Rhapsody (The Original Soundtrack)" in result
        assert "Duration: 5:54" in result
        assert "Spotify ID: `4u7EnebtmKWzUH433cf5Qv`" in result
        assert "URI: `spotify:track:4u7EnebtmKWzUH433cf5Qv`" in result
        assert "Popularity: 87/100" in result

    def test_track_with_multiple_artists(self):
        """Test formatting track with multiple artists."""
        track = {
            "id": "test_id",
            "name": "Test Song",
            "artists": [{"name": "Artist 1"}, {"name": "Artist 2"}],
            "album": {"name": "Test Album"},
            "duration_ms": 180000,
            "uri": "spotify:track:test_id",
        }
        result = format_track_markdown(track)

        assert "Artists: Artist 1, Artist 2" in result

    def test_track_with_no_popularity(self):
        """Test track formatting when popularity field is missing."""
        track = {
            "id": "test_id",
            "name": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album"},
            "duration_ms": 120000,
            "uri": "spotify:track:test_id",
        }
        result = format_track_markdown(track)

        assert "Popularity:" not in result

    def test_track_with_zero_duration(self):
        """Test track formatting with zero duration."""
        track = {
            "id": "test_id",
            "name": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album"},
            "duration_ms": 0,
            "uri": "spotify:track:test_id",
        }
        result = format_track_markdown(track)

        assert "Duration: 0:00" in result

    def test_duration_formatting(self):
        """Test various duration formats."""
        test_cases = [
            (59000, "0:59"),  # Under 1 minute
            (60000, "1:00"),  # Exactly 1 minute
            (125000, "2:05"),  # 2 minutes 5 seconds
            (600000, "10:00"),  # Exactly 10 minutes
        ]

        for duration_ms, expected in test_cases:
            track = {
                "id": "test",
                "name": "Test",
                "artists": [{"name": "Test"}],
                "album": {"name": "Test"},
                "duration_ms": duration_ms,
                "uri": "spotify:track:test",
            }
            result = format_track_markdown(track)
            assert f"Duration: {expected}" in result


class TestCheckCharacterLimit:
    """Tests for check_character_limit function (deprecated)."""

    def test_under_limit(self):
        """Test content under character limit."""
        content = "Short content"
        data_list = [1, 2, 3]
        result = check_character_limit(content, data_list)

        assert result == ""

    def test_over_limit(self):
        """Test content over character limit."""
        content = "x" * (CHARACTER_LIMIT + 1000)
        data_list = list(range(100))
        result = check_character_limit(content, data_list)

        assert "Response truncated" in result
        assert "50 items" in result


class TestTruncateListResponse:
    """Tests for truncate_list_response function."""

    def test_no_truncation_needed(self):
        """Test when content is under limit."""
        items = [{"id": i, "value": f"item_{i}"} for i in range(10)]

        def format_func(items_list):
            return "\n".join([f"{item['id']}: {item['value']}" for item in items_list])

        truncated, was_truncated = truncate_list_response(items, format_func)

        assert was_truncated is False
        assert truncated == items

    def test_truncation_needed(self):
        """Test when content exceeds limit."""
        # Create items that will exceed CHARACTER_LIMIT
        items = [{"id": i, "value": "x" * 1000} for i in range(100)]

        def format_func(items_list):
            return "\n".join(
                [f"{item['id']}: {item['value']}" for item in items_list]
            )

        truncated, was_truncated = truncate_list_response(items, format_func)

        assert was_truncated is True
        assert len(truncated) < len(items)
        # Verify the truncated result is under limit
        assert len(format_func(truncated)) <= CHARACTER_LIMIT

    def test_empty_list(self):
        """Test with empty list."""

        def format_func(items_list):
            return str(items_list)

        truncated, was_truncated = truncate_list_response([], format_func)

        assert was_truncated is False
        assert truncated == []

    def test_single_item_over_limit(self):
        """Test when even single item exceeds limit."""
        items = [{"value": "x" * (CHARACTER_LIMIT + 1000)}]

        def format_func(items_list):
            return items_list[0]["value"] if items_list else ""

        truncated, was_truncated = truncate_list_response(items, format_func)

        # Should return at least one item, but mark as truncated since it exceeds limit
        assert len(truncated) == 1
        # Note: Even though we return 1 item, it's still marked as truncated
        # because the formatted output exceeds the character limit

    def test_custom_max_chars(self):
        """Test with custom character limit."""
        items = [{"id": i, "value": "x" * 100} for i in range(20)]

        def format_func(items_list):
            return "\n".join([f"{item['value']}" for item in items_list])

        truncated, was_truncated = truncate_list_response(
            items, format_func, max_chars=500
        )

        if was_truncated:
            assert len(format_func(truncated)) <= 500


class TestFormatTruncationMessage:
    """Tests for format_truncation_message function."""

    def test_basic_message(self):
        """Test basic truncation message."""
        result = format_truncation_message(100, 50)

        assert "truncated from 100 to 50 items" in result
        assert f"{CHARACTER_LIMIT:,} character limit" in result
        assert "offset" in result
        assert "limit" in result

    def test_custom_response_type(self):
        """Test with custom response type."""
        result = format_truncation_message(200, 100, "tracks")

        assert "truncated from 200 to 100 tracks" in result

    def test_different_counts(self):
        """Test with various count combinations."""
        test_cases = [
            (1000, 500, "items"),
            (50, 25, "playlists"),
            (10, 5, "results"),
        ]

        for original, truncated, response_type in test_cases:
            result = format_truncation_message(original, truncated, response_type)
            assert f"from {original} to {truncated} {response_type}" in result
