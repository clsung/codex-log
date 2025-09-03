"""Integration tests for CLI interface."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch

from codex_log.converter import main


class TestCLI:
    """Test cases for CLI interface."""
    
    def test_cli_basic_usage(self, sample_history_jsonl, temp_dir, template_dir):
        """Test basic CLI usage with history file."""
        runner = CliRunner()
        output_file = temp_dir / "cli_output.html"
        
        # Mock the renderer to use test templates
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(sample_history_jsonl),
                str(output_file)
            ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Check output messages
        assert f"Parsing Codex log: {sample_history_jsonl}" in result.output
        assert "Found 2 sessions with 5 total entries" in result.output
        assert f"HTML report generated: {output_file}" in result.output
    
    def test_cli_sessions_flag(self, sample_sessions_directory, temp_dir, template_dir):
        """Test CLI with --sessions flag."""
        runner = CliRunner()
        output_file = temp_dir / "sessions_output.html"
        
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class, \
             patch('codex_log.session_parser.CodexSessionParser._find_matching_entries', return_value=[]):
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(sample_sessions_directory),
                str(output_file),
                '--sessions'
            ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        assert f"Parsing Codex sessions from: {sample_sessions_directory}" in result.output
        assert "Found 2 session files" in result.output
    
    def test_cli_sessions_auto_detect_directory(self, sample_sessions_directory, temp_dir, template_dir):
        """Test that CLI auto-detects session mode when input is a directory."""
        runner = CliRunner()
        output_file = temp_dir / "auto_sessions_output.html"
        
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class, \
             patch('codex_log.session_parser.CodexSessionParser._find_matching_entries', return_value=[]):
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(sample_sessions_directory),  # Directory input
                str(output_file)
                # No --sessions flag needed
            ])
        
        assert result.exit_code == 0
        assert f"Parsing Codex sessions from: {sample_sessions_directory}" in result.output
    
    def test_cli_input_file_not_exists(self):
        """Test CLI error handling when input file doesn't exist."""
        runner = CliRunner()
        
        result = runner.invoke(main, [
            "/path/that/does/not/exist.jsonl",
            "/tmp/output.html"
        ])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output or "No such file" in result.output
    
    def test_cli_help_message(self):
        """Test CLI help message."""
        runner = CliRunner()
        
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "Convert Codex JSONL log file to HTML" in result.output
        assert "INPUT_FILE" in result.output
        assert "OUTPUT_FILE" in result.output
        assert "--sessions" in result.output
        assert "Parse session files for project grouping" in result.output
    
    def test_cli_missing_arguments(self):
        """Test CLI error when required arguments are missing."""
        runner = CliRunner()
        
        # Missing both arguments
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing argument" in result.output
        
        # Missing output file
        result = runner.invoke(main, ["input.jsonl"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output
    
    def test_cli_invalid_output_path(self, sample_history_jsonl):
        """Test CLI error handling with invalid output path."""
        runner = CliRunner()
        
        # Try to write to a directory that should be a file
        with runner.isolated_filesystem():
            result = runner.invoke(main, [
                str(sample_history_jsonl),
                "/dev/null/invalid/path.html"
            ])
            
            # Should exit with non-zero code due to path error
            assert result.exit_code != 0
    
    def test_cli_sessions_with_default_directory(self, temp_dir, template_dir):
        """Test CLI sessions mode with default sessions directory."""
        runner = CliRunner()
        output_file = temp_dir / "default_sessions.html"
        
        # Create a dummy input file to satisfy Click's path validation
        dummy_file = temp_dir / "dummy.jsonl"
        dummy_file.touch()
        
        with patch('codex_log.converter.CodexConverter.convert_sessions') as mock_convert, \
             patch('pathlib.Path.home') as mock_home:
            
            # Mock home directory
            mock_home.return_value = temp_dir
            
            # Create mock .codex/sessions directory
            codex_dir = temp_dir / ".codex" / "sessions"
            codex_dir.mkdir(parents=True)
            
            result = runner.invoke(main, [
                str(dummy_file),
                str(output_file),
                '--sessions'
            ])
            
            # Should call convert_sessions with default directory
            mock_convert.assert_called_once()
            call_args = mock_convert.call_args[0]
            assert str(call_args[0]).endswith(".codex/sessions")
            assert call_args[1] == output_file
    
    def test_cli_empty_file_handling(self, empty_history_jsonl, temp_dir, template_dir):
        """Test CLI handling of empty input files."""
        runner = CliRunner()
        output_file = temp_dir / "empty_cli_output.html"
        
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(empty_history_jsonl),
                str(output_file)
            ])
        
        assert result.exit_code == 0
        assert "Found 0 sessions with 0 total entries" in result.output
    
    def test_cli_malformed_file_handling(self, malformed_history_jsonl, temp_dir, template_dir):
        """Test CLI handling of malformed input files."""
        runner = CliRunner()
        output_file = temp_dir / "malformed_cli_output.html"
        
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(malformed_history_jsonl),
                str(output_file)
            ])
        
        # Should succeed but with warnings in the output
        assert result.exit_code == 0
        # Parser warnings should be visible in output
        assert result.output
    
    def test_cli_unicode_file_handling(self, temp_dir, template_dir):
        """Test CLI handling of files with unicode content."""
        runner = CliRunner()
        
        # Create unicode test file
        unicode_file = temp_dir / "unicode.jsonl"
        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write('{"session_id": "unicode", "ts": 1694025600000, "text": "Hello 🌍 世界"}\n')
        
        output_file = temp_dir / "unicode_cli_output.html"
        
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(unicode_file),
                str(output_file)
            ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Check that unicode content was preserved
        content = output_file.read_text(encoding='utf-8')
        assert "Hello 🌍 世界" in content
    
    def test_cli_verbose_output_information(self, sample_history_jsonl, temp_dir, template_dir):
        """Test that CLI provides informative output messages."""
        runner = CliRunner()
        output_file = temp_dir / "verbose_output.html"
        
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(sample_history_jsonl),
                str(output_file)
            ])
        
        # Should provide step-by-step information
        output_lines = result.output.strip().split('\n')
        
        # Check for parsing step
        parsing_lines = [line for line in output_lines if "Parsing" in line]
        assert len(parsing_lines) >= 1
        
        # Check for statistics
        stats_lines = [line for line in output_lines if "Found" in line and "sessions" in line]
        assert len(stats_lines) >= 1
        
        # Check for rendering step
        rendering_lines = [line for line in output_lines if "Rendering" in line or "HTML report generated" in line]
        assert len(rendering_lines) >= 1
    
    def test_cli_path_resolution(self, sample_history_jsonl, template_dir):
        """Test that CLI properly resolves relative and absolute paths."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Create local output file (relative path)
            with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
                from codex_log.renderer import CodexRenderer
                mock_renderer_class.return_value = CodexRenderer(template_dir)
                
                result = runner.invoke(main, [
                    str(sample_history_jsonl),  # Absolute path
                    "local_output.html"         # Relative path
                ])
            
            assert result.exit_code == 0
            assert Path("local_output.html").exists()
    
    def test_cli_exit_codes(self, sample_history_jsonl, temp_dir, template_dir):
        """Test that CLI returns appropriate exit codes."""
        runner = CliRunner()
        
        # Success case
        output_file = temp_dir / "success_output.html"
        with patch('codex_log.converter.CodexRenderer') as mock_renderer_class:
            from codex_log.renderer import CodexRenderer
            mock_renderer_class.return_value = CodexRenderer(template_dir)
            
            result = runner.invoke(main, [
                str(sample_history_jsonl),
                str(output_file)
            ])
        
        assert result.exit_code == 0
        
        # Failure case - non-existent input file
        result = runner.invoke(main, [
            "/path/that/definitely/does/not/exist.jsonl",
            str(temp_dir / "fail_output.html")
        ])
        
        assert result.exit_code != 0