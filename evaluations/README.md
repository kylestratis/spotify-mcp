# Spotify MCP Server Evaluations

This directory contains evaluation scenarios for testing the Spotify Playlist MCP Server's functionality, tool integration, and workflow capabilities.

## Overview

The evaluations test all major features of the server:
- Basic playlist management (create, add tracks)
- Track search and discovery
- All 8 similarity strategies (euclidean, weighted, cosine, manhattan, energy_match, mood_match, rhythm_match, genre_match)
- Audio feature analysis
- Recommendations with tunable parameters
- Multi-step workflows
- Pagination and large result handling
- Integration between multiple tools

## Evaluation Files

### spotify_eval.xml

Contains 12 comprehensive evaluation scenarios:

1. **eval_001**: Basic Playlist Creation and Population
2. **eval_002**: Similarity-Based Playlist Creation (Euclidean)
3. **eval_003**: High-Energy Workout Playlist (Energy Match)
4. **eval_004**: Genre Filtering Within Existing Playlist
5. **eval_005**: Mood-Based Playlist with Custom Weights
6. **eval_006**: Audio Feature Analysis and Comparison
7. **eval_007**: Recommendations with Audio Feature Tuning
8. **eval_008**: Finding Similar Tracks in Saved Library
9. **eval_009**: Rhythm-Based Running Playlist
10. **eval_010**: Complex Multi-Step Playlist Curation Workflow
11. **eval_011**: Artist-Style Based Discovery
12. **eval_012**: Pagination and Large Result Handling

## Using the Evaluations

### Manual Testing

Each evaluation can be tested manually by:

1. Starting the MCP server
2. Following the steps outlined in each evaluation's `expected_steps`
3. Verifying the `success_criteria` are met

Example for eval_001:
```bash
# Start server
uv run mcp dev server.py

# In MCP Inspector or Claude Desktop:
# 1. Call spotify_search_tracks with query="Eye of the Tiger Survivor"
# 2. Call spotify_create_playlist with name="Morning Energy"
# 3. Call spotify_add_tracks_to_playlist with the track URI from step 1
```

### Automated Testing

The evaluations can be used with MCP testing frameworks or custom automation:

```python
import xml.etree.ElementTree as ET

# Parse evaluations
tree = ET.parse('evaluations/spotify_eval.xml')
root = tree.getroot()

for evaluation in root.findall('evaluation'):
    eval_id = evaluation.get('id')
    name = evaluation.find('name').text
    scenario = evaluation.find('scenario').text

    print(f"Testing {eval_id}: {name}")
    # Execute test steps...
```

## Evaluation Categories

### Basic Operations (eval_001)
Tests fundamental CRUD operations for playlists and tracks.

### Similarity Engine (eval_002-005, eval_008, eval_009, eval_011)
Tests all similarity strategies:
- **Euclidean** (eval_002): General similarity across all features
- **Energy Match** (eval_003): Focus on energy and danceability
- **Genre Match** (eval_004): Artist genre-based filtering
- **Weighted** (eval_005): Custom feature weighting
- **Rhythm Match** (eval_009): Tempo-based similarity
- **Cosine** (eval_011): Angular similarity for artist style

### Audio Analysis (eval_006)
Tests retrieval and comparison of detailed audio features.

### Recommendations (eval_007)
Tests Spotify's recommendation API with tunable audio features.

### Complex Workflows (eval_010)
Tests multi-step operations that combine multiple tools.

### Scalability (eval_012)
Tests pagination and handling of large datasets.

## Success Criteria

Each evaluation includes specific success criteria to validate:
- Correct API responses
- Data integrity
- Tool integration
- Error handling
- Performance considerations

## Adding New Evaluations

To add new evaluations:

1. Add a new `<evaluation>` block in `spotify_eval.xml`
2. Include all required fields:
   - `id`: Unique identifier
   - `name`: Short descriptive name
   - `description`: One-line summary
   - `scenario`: Detailed user story
   - `expected_steps`: Numbered list of operations
   - `success_criteria`: Bulleted list of expected outcomes

3. Test the evaluation manually
4. Document any specific setup requirements

## Notes

- Some evaluations require a Spotify Premium account for full functionality
- Evaluations assume valid authentication (SPOTIFY_ACCESS_TOKEN set)
- Track IDs and playlist names may vary based on user's account and region
- Genre availability depends on Spotify's genre classifications
- Audio features endpoint may have limitations for newly created applications

## Troubleshooting

### Common Issues

**"No tracks found"**
- Track/artist names may vary by region
- Try alternative search queries
- Verify spelling and capitalization

**"Error: Resource not found (404)"**
- Playlist IDs are user-specific
- Ensure playlist exists in the authenticated user's account
- Use spotify_get_user_playlists to find correct IDs

**"Error: Authentication failed (401)"**
- Refresh your SPOTIFY_ACCESS_TOKEN
- Verify token has required scopes:
  - playlist-modify-public
  - playlist-modify-private
  - playlist-read-private
  - user-read-private

**"Genre match finds no results"**
- Some tracks may not have artist genre data
- Try with more popular artists/tracks
- Use different similarity strategies if genres unavailable

## Coverage Report

These evaluations test:
- ✅ All 9 MCP tools
- ✅ All 8 similarity strategies
- ✅ All 5 search scopes
- ✅ All 3 similarity actions
- ✅ Both response formats (markdown/json)
- ✅ Pagination parameters
- ✅ Audio feature analysis
- ✅ Error handling
- ✅ Multi-tool workflows

## Version

Evaluations version: 1.0.0
Compatible with: spotify-playlist-mcp v0.1.0
