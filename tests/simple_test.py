"""Simple test to verify the basic test setup works."""

from __future__ import annotations

import pytest
from datetime import datetime
from pathlib import Path

from codex_log.models import CodexEntry, CodexSession, GitInfo, CodexConversation


@pytest.mark.unit
def test_basic_model_creation():
    """Test basic model creation without factories."""
    # Test CodexEntry
    entry = CodexEntry(
        session_id="test-session",
        timestamp=int(datetime.now().timestamp() * 1000),
        text="Test message"
    )
    
    assert entry.session_id == "test-session"
    assert entry.timestamp > 0
    assert entry.text == "Test message"
    assert isinstance(entry.datetime, datetime)


@pytest.mark.unit
def test_git_info_project_name():
    """Test GitInfo project name extraction."""
    test_cases = [
        ("https://github.com/user/project.git", "project"),
        ("git@github.com:user/awesome-tool.git", "awesome-tool"), 
        ("https://gitlab.com/team/web-app.git", "web-app"),
        ("invalid-url", "invalid-url")
    ]
    
    for repo_url, expected_name in test_cases:
        git_info = GitInfo(
            repository_url=repo_url,
            branch="main",
            commit_hash="abc123"
        )
        assert git_info.project_name == expected_name


@pytest.mark.unit
def test_session_time_calculations():
    """Test session time calculations."""
    base_time = int(datetime.now().timestamp() * 1000)
    
    entries = [
        CodexEntry("session-1", base_time, "First message"),
        CodexEntry("session-1", base_time + 60000, "Second message"),  # 1 minute later
        CodexEntry("session-1", base_time + 120000, "Third message"),  # 2 minutes later
    ]
    
    session = CodexSession(
        session_id="session-1",
        entries=entries
    )
    
    assert len(session.entries) == 3
    assert session.start_time <= session.end_time
    
    # Test that all entries have the same session_id
    for entry in session.entries:
        assert entry.session_id == "session-1"


@pytest.mark.unit
def test_conversation_totals():
    """Test conversation statistics."""
    base_time = int(datetime.now().timestamp() * 1000)
    
    # Create two sessions with different entry counts
    session1_entries = [
        CodexEntry("session-1", base_time, "Message 1"),
        CodexEntry("session-1", base_time + 60000, "Message 2"),
    ]
    
    session2_entries = [
        CodexEntry("session-2", base_time + 120000, "Message 3"),
        CodexEntry("session-2", base_time + 180000, "Message 4"),
        CodexEntry("session-2", base_time + 240000, "Message 5"),
    ]
    
    sessions = [
        CodexSession(session_id="session-1", entries=session1_entries),
        CodexSession(session_id="session-2", entries=session2_entries)
    ]
    
    conversation = CodexConversation(sessions=sessions)
    
    assert len(conversation.sessions) == 2
    assert conversation.total_entries == 5  # 2 + 3
    assert not conversation.has_projects  # No projects specified


@pytest.mark.unit
def test_imports_work():
    """Test that all main modules can be imported."""
    from codex_log.parser import CodexParser
    from codex_log.session_parser import CodexSessionParser  
    from codex_log.renderer import CodexRenderer
    from codex_log.converter import CodexConverter
    
    # Test instantiation
    parser = CodexParser()
    session_parser = CodexSessionParser()
    renderer = CodexRenderer()
    converter = CodexConverter()
    
    assert parser is not None
    assert session_parser is not None
    assert renderer is not None 
    assert converter is not None


@pytest.mark.integration
def test_temp_directory(tmp_path: Path):
    """Test temporary directory fixture works."""
    test_file = tmp_path / "test.jsonl"
    test_content = '{"session_id": "test", "ts": 123456789, "text": "test"}\n'
    
    test_file.write_text(test_content)
    
    assert test_file.exists()
    assert test_file.read_text() == test_content
    assert test_file.suffix == ".jsonl"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])