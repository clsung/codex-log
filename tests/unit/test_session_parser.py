"""Unit tests for Codex session parser."""

import json
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from codex_log.session_parser import CodexSessionParser
from codex_log.models import CodexEntry, CodexSession, CodexConversation, GitInfo, CodexProject


class TestCodexSessionParser:
    """Test cases for CodexSessionParser class."""
    
    def test_parse_sessions_directory(self, sample_sessions_directory, sample_history_jsonl):
        """Test parsing a directory of session files."""
        parser = CodexSessionParser()
        
        # Mock the history file lookup
        with patch.object(parser, '_find_matching_entries', side_effect=lambda session_id: [
            CodexEntry(session_id, 1694025600000, f"Mock entry for {session_id}")
        ]):
            conversation = parser.parse_sessions_directory(sample_sessions_directory)
        
        assert isinstance(conversation, CodexConversation)
        assert len(conversation.sessions) == 2
        assert conversation.has_projects
        assert len(conversation.projects) == 2
    
    def test_parse_empty_sessions_directory(self, temp_dir):
        """Test parsing an empty sessions directory."""
        empty_dir = temp_dir / "empty_sessions"
        empty_dir.mkdir()
        
        parser = CodexSessionParser()
        conversation = parser.parse_sessions_directory(empty_dir)
        
        assert isinstance(conversation, CodexConversation)
        assert len(conversation.sessions) == 0
        assert len(conversation.projects) == 0
    
    def test_parse_session_file_valid(self, sample_session_file):
        """Test parsing a valid session file."""
        parser = CodexSessionParser()
        
        # Mock finding matching entries
        mock_entries = [
            CodexEntry("session-1", 1694025600000, "Test entry 1"),
            CodexEntry("session-1", 1694025660000, "Test entry 2"),
        ]
        
        with patch.object(parser, '_find_matching_entries', return_value=mock_entries):
            session = parser._parse_session_file(sample_session_file)
        
        assert isinstance(session, CodexSession)
        assert session.session_id == "session-1"
        assert len(session.entries) == 2
        assert session.working_directory == "/home/user/projects/awesome-project"
        assert session.git_info is not None
        assert session.git_info.repository_url == "https://github.com/user/awesome-project.git"
        assert session.git_info.branch == "main"
        assert session.instructions == "You are a helpful coding assistant."
    
    def test_parse_session_file_no_id(self, temp_dir, capsys):
        """Test parsing a session file without session ID."""
        session_file = temp_dir / "no_id.jsonl"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write('{"type": "message", "content": "No ID here"}\n')
        
        parser = CodexSessionParser()
        session = parser._parse_session_file(session_file)
        
        assert session is None
        captured = capsys.readouterr()
        assert "No session ID" in captured.out
    
    def test_parse_session_file_invalid_json(self, temp_dir, capsys):
        """Test parsing a session file with invalid JSON."""
        session_file = temp_dir / "invalid.jsonl"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}\n')
        
        parser = CodexSessionParser()
        session = parser._parse_session_file(session_file)
        
        assert session is None
        captured = capsys.readouterr()
        assert "Failed to parse session file" in captured.out
    
    def test_parse_git_info_valid(self):
        """Test parsing valid git information."""
        parser = CodexSessionParser()
        git_data = {
            "repository_url": "https://github.com/user/repo.git",
            "branch": "feature/test",
            "commit_hash": "abc123def456"
        }
        
        git_info = parser._parse_git_info(git_data)
        
        assert isinstance(git_info, GitInfo)
        assert git_info.repository_url == "https://github.com/user/repo.git"
        assert git_info.branch == "feature/test"
        assert git_info.commit_hash == "abc123def456"
    
    def test_parse_git_info_partial(self):
        """Test parsing partial git information."""
        parser = CodexSessionParser()
        git_data = {"repository_url": "https://github.com/user/repo.git"}
        
        git_info = parser._parse_git_info(git_data)
        
        assert isinstance(git_info, GitInfo)
        assert git_info.repository_url == "https://github.com/user/repo.git"
        assert git_info.branch is None
        assert git_info.commit_hash is None
    
    def test_parse_git_info_none(self):
        """Test parsing when git info is None."""
        parser = CodexSessionParser()
        git_info = parser._parse_git_info(None)
        
        assert git_info is None
    
    def test_extract_working_directory_valid(self):
        """Test extracting working directory from session lines."""
        parser = CodexSessionParser()
        lines = [
            '{"type": "metadata"}',
            '{"type": "message", "content": [{"type": "input_text", "text": "<environment_context>\\n<cwd>/home/user/project</cwd>\\n</environment_context>\\n\\nHello"}]}',
            '{"type": "response"}'
        ]
        
        working_dir = parser._extract_working_directory(lines)
        
        assert working_dir == "/home/user/project"
    
    def test_extract_working_directory_no_cwd(self):
        """Test extracting working directory when no <cwd> tag present."""
        parser = CodexSessionParser()
        lines = [
            '{"type": "message", "content": [{"type": "input_text", "text": "Hello world"}]}',
        ]
        
        working_dir = parser._extract_working_directory(lines)
        
        assert working_dir is None
    
    def test_extract_working_directory_malformed_cwd(self):
        """Test extracting working directory with malformed <cwd> tag."""
        parser = CodexSessionParser()
        lines = [
            '{"type": "message", "content": [{"type": "input_text", "text": "<environment_context>\\n<cwd>/incomplete"}]}',
        ]
        
        working_dir = parser._extract_working_directory(lines)
        
        assert working_dir is None
    
    def test_extract_working_directory_invalid_json(self):
        """Test extracting working directory with invalid JSON in lines."""
        parser = CodexSessionParser()
        lines = [
            '{"valid": "json"}',
            '{"invalid": json}',  # Invalid JSON
            '{"type": "message", "content": [{"type": "input_text", "text": "<environment_context>\\n<cwd>/home/user/project</cwd>\\n</environment_context>"}]}',
        ]
        
        working_dir = parser._extract_working_directory(lines)
        
        assert working_dir == "/home/user/project"
    
    def test_find_matching_entries_existing_file(self, sample_history_jsonl):
        """Test finding matching entries when history file exists."""
        parser = CodexSessionParser()
        
        # Mock the home directory to point to our temp file
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = sample_history_jsonl.parent.parent  # Go up to parent of .codex
            
            # Create .codex directory structure
            codex_dir = sample_history_jsonl.parent.parent / ".codex"
            codex_dir.mkdir(exist_ok=True)
            
            # Copy our sample file to the expected location
            history_file = codex_dir / "history.jsonl"
            history_file.write_text(sample_history_jsonl.read_text())
            
            entries = parser._find_matching_entries("session-1")
        
        assert len(entries) == 3
        assert all(entry.session_id == "session-1" for entry in entries)
        assert entries[0].timestamp <= entries[1].timestamp <= entries[2].timestamp  # Sorted
    
    def test_find_matching_entries_no_file(self):
        """Test finding matching entries when history file doesn't exist."""
        parser = CodexSessionParser()
        
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/nonexistent")
            entries = parser._find_matching_entries("session-1")
        
        assert entries == []
    
    def test_find_matching_entries_io_error(self, capsys):
        """Test finding matching entries with IO error."""
        parser = CodexSessionParser()
        
        with patch("pathlib.Path.home") as mock_home, \
             patch("builtins.open", side_effect=IOError("Permission denied")):
            mock_home.return_value = Path("/tmp")
            
            # Mock that file exists but can't be read
            with patch("pathlib.Path.exists", return_value=True):
                entries = parser._find_matching_entries("session-1")
        
        assert entries == []
        captured = capsys.readouterr()
        assert "Failed to read history.jsonl" in captured.out
    
    def test_group_sessions_by_project_with_git_info(self, sample_sessions):
        """Test grouping sessions by project using git info."""
        parser = CodexSessionParser()
        projects = parser._group_sessions_by_project(sample_sessions)
        
        assert len(projects) == 2
        project_names = {p.name for p in projects}
        assert "awesome-project" in project_names
        assert "scraper-tool" in project_names
        
        # Check project details
        awesome_project = next(p for p in projects if p.name == "awesome-project")
        assert awesome_project.repository_url == "https://github.com/user/awesome-project.git"
        assert len(awesome_project.sessions) == 1
    
    def test_group_sessions_by_project_with_working_dir(self):
        """Test grouping sessions by project using working directory."""
        parser = CodexSessionParser()
        
        # Create sessions with working directories but no git info
        sessions = [
            CodexSession("session-1", [], working_directory="/home/user/project-a"),
            CodexSession("session-2", [], working_directory="/home/user/project-b"),
            CodexSession("session-3", [], working_directory="/home/user/project-a"),  # Same project
        ]
        
        projects = parser._group_sessions_by_project(sessions)
        
        assert len(projects) == 2
        project_names = {p.name for p in projects}
        assert "project-a" in project_names
        assert "project-b" in project_names
        
        project_a = next(p for p in projects if p.name == "project-a")
        assert len(project_a.sessions) == 2
    
    def test_group_sessions_by_project_unknown(self):
        """Test grouping sessions with no identifiable project."""
        parser = CodexSessionParser()
        
        # Sessions with no git info or working directory
        sessions = [
            CodexSession("session-1", []),
            CodexSession("session-2", []),
        ]
        
        projects = parser._group_sessions_by_project(sessions)
        
        assert len(projects) == 1
        assert projects[0].name == "Unknown Project"
        assert len(projects[0].sessions) == 2
    
    def test_get_project_key_git_url(self):
        """Test getting project key from git URL."""
        parser = CodexSessionParser()
        
        session = CodexSession(
            "session-1", 
            [],
            git_info=GitInfo(repository_url="https://github.com/user/repo.git")
        )
        
        key = parser._get_project_key(session)
        assert key == "https://github.com/user/repo.git"
    
    def test_get_project_key_working_directory(self):
        """Test getting project key from working directory."""
        parser = CodexSessionParser()
        
        session = CodexSession("session-1", [], working_directory="/home/user/my-project")
        
        key = parser._get_project_key(session)
        assert key == "my-project"
    
    def test_get_project_key_unknown(self):
        """Test getting project key when neither git nor working dir available."""
        parser = CodexSessionParser()
        
        session = CodexSession("session-1", [])
        
        key = parser._get_project_key(session)
        assert key == "Unknown Project"
    
    def test_sessions_sorted_by_time(self, sample_sessions_directory):
        """Test that parsed sessions are sorted by start time."""
        parser = CodexSessionParser()
        
        # Mock entries with different timestamps
        def mock_find_entries(session_id):
            if session_id == "session-1":
                return [CodexEntry(session_id, 1694026000000, "Later entry")]  # Later timestamp
            else:
                return [CodexEntry(session_id, 1694025000000, "Earlier entry")]  # Earlier timestamp
        
        with patch.object(parser, '_find_matching_entries', side_effect=mock_find_entries):
            conversation = parser.parse_sessions_directory(sample_sessions_directory)
        
        # Sessions should be sorted by start time
        assert len(conversation.sessions) == 2
        assert conversation.sessions[0].start_time <= conversation.sessions[1].start_time
    
    def test_projects_sorted_by_name(self, sample_sessions):
        """Test that projects are sorted by name."""
        parser = CodexSessionParser()
        projects = parser._group_sessions_by_project(sample_sessions)
        
        project_names = [p.name.lower() for p in projects]
        assert project_names == sorted(project_names)