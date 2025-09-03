"""Unit tests for Codex JSONL parser."""

import json
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from codex_log.parser import CodexParser
from codex_log.models import CodexEntry, CodexSession, CodexConversation


class TestCodexParser:
    """Test cases for CodexParser class."""
    
    def test_parse_valid_file(self, sample_history_jsonl):
        """Test parsing a valid history.jsonl file."""
        parser = CodexParser()
        conversation = parser.parse_file(sample_history_jsonl)
        
        assert isinstance(conversation, CodexConversation)
        assert len(conversation.sessions) == 2
        assert conversation.total_entries == 5
        
        # Check session-1
        session1 = next(s for s in conversation.sessions if s.session_id == "session-1")
        assert len(session1.entries) == 3
        assert session1.entries[0].text == "Hello, I need help with Python."
        assert session1.entries[-1].text == "Thank you for the help!"
        
        # Check session-2
        session2 = next(s for s in conversation.sessions if s.session_id == "session-2")
        assert len(session2.entries) == 2
        assert session2.entries[0].text == "I'm working on a web scraper."
    
    def test_parse_empty_file(self, empty_history_jsonl):
        """Test parsing an empty file."""
        parser = CodexParser()
        conversation = parser.parse_file(empty_history_jsonl)
        
        assert isinstance(conversation, CodexConversation)
        assert len(conversation.sessions) == 0
        assert conversation.total_entries == 0
    
    def test_parse_malformed_file(self, malformed_history_jsonl, capsys):
        """Test parsing a file with malformed JSON entries."""
        parser = CodexParser()
        conversation = parser.parse_file(malformed_history_jsonl)
        
        # Should still create a conversation with valid entries
        assert isinstance(conversation, CodexConversation)
        assert len(conversation.sessions) == 2
        assert conversation.total_entries == 2  # Only valid entries
        
        # Check that warnings were printed
        captured = capsys.readouterr()
        assert "Failed to parse line" in captured.out or "Error processing line" in captured.out
    
    def test_parse_file_not_exists(self):
        """Test parsing a non-existent file."""
        parser = CodexParser()
        non_existent_file = Path("/path/that/does/not/exist.jsonl")
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file(non_existent_file)
    
    def test_sessions_sorted_by_time(self, sample_history_jsonl):
        """Test that sessions are sorted by start time."""
        parser = CodexParser()
        conversation = parser.parse_file(sample_history_jsonl)
        
        # Sessions should be sorted by start time
        session_start_times = [session.start_time for session in conversation.sessions]
        assert session_start_times == sorted(session_start_times)
    
    def test_entries_sorted_by_timestamp_within_session(self, sample_history_jsonl):
        """Test that entries within each session are sorted by timestamp."""
        parser = CodexParser()
        conversation = parser.parse_file(sample_history_jsonl)
        
        for session in conversation.sessions:
            timestamps = [entry.timestamp for entry in session.entries]
            assert timestamps == sorted(timestamps)
    
    def test_parse_entry_valid_data(self):
        """Test _parse_entry with valid data."""
        parser = CodexParser()
        data = {"session_id": "test-session", "ts": 1694025600000, "text": "Hello"}
        
        entry = parser._parse_entry(data)
        
        assert isinstance(entry, CodexEntry)
        assert entry.session_id == "test-session"
        assert entry.timestamp == 1694025600000
        assert entry.text == "Hello"
    
    def test_parse_entry_missing_session_id(self, capsys):
        """Test _parse_entry with missing session_id."""
        parser = CodexParser()
        data = {"ts": 1694025600000, "text": "Hello"}
        
        entry = parser._parse_entry(data)
        
        assert entry is None
        captured = capsys.readouterr()
        assert "Missing required field" in captured.out
    
    def test_parse_entry_missing_timestamp(self, capsys):
        """Test _parse_entry with missing timestamp."""
        parser = CodexParser()
        data = {"session_id": "test-session", "text": "Hello"}
        
        entry = parser._parse_entry(data)
        
        assert entry is None
        captured = capsys.readouterr()
        assert "Missing required field" in captured.out
    
    def test_parse_entry_missing_text(self, capsys):
        """Test _parse_entry with missing text."""
        parser = CodexParser()
        data = {"session_id": "test-session", "ts": 1694025600000}
        
        entry = parser._parse_entry(data)
        
        assert entry is None
        captured = capsys.readouterr()
        assert "Missing required field" in captured.out
    
    def test_parse_file_with_unicode_content(self, temp_dir):
        """Test parsing file with unicode content."""
        unicode_file = temp_dir / "unicode_history.jsonl"
        
        # Create file with unicode content
        unicode_data = [
            {"session_id": "unicode-test", "ts": 1694025600000, "text": "Hello 🌍 世界 🚀"},
            {"session_id": "unicode-test", "ts": 1694025660000, "text": "Émojis and spéciål châractérs"},
        ]
        
        with open(unicode_file, 'w', encoding='utf-8') as f:
            for item in unicode_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        parser = CodexParser()
        conversation = parser.parse_file(unicode_file)
        
        assert len(conversation.sessions) == 1
        session = conversation.sessions[0]
        assert len(session.entries) == 2
        assert "🌍 世界 🚀" in session.entries[0].text
        assert "spéciål châractérs" in session.entries[1].text
    
    @patch("builtins.open", mock_open(read_data='{"invalid": "json"'))
    def test_parse_file_with_io_error(self, temp_dir, capsys):
        """Test handling IO errors during file parsing."""
        parser = CodexParser()
        test_file = temp_dir / "test.jsonl"
        
        # Mock file that raises exception when read
        with patch("builtins.open", side_effect=IOError("Disk error")):
            with pytest.raises(IOError):
                parser.parse_file(test_file)
    
    def test_parse_file_with_blank_lines(self, temp_dir):
        """Test parsing file with blank lines and whitespace."""
        test_file = temp_dir / "blank_lines.jsonl"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('{"session_id": "test", "ts": 1694025600000, "text": "First"}\n')
            f.write('\n')  # Empty line
            f.write('   \n')  # Whitespace only
            f.write('{"session_id": "test", "ts": 1694025660000, "text": "Second"}\n')
            f.write('\n')
        
        parser = CodexParser()
        conversation = parser.parse_file(test_file)
        
        assert len(conversation.sessions) == 1
        assert len(conversation.sessions[0].entries) == 2
    
    def test_multiple_sessions_grouping(self, temp_dir):
        """Test that entries are correctly grouped by session_id."""
        test_file = temp_dir / "multi_session.jsonl"
        
        # Create entries for multiple sessions in mixed order
        entries_data = [
            {"session_id": "session-a", "ts": 1694025600000, "text": "A1"},
            {"session_id": "session-b", "ts": 1694025610000, "text": "B1"},
            {"session_id": "session-a", "ts": 1694025620000, "text": "A2"},
            {"session_id": "session-c", "ts": 1694025630000, "text": "C1"},
            {"session_id": "session-b", "ts": 1694025640000, "text": "B2"},
            {"session_id": "session-a", "ts": 1694025650000, "text": "A3"},
        ]
        
        with open(test_file, 'w', encoding='utf-8') as f:
            for item in entries_data:
                f.write(json.dumps(item) + '\n')
        
        parser = CodexParser()
        conversation = parser.parse_file(test_file)
        
        assert len(conversation.sessions) == 3
        
        # Check each session has the right entries
        session_a = next(s for s in conversation.sessions if s.session_id == "session-a")
        session_b = next(s for s in conversation.sessions if s.session_id == "session-b")
        session_c = next(s for s in conversation.sessions if s.session_id == "session-c")
        
        assert len(session_a.entries) == 3
        assert len(session_b.entries) == 2
        assert len(session_c.entries) == 1
        
        # Check entries are sorted by timestamp within sessions
        assert session_a.entries[0].text == "A1"
        assert session_a.entries[1].text == "A2"
        assert session_a.entries[2].text == "A3"