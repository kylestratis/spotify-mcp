# Spotify Playlist MCP Server

A Model Context Protocol server for creating playlists on the fly with natural language, including using one of several similarity methods for similar tracks.

<a href="https://glama.ai/mcp/servers/@kylestratis/spotify-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@kylestratis/spotify-mcp/badge" alt="Spotify Playlist Server MCP server" />
</a>

This was built to scratch two personal itches:
1. To build playlists using natural language and with one of several similarity metrics. The ideal would be ephemeral playlists, but alas.
2. To play with the new Claude skills and see how much it aids in AI-assisted coding. Verdict: It may chew up tokens but works very well.

** WARNING **: This still needs to put through its paces in real-world testing and have some evaluations written for it.

## Features

### Core Playlist Management
- Create and manage Spotify playlists
- Search tracks across Spotify's catalog
- Get track details and recommendations
- Browse user playlists and playlist contents

### Advanced Similarity Engine
- **Audio Feature Analysis**: Extract and analyze acousticness, danceability, energy, tempo, valence, and more
- **Multiple Similarity Algorithms**: Choose from 8 different strategies (Euclidean, Cosine, Weighted, Manhattan, Energy Match, Mood Match, Rhythm Match, Genre Match)
- **Genre-Based Matching**: Find tracks with similar artist genres within playlists or collections
- **Customizable Feature Weights**: Fine-tune similarity calculations by weighting specific audio features
- **Flexible Search Scopes**: Search entire catalog, within playlists, artist discographies, albums, or saved tracks
- **Automated Actions**: Find similar tracks and automatically create playlists or add to existing ones

## Available Tools

### Basic Tools
1. **`spotify_search_tracks`** - Search for tracks by name, artist, or query
2. **`spotify_get_track`** - Get detailed information about a specific track
3. **`spotify_get_recommendations`** - Get track recommendations with tunable parameters
4. **`spotify_create_playlist`** - Create a new Spotify playlist
5. **`spotify_add_tracks_to_playlist`** - Add tracks to an existing playlist
6. **`spotify_get_user_playlists`** - List user's playlists with pagination
7. **`spotify_get_playlist_tracks`** - Get tracks from a specific playlist

### Advanced Similarity Tools
8. **`spotify_get_audio_features`** - Get detailed audio features for tracks
9. **`spotify_find_similar_tracks`** - Advanced similarity engine (see below)

## Similarity Engine

### How It Works

The similarity engine finds similar tracks using two approaches:

1. **Audio Feature Analysis**: Analyzes sonic characteristics like energy, tempo, and danceability
2. **Genre Matching**: Compares artist genres for style-based similarity

For audio feature analysis, the engine uses Spotify's audio analysis API to extract features like:

- **Acousticness** (0-1): Confidence that track uses acoustic instruments
- **Danceability** (0-1): How suitable for dancing
- **Energy** (0-1): Intensity and activity level
- **Instrumentalness** (0-1): Likelihood of no vocals
- **Valence** (0-1): Musical positiveness (happiness/cheerfulness)
- **Tempo** (BPM): Speed of the track
- **Loudness** (dB): Overall volume
- **Speechiness** (0-1): Presence of spoken words
- **Liveness** (0-1): Audience presence (live performance)

### Similarity Strategies

Choose from 8 different algorithms:

1. **`euclidean`** (Default) - Overall similarity across all features using Euclidean distance
2. **`weighted`** - Custom weighted similarity - specify importance of each feature
3. **`cosine`** - Angular similarity (good for high-dimensional matching)
4. **`manhattan`** - City-block distance metric
5. **`energy_match`** - Focus on energy and danceability for workout/party playlists
6. **`mood_match`** - Focus on valence and acousticness for mood-based matching
7. **`rhythm_match`** - Focus on tempo for rhythm-based similarity
8. **`genre_match`** - Match tracks based on artist genres (exact and partial matches)

