"""Pytest configuration and shared fixtures for Codex Log Converter tests."""

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from tempfile import TemporaryDirectory

from codex_log.models import CodexEntry, CodexSession, CodexConversation, GitInfo, CodexProject


@pytest.fixture
def sample_entries():
    """Sample CodexEntry objects for testing."""
    return [
        CodexEntry("session-1", 1694025600000, "Hello, I need help with Python."),
        CodexEntry("session-1", 1694025660000, "Can you help me with file parsing?"),
        CodexEntry("session-1", 1694025720000, "Thank you for the help!"),
        CodexEntry("session-2", 1694026800000, "I'm working on a web scraper."),
        CodexEntry("session-2", 1694026860000, "How do I handle rate limiting?"),
    ]


@pytest.fixture
def sample_git_info():
    """Sample GitInfo object for testing."""
    return GitInfo(
        repository_url="https://github.com/user/awesome-project.git",
        branch="main",
        commit_hash="abc123def456"
    )


@pytest.fixture
def sample_session(sample_entries, sample_git_info):
    """Sample CodexSession object for testing."""
    session_entries = [e for e in sample_entries if e.session_id == "session-1"]
    return CodexSession(
        session_id="session-1",
        entries=session_entries,
        working_directory="/home/user/projects/awesome-project",
        git_info=sample_git_info,
        instructions="You are a helpful coding assistant."
    )


@pytest.fixture
def sample_sessions(sample_entries):
    """Sample list of CodexSession objects for testing."""
    sessions_dict = {}
    for entry in sample_entries:
        if entry.session_id not in sessions_dict:
            sessions_dict[entry.session_id] = []
        sessions_dict[entry.session_id].append(entry)
    
    sessions = []
    for session_id, entries in sessions_dict.items():
        git_info = None
        working_dir = None
        
        if session_id == "session-1":
            git_info = GitInfo(
                repository_url="https://github.com/user/awesome-project.git",
                branch="main",
                commit_hash="abc123"
            )
            working_dir = "/home/user/projects/awesome-project"
        elif session_id == "session-2":
            git_info = GitInfo(
                repository_url="git@github.com:user/scraper-tool.git",
                branch="feature/rate-limiting",
                commit_hash="def456"
            )
            working_dir = "/home/user/projects/scraper-tool"
        
        sessions.append(CodexSession(
            session_id=session_id,
            entries=entries,
            working_directory=working_dir,
            git_info=git_info
        ))
    
    return sessions


@pytest.fixture
def sample_conversation(sample_sessions):
    """Sample CodexConversation object for testing."""
    return CodexConversation(sessions=sample_sessions)


@pytest.fixture
def sample_projects(sample_sessions):
    """Sample CodexProject objects for testing."""
    projects = []
    
    # Group sessions by project
    project_sessions = {}
    for session in sample_sessions:
        project_key = session.project_name
        if project_key not in project_sessions:
            project_sessions[project_key] = []
        project_sessions[project_key].append(session)
    
    for project_name, sessions in project_sessions.items():
        first_session = sessions[0]
        repo_url = first_session.git_info.repository_url if first_session.git_info else None
        working_dir = first_session.working_directory
        
        projects.append(CodexProject(
            name=project_name,
            repository_url=repo_url,
            sessions=sessions,
            working_directory=working_dir
        ))
    
    return projects


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_history_jsonl(temp_dir):
    """Create a sample history.jsonl file for testing."""
    history_file = temp_dir / "history.jsonl"
    
    sample_data = [
        {"session_id": "session-1", "ts": 1694025600000, "text": "Hello, I need help with Python."},
        {"session_id": "session-1", "ts": 1694025660000, "text": "Can you help me with file parsing?"},
        {"session_id": "session-1", "ts": 1694025720000, "text": "Thank you for the help!"},
        {"session_id": "session-2", "ts": 1694026800000, "text": "I'm working on a web scraper."},
        {"session_id": "session-2", "ts": 1694026860000, "text": "How do I handle rate limiting?"},
    ]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        for item in sample_data:
            f.write(json.dumps(item) + '\n')
    
    return history_file


