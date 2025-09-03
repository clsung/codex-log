"""Integration tests for Codex converter."""

import pytest
from pathlib import Path
from unittest.mock import patch

from codex_log.converter import CodexConverter
from codex_log.models import CodexConversation


class TestCodexConverter:
    """Integration test cases for CodexConverter class."""
    
    def test_convert_basic_workflow(self, sample_history_jsonl, temp_dir, template_dir, capsys):
        """Test complete conversion workflow from JSONL to HTML."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)  # Use test templates
        
        output_file = temp_dir / "output.html"
        
        converter.convert(sample_history_jsonl, output_file)
        
        # Verify output file was created
        assert output_file.exists()
        
        # Verify output content
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "Codex Conversation" in content
        assert "Sessions: 2" in content
        assert "Total Entries: 5" in content
        
        # Verify console output
        captured = capsys.readouterr()
        assert f"Parsing Codex log: {sample_history_jsonl}" in captured.out
        assert f"Found 2 sessions with 5 total entries" in captured.out
        assert f"Rendering HTML: {output_file}" in captured.out
        assert f"HTML report generated: {output_file}" in captured.out
    
    def test_convert_sessions_workflow(self, sample_sessions_directory, temp_dir, template_dir, capsys):
        """Test complete session conversion workflow with project grouping."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "projects_output.html"
        
        # Mock the session parser's history lookup
        with patch.object(converter.session_parser, '_find_matching_entries', 
                         side_effect=lambda session_id: []):
            converter.convert_sessions(sample_sessions_directory, output_file)
        
        # Verify output file was created
        assert output_file.exists()
        
        # Verify output uses projects template
        content = output_file.read_text()
        assert "Codex Projects" in content
        
        # Verify console output
        captured = capsys.readouterr()
        assert f"Parsing Codex sessions from: {sample_sessions_directory}" in captured.out
        assert "Found 2 session files" in captured.out
        assert "Organized into" in captured.out and "projects" in captured.out
    
    def test_convert_empty_file(self, empty_history_jsonl, temp_dir, template_dir, capsys):
        """Test converting an empty JSONL file."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "empty_output.html"
        
        converter.convert(empty_history_jsonl, output_file)
        
        # Should still create output file
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "Sessions: 0" in content
        assert "Total Entries: 0" in content
        
        captured = capsys.readouterr()
        assert "Found 0 sessions with 0 total entries" in captured.out
    
    def test_convert_malformed_file(self, malformed_history_jsonl, temp_dir, template_dir, capsys):
        """Test converting a file with malformed entries."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "malformed_output.html"
        
        converter.convert(malformed_history_jsonl, output_file)
        
        # Should create output with only valid entries
        assert output_file.exists()
        
        captured = capsys.readouterr()
        assert "Found 2 sessions with 2 total entries" in captured.out  # Only valid entries
    
    def test_converter_components_integration(self):
        """Test that converter properly initializes its components."""
        converter = CodexConverter()
        
        # Verify all components are initialized
        assert converter.parser is not None
        assert converter.session_parser is not None
        assert converter.renderer is not None
        
        # Verify components are of correct types
        from codex_log.parser import CodexParser
        from codex_log.session_parser import CodexSessionParser
        from codex_log.renderer import CodexRenderer
        
        assert isinstance(converter.parser, CodexParser)
        assert isinstance(converter.session_parser, CodexSessionParser)
        assert isinstance(converter.renderer, CodexRenderer)
    
    def test_convert_sessions_no_projects(self, temp_dir, template_dir, capsys):
        """Test session conversion when no projects are identified."""
        # Create sessions directory with sessions that have no project info
        sessions_dir = temp_dir / "no_projects_sessions"
        sessions_dir.mkdir()
        
        # Create session file with minimal data
        session_file = sessions_dir / "minimal.jsonl"
        with open(session_file, 'w') as f:
            f.write('{"id": "minimal-session"}\n')
        
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "no_projects_output.html"
        
        with patch.object(converter.session_parser, '_find_matching_entries', 
                         return_value=[]):
            converter.convert_sessions(sessions_dir, output_file)
        
        # Should use conversation template instead of projects template
        content = output_file.read_text()
        assert "Codex Conversation" in content
        
        captured = capsys.readouterr()
        # Should not mention organizing into projects
        assert "Organized into" not in captured.out
    
    def test_convert_file_not_found(self, temp_dir):
        """Test error handling when input file doesn't exist."""
        converter = CodexConverter()
        non_existent_file = temp_dir / "does_not_exist.jsonl"
        output_file = temp_dir / "output.html"
        
        with pytest.raises(FileNotFoundError):
            converter.convert(non_existent_file, output_file)
    
    def test_convert_output_directory_creation(self, sample_history_jsonl, temp_dir, template_dir):
        """Test that output directory is created if it doesn't exist."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        # Create nested output path
        nested_output = temp_dir / "deep" / "nested" / "path" / "output.html"
        
        # Create parent directories
        nested_output.parent.mkdir(parents=True)
        
        converter.convert(sample_history_jsonl, nested_output)
        
        assert nested_output.exists()
        assert nested_output.is_file()
    
    def test_end_to_end_data_flow(self, sample_history_jsonl, temp_dir, template_dir):
        """Test complete data flow from input to output."""
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "e2e_output.html"
        
        converter.convert(sample_history_jsonl, output_file)
        
        # Parse the output to verify data integrity
        content = output_file.read_text()
        
        # Should contain data from the original JSONL
        assert "Hello, I need help with Python." in content
        assert "Can you help me with file parsing?" in content
        assert "Thank you for the help!" in content
        assert "I'm working on a web scraper." in content
        assert "How do I handle rate limiting?" in content
        
        # Should show correct session information
        assert "session-1" in content
        assert "session-2" in content
    
    def test_unicode_data_preservation(self, temp_dir, template_dir):
        """Test that unicode data is preserved through the conversion process."""
        # Create JSONL with unicode content
        unicode_jsonl = temp_dir / "unicode.jsonl"
        with open(unicode_jsonl, 'w', encoding='utf-8') as f:
            f.write('{"session_id": "unicode", "ts": 1694025600000, "text": "Hello 🌍 世界 🚀"}\n')
            f.write('{"session_id": "unicode", "ts": 1694025660000, "text": "Émojis and spéciål characters"}\n')
        
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "unicode_output.html"
        
        converter.convert(unicode_jsonl, output_file)
        
        content = output_file.read_text(encoding='utf-8')
        assert "Hello 🌍 世界 🚀" in content
        assert "Émojis and spéciål characters" in content
    
    def test_large_file_handling(self, temp_dir, template_dir):
        """Test handling of larger files with many entries."""
        # Create a larger JSONL file
        large_jsonl = temp_dir / "large.jsonl"
        
        with open(large_jsonl, 'w') as f:
            for i in range(100):
                session_id = f"session-{i % 10}"  # 10 different sessions
                timestamp = 1694025600000 + i * 60000  # 1 minute apart
                text = f"Entry number {i} with some content"
                f.write(f'{{"session_id": "{session_id}", "ts": {timestamp}, "text": "{text}"}}\n')
        
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "large_output.html"
        
        converter.convert(large_jsonl, output_file)
        
        # Verify processing worked
        assert output_file.exists()
        content = output_file.read_text()
        
        assert "Sessions: 10" in content  # 10 unique sessions
        assert "Total Entries: 100" in content  # 100 total entries
    
    def test_convert_sessions_with_real_git_info(self, temp_dir, template_dir):
        """Test session conversion with realistic git repository information."""
        sessions_dir = temp_dir / "git_sessions"
        sessions_dir.mkdir()
        
        # Create session with GitHub repository info
        github_session = sessions_dir / "github.jsonl"
        with open(github_session, 'w') as f:
            f.write('{"id": "github-session", "git": {"repository_url": "https://github.com/facebook/react.git", "branch": "main", "commit_hash": "abcdef123456"}}\n')
        
        # Create session with GitLab repository info
        gitlab_session = sessions_dir / "gitlab.jsonl"
        with open(gitlab_session, 'w') as f:
            f.write('{"id": "gitlab-session", "git": {"repository_url": "https://gitlab.com/gitlab-org/gitlab.git", "branch": "master", "commit_hash": "fedcba654321"}}\n')
        
        converter = CodexConverter()
        converter.renderer = converter.renderer.__class__(template_dir)
        
        output_file = temp_dir / "git_output.html"
        
        with patch.object(converter.session_parser, '_find_matching_entries', 
                         return_value=[]):
            converter.convert_sessions(sessions_dir, output_file)
        
        content = output_file.read_text()
        
        # Should organize into separate projects
        assert "react" in content
        assert "gitlab" in content
        
        # Should use projects template
        assert "Codex Projects" in content