### Search Scopes

Control where to search for similar tracks:

- **`catalog`** - Search entire Spotify catalog (uses recommendations API)
- **`playlist`** - Find similar tracks within a specific playlist
- **`artist`** - Search within an artist's discography
- **`album`** - Find similar tracks within a specific album
- **`saved_tracks`** - Search within user's saved library

### Actions

Choose what to do with similar tracks:

- **`return_tracks`** - Just return the list with similarity scores
- **`create_playlist`** - Automatically create a new playlist with similar tracks
- **`add_to_playlist`** - Add similar tracks to an existing playlist

## Installation

### Prerequisites

1. **Python 3.12+** (managed with mise)
2. **uv** for dependency management
3. **Spotify Developer Account** and API credentials

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd spotify-playlist-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your SPOTIFY_ACCESS_TOKEN
```

4. Get your Spotify access token (see `.env.example` for detailed instructions):
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create an app
   - Get your Client ID and Client Secret
   - Generate an access token with required scopes:
     - `playlist-modify-public`
     - `playlist-modify-private`
     - `playlist-read-private`
     - `user-read-private`

## Usage

### Running the Server

#### Development Mode (with MCP Inspector)
```bash
uv run mcp dev server.py
```

#### Direct Execution
```bash
uv run python server.py
```

#### Install for Claude Desktop
```bash
uv run mcp install server.py
```

### Example Use Cases

#### Find Similar Tracks in a Playlist
```
"Find songs similar to track [ID] within my workout playlist"
```

#### Create a Playlist Based on a Track
```
"Find tracks similar to [track name] using the energy_match strategy
and create a playlist called 'High Energy Workout'"
```

#### Custom Weighted Similarity
```
"Find tracks similar to this song, but prioritize energy and danceability
more than other features (weights: energy=5.0, danceability=5.0)"
```

#### Mood-Based Playlist from Artist
```
"Create a calm acoustic playlist based on [artist name]'s style
using the mood_match strategy"
```

#### Search Saved Tracks
```
"Find all tracks in my saved library that sound similar to this song"
```

#### Genre-Based Playlist Filtering
```
"Create a playlist with tracks from my Discover Weekly that have
the same genre as this track I'm listening to"
```

## Similarity Engine Examples

### Example 1: Find Similar Tracks in a Playlist

```json
{
  "track_id": "3n3Ppam7vgaVa1iaRUc9Lp",
  "strategy": "euclidean",
  "scope": "playlist",
  "scope_id": "37i9dQZF1DXcBWIGoYBM5M",
  "limit": 10,
  "action": "return_tracks"
}
```

### Example 2: Create High-Energy Workout Playlist

```json
{
  "track_id": "4iV5W9uYEdYUVa79Axb7Rh",
  "strategy": "energy_match",
  "scope": "catalog",
  "limit": 30,
  "action": "create_playlist",
  "playlist_name": "High Energy Workout"
}
```

### Example 3: Custom Weighted Similarity

```json
{
  "track_id": "7qiZfU4dY1lWllzX7mPBI",
  "strategy": "weighted",
  "weights": {
    "energy": 5.0,
    "danceability": 5.0,
    "valence": 3.0,
    "acousticness": 0.5,
    "tempo": 2.0
  },
  "scope": "catalog",
  "limit": 20,
  "action": "create_playlist",
  "playlist_name": "Custom Mix"
}
```

### Example 4: Find Similar Tracks by Artist Style

```json
{
  "artist_id": "0OdUWJ0sBjDrqHygGUXeCF",
  "strategy": "cosine",
  "scope": "saved_tracks",
  "limit": 15,
  "action": "add_to_playlist",
  "target_playlist_id": "5FqPqTauQoRPRxJBQC8C2N"
}
```

### Example 5: Genre-Based Playlist Filtering

Find tracks from a playlist that match the genre of a specific track:

```json
{
  "track_id": "3n3Ppam7vgaVa1iaRUc9Lp",
  "strategy": "genre_match",
  "scope": "playlist",
  "scope_id": "37i9dQZF1DXcBWIGoYBM5M",
  "limit": 20,
  "action": "create_playlist",
  "playlist_name": "Same Genre from Discover Weekly"
}
```

Note: `genre_match` strategy requires a specific scope (playlist, artist, album, or saved_tracks) and does not work with the catalog scope.

## Architecture

### Modular Design

The similarity engine is built with modularity in mind:

1. **Feature Normalization** - Normalizes audio features to 0-1 range
2. **Similarity Calculators** - Pluggable distance/similarity functions
3. **Scope Handlers** - Extract candidate tracks from different sources
4. **Action Executors** - Handle different output actions

### Adding Custom Strategies

To add a new similarity strategy:

1. Add the strategy to the `SimilarityStrategy` enum
2. Implement the calculation logic in `_calculate_similarity()`
3. Document the strategy in tool descriptions

## API Reference

### `spotify_find_similar_tracks`

**Parameters:**
- `track_id` (Optional[str]): Source track ID
- `artist_id` (Optional[str]): Source artist ID
- `playlist_id` (Optional[str]): Source playlist ID
- `strategy` (SimilarityStrategy): Algorithm to use
- `weights` (Optional[FeatureWeights]): Custom feature weights
- `scope` (SearchScope): Where to search
- `scope_id` (Optional[str]): ID for scope (playlist/artist/album)
- `limit` (int): Number of results (1-100)
- `min_similarity` (Optional[float]): Minimum similarity threshold
- `action` (SimilarityAction): What to do with results
- `playlist_name` (Optional[str]): Name for new playlist
- `target_playlist_id` (Optional[str]): Target for adding tracks
- `response_format` (ResponseFormat): 'markdown' or 'json'

**Returns:**
- List of similar tracks with similarity scores
- OR playlist creation confirmation
- OR add to playlist confirmation

## Troubleshooting

### Audio Features Deprecated Error

If you encounter errors about audio features being deprecated:
- Ensure you have extended mode access on your Spotify app
- Note: Audio features endpoint was deprecated for NEW applications in November 2024
- Existing applications with extended mode access can still use it

### Authentication Errors

- Access tokens expire after 1 hour - refresh regularly
- Ensure all required scopes are granted
- Check that your token is correctly set in `.env`

### Rate Limiting

- Spotify API has rate limits - the server handles 429 errors gracefully
- If searching large playlists, be patient as it may take time

## Best Practices

1. **Token Management**: Implement token refresh logic for production use
2. **Scope Selection**: Use specific scopes (playlist/artist/album) for better performance
3. **Strategy Choice**:
   - Use `euclidean` for general similarity
   - Use `energy_match` for workout/party playlists
   - Use `mood_match` for relaxation/study playlists
   - Use `rhythm_match` for tempo-based matching (running, dancing)
   - Use `genre_match` to filter playlists by genre similarity
   - Use `weighted` when you know which features matter most
4. **Genre Match Considerations**:
   - Requires specific scope (playlist, artist, album, or saved_tracks)
   - Does not work with catalog scope
   - Best for filtering existing collections by genre
   - Uses artist genres (tracks without artist genre data will be skipped)
5. **Batch Operations**: When analyzing multiple tracks, use batch endpoints
6. **Error Handling**: Always check response for errors before proceeding

## Contributing

Contributions are welcome! Areas for improvement:

- Additional similarity strategies
- More sophisticated feature weighting algorithms
- Tempo range matching with BPM bands
- Key and mode compatibility checking
- Audio analysis integration (bars, beats, segments)
- Advanced genre hierarchies and taxonomy
- Multi-artist collaboration detection

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) as it appears in the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- Follows [Model Context Protocol](https://modelcontextprotocol.io) specification
- Uses the mcp-builder Claude skill to improve code generation.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.