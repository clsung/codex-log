# Codex Log Converter

A Python CLI tool that converts Codex transcript JSONL files into readable HTML format, based on claude-code-log.

## Project Overview

This tool processes Codex history files (stored as JSONL) and generates clean, organized HTML pages with session navigation and chronological ordering. It's designed to create a readable log of your Codex interactions with proper session grouping and timestamps.

## Key Features

- **Session-Based Organization**: Groups Codex entries by session_id for logical conversation flow
- **Chronological Ordering**: All messages sorted by timestamp within and across sessions
- **Clean HTML Output**: Responsive design optimized for readability
- **Timestamp Display**: Shows both session-level and individual entry timestamps
- **Simple CLI Interface**: Easy-to-use command-line tool using Click
- **Lightweight Dependencies**: Minimal external dependencies for portability

## Setup Instructions

### Dependencies
- Python 3.8+
- Required packages: jinja2, click

### Installation
```bash
# Install with uv (recommended - handles virtual environment automatically)
uv sync

# Install with development dependencies
uv sync --dev

# Alternative: traditional pip approach
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Usage
```bash
# Basic usage with uv
uv run codex-log ~/.codex/history.jsonl output.html

# Project mode with uv
uv run codex-log --sessions ~/.codex/sessions codex_projects.html

# Legacy module usage
uv run python -m codex_log ~/.codex/history.jsonl output.html
```

## Development

### Project Structure
- `codex_log/` - Main package directory
  - `parser.py` - Parses Codex JSONL log files
  - `models.py` - Data models for Codex conversations
  - `renderer.py` - HTML rendering using Jinja2 templates
  - `converter.py` - Main conversion orchestration and CLI
- `templates/` - Jinja2 HTML templates
  - `conversation.html` - Main conversation viewer template
- `tests/` - Unit tests

### Key Differences from Claude Code Log
- **Data Source**: Reads from `~/.codex/history.jsonl` instead of Claude transcript files
- **Data Structure**: Adapted parser to handle Codex-specific JSONL structure with session_id, ts, and text fields
- **Session Model**: Modified data models to match Codex conversation format with simple text entries
- **Timestamp Format**: Handles Codex timestamp format (milliseconds since epoch)

### Data Models

The application uses dataclasses to parse and structure Codex data:

- **CodexEntry**: Individual entry from history.jsonl with session_id, timestamp, and text
- **CodexSession**: Group of entries from the same session with start/end times
- **CodexConversation**: Collection of all sessions with metadata

### Template System

Uses Jinja2 templates for HTML generation:
- **Session Navigation**: Displays sessions with timestamps and entry counts
- **Entry Rendering**: Shows individual entries with timestamps and formatted text
- **Responsive Design**: Mobile-friendly layout with proper spacing

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=codex_log --cov-report=html

# Run specific test categories
uv run pytest -m unit tests/
uv run pytest -m integration tests/

# Run tests in parallel
uv run pytest -n auto tests/
```

### Code Quality
```bash
# Format code
uv run black codex_log/
uv run ruff format codex_log/

# Lint code
uv run ruff check codex_log/
uv run mypy codex_log/

# Security checks
uv run safety check
uv run bandit -r codex_log/

# All quality checks
uv run ruff check codex_log/ && uv run mypy codex_log/ && uv run pytest
```

### Development with uv

The project is now fully configured for `uv` dependency management:

```bash
# Initialize new development environment
uv sync --dev

# Add new dependency
uv add new-package

# Add development dependency
uv add --dev pytest-new-plugin

# Update all dependencies
uv sync --upgrade

# Test the converter
uv run codex-log ~/.codex/history.jsonl test_output.html
```