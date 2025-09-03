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
# Create virtual environment with uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

### Usage
```bash
# Basic usage
python -m codex_log ~/.codex/history.jsonl output.html

# With virtual environment
source .venv/bin/activate
python -m codex_log ~/.codex/history.jsonl codex_log_output.html
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
python -m pytest tests/
```

### Code Quality
```bash
# Linting
python -m flake8 codex_log/
python -m mypy codex_log/

# Or with ruff (if available)
ruff check codex_log/
ruff format codex_log/
```

### Development with uv

The project works well with `uv` for dependency management:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Test the converter
python -m codex_log ~/.codex/history.jsonl test_output.html
```