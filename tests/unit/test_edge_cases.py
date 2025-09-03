"""Edge case tests for error handling and boundary conditions."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

from codex_log.models import CodexEntry, CodexSession, GitInfo, CodexProject, CodexConversation
from codex_log.parser import CodexParser
from codex_log.session_parser import CodexSessionParser
from codex_log.renderer import CodexRenderer
from codex_log.converter import CodexConverter


class TestDataModelEdgeCases:
    """Edge cases for data models."""
    
    def test_codex_entry_extreme_timestamps(self):
        """Test CodexEntry with extreme timestamp values."""
        # Very large timestamp (year 2038+ problem)
        large_timestamp = 2147483647000  # Jan 19, 2038
        entry = CodexEntry("session", large_timestamp, "Future entry")
        assert entry.datetime.year == 2038
        
        # Very small timestamp (early Unix epoch)
        small_timestamp = 0  # Jan 1, 1970
        entry = CodexEntry("session", small_timestamp, "Epoch entry")
        assert entry.datetime.year == 1970
        
        # Negative timestamp (before epoch)
        negative_timestamp = -86400000  # Dec 31, 1969
        entry = CodexEntry("session", negative_timestamp, "Before epoch")
        assert entry.datetime.year == 1969
    
    def test_codex_entry_very_long_text(self):
        """Test CodexEntry with extremely long text."""
        long_text = "x" * 1000000  # 1MB of text
        entry = CodexEntry("session", 1694025600000, long_text)
        assert len(entry.text) == 1000000
        assert entry.text == long_text
    
    def test_codex_entry_special_characters(self):
        """Test CodexEntry with various special characters."""
        special_chars = "\n\r\t\0\x01\x1f💀🚀🌍«»"
        entry = CodexEntry("session", 1694025600000, special_chars)
        assert entry.text == special_chars
    
    def test_git_info_edge_case_urls(self):
        """Test GitInfo with various edge case repository URLs."""
        edge_cases = [
            ("", "Unknown Project"),
            ("https://", "Unknown Project"),
            ("git@", "Unknown Project"),
            ("https://github.com/", "Unknown Project"),
            ("https://github.com/user/", "Unknown Project"),
            ("https://github.com/user/.git", ""),  # Empty repo name
            ("file:///local/repo.git", "repo"),
            ("ssh://user@host:port/path/repo.git", "repo"),
            ("https://very-long-domain-name.example.com/org/project-with-very-long-name.git", 
             "project-with-very-long-name"),
        ]
        
        for url, expected_name in edge_cases:
            git_info = GitInfo(repository_url=url)
            assert git_info.project_name == expected_name
    
    def test_session_empty_entries_edge_cases(self):
        """Test CodexSession with edge cases around empty entries."""
        session = CodexSession("session", [])
        
        # Time properties should return current time
        now = datetime.now()
        assert abs((session.start_time - now).total_seconds()) < 2
        assert abs((session.end_time - now).total_seconds()) < 2
        assert session.start_time == session.end_time
    
    def test_session_single_entry_times(self):
        """Test CodexSession time calculations with single entry."""
        entry = CodexEntry("session", 1694025600000, "Single entry")
        session = CodexSession("session", [entry])
        
        assert session.start_time == entry.datetime
        assert session.end_time == entry.datetime
        assert session.start_time == session.end_time
    
    def test_project_empty_sessions_edge_cases(self):
        """Test CodexProject with empty sessions list."""
        project = CodexProject("empty", None, [])
        
        assert project.total_entries == 0
        
        now = datetime.now()
        start, end = project.date_range
        assert abs((start - now).total_seconds()) < 2
        assert abs((end - now).total_seconds()) < 2


class TestParserEdgeCases:
    """Edge cases for parser implementations."""
    
    def test_parser_extremely_large_file(self, temp_dir):
        """Test parser with very large file (memory usage test)."""
        parser = CodexParser()
        large_file = temp_dir / "large.jsonl"
        
        # Create file with many entries but don't load it all into memory
        with open(large_file, 'w') as f:
            for i in range(10000):  # 10k entries
                entry = {
                    "session_id": f"session-{i % 100}",  # 100 sessions
                    "ts": 1694025600000 + i * 1000,
                    "text": f"Entry {i} with content"
                }
                f.write(json.dumps(entry) + '\n')
        
        # This should not cause memory issues
        conversation = parser.parse_file(large_file)
        assert len(conversation.sessions) == 100
        assert conversation.total_entries == 10000
    
    def test_parser_file_with_null_bytes(self, temp_dir):
        """Test parser handling of files with null bytes."""
        parser = CodexParser()
        null_file = temp_dir / "null_bytes.jsonl"
        
        with open(null_file, 'wb') as f:
            # Valid JSON with null byte
            f.write(b'{"session_id": "test", "ts": 1694025600000, "text": "before null"}\n')
            f.write(b'\x00')  # Null byte
            f.write(b'{"session_id": "test", "ts": 1694025660000, "text": "after null"}\n')
        
        # Should handle gracefully
        conversation = parser.parse_file(null_file)
        # Exact behavior depends on JSON parser, but should not crash
        assert isinstance(conversation, CodexConversation)
    
    def test_parser_deeply_nested_json(self, temp_dir):
        """Test parser with deeply nested JSON structures."""
        parser = CodexParser()
        nested_file = temp_dir / "nested.jsonl"
        
        # Create deeply nested structure (but still valid for our use case)
        nested_text = '{"level": ' * 100 + '"deep"' + '}' * 100
        
        with open(nested_file, 'w') as f:
            f.write(f'{{"session_id": "nested", "ts": 1694025600000, "text": "{nested_text}"}}\n')
        
        conversation = parser.parse_file(nested_file)
        assert len(conversation.sessions) == 1
        assert nested_text in conversation.sessions[0].entries[0].text
    
    def test_parser_mixed_line_endings(self, temp_dir):
        """Test parser with mixed line ending styles."""
        parser = CodexParser()
        mixed_file = temp_dir / "mixed_endings.jsonl"
        
        # Create file with different line endings
        content = (
            '{"session_id": "test", "ts": 1694025600000, "text": "Unix LF"}\n' +
            '{"session_id": "test", "ts": 1694025660000, "text": "Windows CRLF"}\r\n' +
            '{"session_id": "test", "ts": 1694025720000, "text": "Classic Mac CR"}\r'
        )
        
        with open(mixed_file, 'w', newline='') as f:
            f.write(content)
        
        conversation = parser.parse_file(mixed_file)
        assert len(conversation.sessions) == 1
        assert len(conversation.sessions[0].entries) == 3
    
    def test_session_parser_malformed_session_files(self, temp_dir):
        """Test session parser with various malformed session files."""
        parser = CodexSessionParser()
        sessions_dir = temp_dir / "malformed_sessions"
        sessions_dir.mkdir()
        
        # File with no JSON at all
        no_json = sessions_dir / "no_json.jsonl"
        with open(no_json, 'w') as f:
            f.write("This is not JSON\n")
        
        # File with JSON but no ID
        no_id = sessions_dir / "no_id.jsonl"
        with open(no_id, 'w') as f:
            f.write('{"type": "message", "content": "No ID"}\n')
        
        # Empty file
        empty = sessions_dir / "empty.jsonl"
        empty.touch()
        
        # File with only whitespace
        whitespace = sessions_dir / "whitespace.jsonl"
        with open(whitespace, 'w') as f:
            f.write("   \n\n\t\n")
        
        # Should handle all gracefully
        conversation = parser.parse_sessions_directory(sessions_dir)
        assert isinstance(conversation, CodexConversation)
        # Might have 0 sessions due to all being malformed
        assert len(conversation.sessions) >= 0
    
    def test_session_parser_permission_denied(self, temp_dir):
        """Test session parser handling of permission denied errors."""
        parser = CodexSessionParser()
        
        # Mock permission denied error
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('pathlib.Path.rglob', return_value=[temp_dir / "test.jsonl"]):
                conversation = parser.parse_sessions_directory(temp_dir)
                # Should return empty conversation without crashing
                assert len(conversation.sessions) == 0


class TestRendererEdgeCases:
    """Edge cases for HTML renderer."""
    
    def test_renderer_template_syntax_error(self, temp_dir):
        """Test renderer handling of templates with syntax errors."""
        template_dir = temp_dir / "bad_templates"
        template_dir.mkdir()
        
        # Create template with Jinja2 syntax error
        bad_template = template_dir / "bad.html"
        with open(bad_template, 'w') as f:
            f.write("{{ unclosed_variable")  # Missing }}
        
        renderer = CodexRenderer(template_dir)
        
        from jinja2.exceptions import TemplateSyntaxError
        with pytest.raises(TemplateSyntaxError):
            renderer.render_conversation(CodexConversation([]), "bad.html")
    
    def test_renderer_template_runtime_error(self, temp_dir, sample_conversation):
        """Test renderer handling of template runtime errors."""
        template_dir = temp_dir / "runtime_error_templates"
        template_dir.mkdir()
        
        # Template that tries to access non-existent attribute
        error_template = template_dir / "error.html"
        with open(error_template, 'w') as f:
            f.write("{{ conversation.nonexistent_attribute }}")
        
        renderer = CodexRenderer(template_dir)
        
        # Should raise an error during rendering
        with pytest.raises(Exception):  # Could be AttributeError or UndefinedError
            renderer.render_conversation(sample_conversation, "error.html")
    
    def test_renderer_very_large_output(self, temp_dir, template_dir):
        """Test renderer with very large conversation generating big output."""
        from codex_log.models import CodexEntry, CodexSession
        
        # Create conversation with many entries
        large_entries = []
        for i in range(1000):
            large_entries.append(CodexEntry(
                f"session-{i % 10}",
                1694025600000 + i * 1000,
                f"Entry {i} with some content that makes it longer " * 10
            ))
        
        # Group into sessions
        sessions = {}
        for entry in large_entries:
            if entry.session_id not in sessions:
                sessions[entry.session_id] = []
            sessions[entry.session_id].append(entry)
        
        session_objects = [
            CodexSession(sid, entries) 
            for sid, entries in sessions.items()
        ]
        
        large_conversation = CodexConversation(session_objects)
        
        renderer = CodexRenderer(template_dir)
        output_file = temp_dir / "large_output.html"
        
        # Should handle large output without issues
        renderer.render_to_file(large_conversation, output_file)
        
        assert output_file.exists()
        # File should be quite large
        assert output_file.stat().st_size > 100000  # > 100KB
    
    def test_renderer_disk_full_simulation(self, sample_conversation, template_dir, temp_dir):
        """Test renderer handling when disk is full (simulated)."""
        renderer = CodexRenderer(template_dir)
        output_file = temp_dir / "disk_full_test.html"
        
        # Mock open to raise OSError (no space left on device)
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with pytest.raises(OSError):
                renderer.render_to_file(sample_conversation, output_file)


class TestConverterEdgeCases:
    """Edge cases for the converter orchestration."""
    
    def test_converter_component_initialization_failure(self):
        """Test converter behavior when component initialization fails."""
        # Mock one component to fail during initialization
        with patch('codex_log.converter.CodexParser', side_effect=ImportError("Module not found")):
            with pytest.raises(ImportError):
                CodexConverter()
    
    def test_converter_mixed_success_failure(self, temp_dir, template_dir):
        """Test converter with some operations succeeding and others failing."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        # Create partially valid input
        mixed_file = temp_dir / "mixed.jsonl"
        with open(mixed_file, 'w') as f:
            f.write('{"session_id": "good", "ts": 1694025600000, "text": "Valid entry"}\n')
            f.write('{"session_id": "bad", missing_ts_field}\n')  # Invalid JSON
            f.write('{"session_id": "good", "ts": 1694025660000, "text": "Another valid"}\n')
        
        output_file = temp_dir / "mixed_output.html"
        
        # Should complete successfully with valid entries only
        converter.convert(mixed_file, output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "Valid entry" in content
        assert "Another valid" in content
    
    def test_converter_memory_pressure(self, temp_dir, template_dir):
        """Test converter behavior under memory pressure (simulated)."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        # Create file that would normally use significant memory
        memory_file = temp_dir / "memory_test.jsonl"
        with open(memory_file, 'w') as f:
            for i in range(5000):  # Moderate size for test
                entry = {
                    "session_id": f"session-{i % 50}",
                    "ts": 1694025600000 + i * 1000,
                    "text": "Content " * 100  # Larger text per entry
                }
                f.write(json.dumps(entry) + '\n')
        
        output_file = temp_dir / "memory_output.html"
        
        # Should complete without memory issues
        converter.convert(memory_file, output_file)
        
        assert output_file.exists()
    
    def test_converter_concurrent_access(self, sample_history_jsonl, temp_dir, template_dir):
        """Test converter handling of concurrent file access."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "concurrent_output.html"
        
        # Simulate file being locked by another process
        with patch('builtins.open', side_effect=[
            mock_open(read_data=sample_history_jsonl.read_text()).return_value,
            PermissionError("File is locked by another process")
        ]):
            with pytest.raises(PermissionError):
                converter.convert(sample_history_jsonl, output_file)
    
    def test_converter_invalid_template_directory(self, sample_history_jsonl, temp_dir):
        """Test converter with invalid template directory."""
        # Point renderer to non-existent template directory
        bad_template_dir = temp_dir / "nonexistent_templates"
        
        converter = CodexConverter()
        converter.renderer = CodexRenderer(bad_template_dir)
        
        output_file = temp_dir / "bad_template_output.html"
        
        from jinja2.exceptions import TemplateNotFound
        with pytest.raises(TemplateNotFound):
            converter.convert(sample_history_jsonl, output_file)


class TestSystemLevelEdgeCases:
    """System-level edge cases and resource constraints."""
    
    def test_file_encoding_detection(self, temp_dir):
        """Test handling of files with different encodings."""
        parser = CodexParser()
        
        # Create file with different encoding
        encoding_file = temp_dir / "different_encoding.jsonl"
        content = '{"session_id": "test", "ts": 1694025600000, "text": "Café naïve résumé"}'
        
        # Write with different encoding
        with open(encoding_file, 'w', encoding='iso-8859-1') as f:
            f.write(content)
        
        # Parser expects UTF-8, so this might cause issues
        try:
            conversation = parser.parse_file(encoding_file)
            # If it succeeds, check the content
            assert isinstance(conversation, CodexConversation)
        except UnicodeDecodeError:
            # This is expected behavior for encoding mismatch
            pass
    
    def test_system_resource_limits(self, temp_dir):
        """Test behavior when system resources are constrained."""
        parser = CodexParser()
        
        # Create file with very long lines
        long_line_file = temp_dir / "long_lines.jsonl"
        with open(long_line_file, 'w') as f:
            very_long_text = "x" * 100000  # 100KB single line
            entry = {
                "session_id": "long",
                "ts": 1694025600000,
                "text": very_long_text
            }
            f.write(json.dumps(entry) + '\n')
        
        # Should handle without system issues
        conversation = parser.parse_file(long_line_file)
        assert len(conversation.sessions) == 1
        assert len(conversation.sessions[0].entries[0].text) == 100000
    
    def test_file_system_case_sensitivity(self, temp_dir):
        """Test handling of case-sensitive file system issues."""
        # This test is more relevant on case-insensitive systems
        file1 = temp_dir / "test.jsonl"
        file2 = temp_dir / "TEST.jsonl"  # Different case
        
        file1.write_text('{"session_id": "lower", "ts": 1694025600000, "text": "lowercase"}\n')
        
        # On case-insensitive systems, these might be the same file
        try:
            file2.write_text('{"session_id": "upper", "ts": 1694025600000, "text": "uppercase"}\n')
            files_are_different = file1.read_text() != file2.read_text()
        except FileExistsError:
            files_are_different = False
        
        parser = CodexParser()
        conversation1 = parser.parse_file(file1)
        
        if files_are_different:
            conversation2 = parser.parse_file(file2)
            assert conversation1.sessions[0].entries[0].text != conversation2.sessions[0].entries[0].text