@pytest.fixture
def malformed_history_jsonl(temp_dir):
    """Create a malformed history.jsonl file for testing error handling."""
    history_file = temp_dir / "malformed_history.jsonl"
    
    with open(history_file, 'w', encoding='utf-8') as f:
        # Valid entry
        f.write('{"session_id": "session-1", "ts": 1694025600000, "text": "Valid entry"}\n')
        # Invalid JSON
        f.write('{"session_id": "session-1", "ts": 1694025660000, "text": "Invalid JSON"\n')
        # Missing required field
        f.write('{"session_id": "session-1", "text": "Missing timestamp"}\n')
        # Empty line (should be skipped)
        f.write('\n')
        # Another valid entry
        f.write('{"session_id": "session-2", "ts": 1694025720000, "text": "Another valid entry"}\n')
    
    return history_file


@pytest.fixture
def empty_history_jsonl(temp_dir):
    """Create an empty history.jsonl file for testing."""
    history_file = temp_dir / "empty_history.jsonl"
    history_file.touch()
    return history_file


@pytest.fixture
def sample_session_file(temp_dir):
    """Create a sample session file for testing."""
    session_file = temp_dir / "session-1.jsonl"
    
    session_data = [
        {
            "id": "session-1",
            "git": {
                "repository_url": "https://github.com/user/awesome-project.git",
                "branch": "main",
                "commit_hash": "abc123def456"
            },
            "instructions": "You are a helpful coding assistant."
        },
        {
            "type": "message",
            "content": [
                {
                    "type": "input_text",
                    "text": "<environment_context>\n<cwd>/home/user/projects/awesome-project</cwd>\n</environment_context>\n\nHello, I need help with Python."
                }
            ]
        }
    ]
    
    with open(session_file, 'w', encoding='utf-8') as f:
        for item in session_data:
            f.write(json.dumps(item) + '\n')
    
    return session_file


@pytest.fixture
def sample_sessions_directory(temp_dir, sample_history_jsonl):
    """Create a sample sessions directory with multiple session files."""
    sessions_dir = temp_dir / "sessions"
    sessions_dir.mkdir()
    
    # Create multiple session files
    session_files_data = [
        {
            "filename": "session-1.jsonl",
            "data": [
                {
                    "id": "session-1",
                    "git": {
                        "repository_url": "https://github.com/user/awesome-project.git",
                        "branch": "main",
                        "commit_hash": "abc123"
                    }
                },
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "<environment_context>\n<cwd>/home/user/projects/awesome-project</cwd>\n</environment_context>\n\nHello"
                        }
                    ]
                }
            ]
        },
        {
            "filename": "session-2.jsonl",
            "data": [
                {
                    "id": "session-2",
                    "git": {
                        "repository_url": "git@github.com:user/scraper-tool.git",
                        "branch": "feature/rate-limiting",
                        "commit_hash": "def456"
                    }
                },
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "<environment_context>\n<cwd>/home/user/projects/scraper-tool</cwd>\n</environment_context>\n\nWorking on scraper"
                        }
                    ]
                }
            ]
        }
    ]
    
    for session_file_data in session_files_data:
        session_file = sessions_dir / session_file_data["filename"]
        with open(session_file, 'w', encoding='utf-8') as f:
            for item in session_file_data["data"]:
                f.write(json.dumps(item) + '\n')
    
    return sessions_dir


@pytest.fixture
def template_dir(temp_dir):
    """Create a temporary templates directory for testing."""
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir()
    
    # Create a simple test template
    conversation_template = templates_dir / "conversation.html"
    with open(conversation_template, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head><title>Codex Conversation</title></head>
<body>
<h1>Codex Conversation</h1>
<p>Sessions: {{ conversation.sessions|length }}</p>
<p>Total Entries: {{ conversation.total_entries }}</p>
{% for session in conversation.sessions %}
<div class="session">
    <h2>{{ session.session_id }}</h2>
    <p>Entries: {{ session.entries|length }}</p>
    <p>Project: {{ session.project_name }}</p>
</div>
{% endfor %}
</body>
</html>""")
    
    # Create projects template
    projects_template = templates_dir / "projects.html"
    with open(projects_template, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head><title>Codex Projects</title></head>
<body>
<h1>Codex Projects</h1>
<p>Projects: {{ conversation.projects|length }}</p>
{% if conversation.projects %}
{% for project in conversation.projects %}
<div class="project">
    <h2>{{ project.name }}</h2>
    <p>Sessions: {{ project.sessions|length }}</p>
    <p>Total Entries: {{ project.total_entries }}</p>
</div>
{% endfor %}
{% endif %}
</body>
</html>""")
    
    return templates_dir