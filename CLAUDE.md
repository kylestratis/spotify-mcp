# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for Spotify playlist management. The project uses `uv` for dependency management and requires Python 3.12+.

## Development Environment

- **Python Version**: 3.12+
- **Package Manager**: `uv` (as per user's Python directives)
- **Tool Manager**: `mise` (as per user's Python directives)

## Running the Code

```bash
uv run main.py
```

## Verifying the Code
Use `ruff` with `uv` to lint the code and fix errors. 

## Project Structure

Currently a single-file project:
- [main.py](main.py) - Entry point with placeholder implementation

## Architecture Notes

This project is in its initial state. When implementing the MCP server:
- The MCP server should expose Spotify playlist operations as tools/resources
- Authentication with Spotify API will need to be handled (OAuth flow)
- Consider using the `mcp` Python package for server implementation
- Main functionality should expose tools for: listing playlists, creating playlists, adding/removing tracks, searching tracks
