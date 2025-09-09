# Codex Log Converter

A Python CLI tool that converts Codex transcript files into readable HTML format, inspired by [claude-code-log](https://github.com/daaain/claude-code-log).

## Features

- **Dual Mode Support**: Parse simple history logs or full session files with project grouping
- **Project Organization**: Automatically groups sessions by Git repository and working directory
- **Clean HTML Output**: Responsive design optimized for readability
- **Session Management**: Chronological ordering with proper timestamp display
- **Git Integration**: Extracts repository information, branches, and commit hashes
- **Lightweight**: Minimal dependencies for easy installation

## Installation

### Using uv (Recommended)

```bash
# Clone the project
git clone https://github.com/clsung/codex-log.git
cd codex-log

# Install with uv (creates virtual environment automatically)
uv sync

# Run the tool
uv run codex-log ~/.codex/history.jsonl output.html
```

### Alternative: Using pip

```bash
# Clone the project
git clone https://github.com/clsung/codex-log.git
cd codex-log

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the tool
codex-log ~/.codex/history.jsonl output.html
```

## Usage

### Simple Mode (History.jsonl)

Convert the basic Codex history file to HTML:

```bash
# With uv (recommended)
uv run codex-log ~/.codex/history.jsonl output.html

# Or with pip installation
codex-log ~/.codex/history.jsonl codex_log_output.html
```

This creates a chronological view of all your Codex interactions grouped by session.

### Project Mode (Session Files)

Parse session files for project-based organization:

```bash
# With uv (recommended)
uv run codex-log --sessions ~/.codex/sessions codex_projects.html

# Or specify sessions directory directly  
uv run codex-log ~/.codex/sessions codex_projects.html
```

This creates a project-centric view with:
- Git repository grouping
- Working directory information
- Project statistics and timelines
- Session previews per project

## Output Examples

### Simple Mode Output
- Single HTML file with all sessions chronologically
- Session-based navigation
- Individual entry timestamps
- Clean conversation flow

### Project Mode Output
- Project cards with repository information
- Statistics per project (sessions, entries, date ranges)
- Working directory paths
- Recent session previews
- Git repository URLs and metadata

## Project Structure

```
codex-log/
├── codex_log/                 # Main package
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py              # Data models for sessions and projects
│   ├── parser.py              # Basic history.jsonl parser
│   ├── session_parser.py      # Advanced session files parser
│   ├── renderer.py            # HTML template renderer
│   └── converter.py           # Main conversion logic and CLI
├── templates/                 # Jinja2 HTML templates
│   ├── conversation.html      # Simple session view
│   └── projects.html          # Project-grouped view
├── requirements.txt           # Python dependencies
├── CLAUDE.md                  # Project documentation
└── README.md                  # This file
```

## Data Sources

### History.jsonl Format
```json
{"session_id": "abc-123", "ts": 1234567890000, "text": "User message"}
```

### Session Files Format
Session files contain rich metadata including:
- Git repository information
- Working directory context
- Branch and commit details
- Environment configuration
- Detailed instructions and context

## Development

### Dependencies
- Python 3.8+
- jinja2 - HTML template rendering
- click - Command-line interface

### Development

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=codex_log

# Code quality checks
uv run ruff check codex_log/
uv run ruff format codex_log/
uv run mypy codex_log/

# Security scan
uv run safety check
uv run bandit -r codex_log/
```

## Key Differences from Claude Code Log

| Feature | Claude Code Log | Codex Log Converter |
|---------|-----------------|-------------------|
| **Data Source** | Claude transcript files | Codex history.jsonl + session files |
| **Project Grouping** | Manual project discovery | Automatic Git repository grouping |
| **Session Metadata** | Message-based metadata | Rich session file metadata |
| **Working Directory** | Inferred from messages | Extracted from session context |
| **Repository Info** | Not available | Git URL, branch, commit hash |
| **Template System** | Single template | Dual templates (simple/project view) |

## Examples

### Sample Project Output
When using `--sessions` mode, you'll get a project overview showing:

```
📊 ntpu-course (git@github.com:clsung/ntpu-course.git)
   - 9 sessions, 67 entries
   - Activity: August 26, 2025 - September 02, 2025
   - Working directory: /Users/clsung/git/ntpu-course

📊 url_cache (git@github.com:clsung/url_cache.git)  
   - 1 session, 2 entries
   - Activity: September 01, 2025
   - Working directory: /Users/clsung/git/url_cache
```

### CLI Help
```bash
python -m codex-log --help
```

## Documentation

For additional documentation, see the [docs/](docs/) directory:
- [Test Suite Documentation](docs/test-suite.md)
- [Testing Implementation Guide](docs/testing.md) 
- [Reference Materials](docs/claude-code-log-reference.md)

For development setup and contribution guidelines, see [CLAUDE.md](CLAUDE.md).

## License

MIT License - feel free to use and modify as needed.

## Contributing

1. Fork the repository
2. Create a feature branch  
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for detailed development setup and testing procedures.

## Acknowledgments

Based on [claude-code-log](https://github.com/daaain/claude-code-log) by daaain. Adapted for Codex log format with enhanced project grouping capabilities.
