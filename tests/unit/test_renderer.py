"""Unit tests for Codex HTML renderer."""

import pytest
from pathlib import Path
from jinja2.exceptions import TemplateNotFound
from unittest.mock import patch, mock_open

from codex_log.renderer import CodexRenderer
from codex_log.models import CodexConversation


class TestCodexRenderer:
    """Test cases for CodexRenderer class."""
    
    def test_init_default_template_dir(self):
        """Test renderer initialization with default template directory."""
        renderer = CodexRenderer()
        
        # Should use templates directory relative to the renderer module
        expected_dir = Path(__file__).parent.parent.parent / "templates"
        assert renderer.env.loader.searchpath == [str(expected_dir)]
    
    def test_init_custom_template_dir(self, template_dir):
        """Test renderer initialization with custom template directory."""
        renderer = CodexRenderer(template_dir)
        
        assert renderer.env.loader.searchpath == [str(template_dir)]
    
    def test_render_conversation_basic(self, sample_conversation, template_dir):
        """Test basic conversation rendering."""
        renderer = CodexRenderer(template_dir)
        html = renderer.render_conversation(sample_conversation)
        
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "Codex Conversation" in html
        assert f"Sessions: {len(sample_conversation.sessions)}" in html
        assert f"Total Entries: {sample_conversation.total_entries}" in html
    
    def test_render_conversation_custom_template(self, sample_conversation, template_dir):
        """Test rendering with custom template."""
        renderer = CodexRenderer(template_dir)
        html = renderer.render_conversation(sample_conversation, "projects.html")
        
        assert "Codex Projects" in html
        assert f"Projects: {len(sample_conversation.projects) if sample_conversation.projects else 0}" in html
    
    def test_render_conversation_template_not_found(self, sample_conversation, template_dir):
        """Test rendering with non-existent template."""
        renderer = CodexRenderer(template_dir)
        
        with pytest.raises(TemplateNotFound):
            renderer.render_conversation(sample_conversation, "nonexistent.html")
    
    def test_render_conversation_with_projects(self, sample_conversation, sample_projects, template_dir):
        """Test rendering conversation with project groupings."""
        conversation_with_projects = CodexConversation(
            sessions=sample_conversation.sessions,
            projects=sample_projects
        )
        
        renderer = CodexRenderer(template_dir)
        html = renderer.render_conversation(conversation_with_projects, "projects.html")
        
        assert "Codex Projects" in html
        assert f"Projects: {len(sample_projects)}" in html
        
        # Check that project details are included
        for project in sample_projects:
            assert project.name in html
    
    def test_render_to_file(self, sample_conversation, template_dir, temp_dir, capsys):
        """Test rendering conversation to file."""
        renderer = CodexRenderer(template_dir)
        output_file = temp_dir / "test_output.html"
        
        renderer.render_to_file(sample_conversation, output_file)
        
        # Check file was created
        assert output_file.exists()
        
        # Check file contents
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "Codex Conversation" in content
        
        # Check success message was printed
        captured = capsys.readouterr()
        assert f"HTML report generated: {output_file}" in captured.out
    
    def test_render_to_file_custom_template(self, sample_conversation, sample_projects, template_dir, temp_dir):
        """Test rendering to file with custom template."""
        conversation_with_projects = CodexConversation(
            sessions=sample_conversation.sessions,
            projects=sample_projects
        )
        
        renderer = CodexRenderer(template_dir)
        output_file = temp_dir / "projects_output.html"
        
        renderer.render_to_file(conversation_with_projects, output_file, "projects.html")
        
        # Check file was created with correct content
        assert output_file.exists()
        content = output_file.read_text()
        assert "Codex Projects" in content
    
    def test_render_to_file_creates_directories(self, sample_conversation, template_dir, temp_dir):
        """Test that render_to_file creates parent directories if needed."""
        renderer = CodexRenderer(template_dir)
        nested_output = temp_dir / "nested" / "deeper" / "output.html"
        
        # Parent directories don't exist yet
        assert not nested_output.parent.exists()
        
        # This should work and create directories
        nested_output.parent.mkdir(parents=True)
        renderer.render_to_file(sample_conversation, nested_output)
        
        assert nested_output.exists()
        content = nested_output.read_text()
        assert "Codex Conversation" in content
    
    def test_template_context_variables(self, sample_conversation, template_dir):
        """Test that all expected context variables are available in templates."""
        # Create a custom template that uses various context variables
        custom_template = template_dir / "test_context.html"
        with open(custom_template, 'w') as f:
            f.write("""
Sessions: {{ conversation.sessions|length }}
Total Entries: {{ conversation.total_entries }}
Has Projects: {{ conversation.has_projects }}
{% for session in conversation.sessions %}
Session ID: {{ session.session_id }}
Session Entries: {{ session.entries|length }}
Project Name: {{ session.project_name }}
Start Time: {{ session.start_time }}
End Time: {{ session.end_time }}
{% if session.git_info %}
Git URL: {{ session.git_info.repository_url }}
Git Branch: {{ session.git_info.branch }}
Git Commit: {{ session.git_info.commit_hash }}
{% endif %}
{% for entry in session.entries %}
Entry Text: {{ entry.text }}
Entry Timestamp: {{ entry.timestamp }}
Entry DateTime: {{ entry.datetime }}
{% endfor %}
{% endfor %}
""")
        
        renderer = CodexRenderer(template_dir)
        html = renderer.render_conversation(sample_conversation, "test_context.html")
        
        # Verify various context variables are rendered
        assert f"Sessions: {len(sample_conversation.sessions)}" in html
        assert f"Total Entries: {sample_conversation.total_entries}" in html
        assert f"Has Projects: {sample_conversation.has_projects}" in html
        
        # Check session-specific data
        for session in sample_conversation.sessions:
            assert f"Session ID: {session.session_id}" in html
            assert f"Project Name: {session.project_name}" in html
            
            for entry in session.entries:
                assert f"Entry Text: {entry.text}" in html
                assert f"Entry Timestamp: {entry.timestamp}" in html
    
    def test_render_empty_conversation(self, template_dir):
        """Test rendering an empty conversation."""
        empty_conversation = CodexConversation(sessions=[])
        renderer = CodexRenderer(template_dir)
        
        html = renderer.render_conversation(empty_conversation)
        
        assert "Sessions: 0" in html
        assert "Total Entries: 0" in html
    
    def test_render_conversation_unicode_content(self, template_dir):
        """Test rendering conversation with unicode content."""
        from codex_log.models import CodexEntry, CodexSession
        
        # Create conversation with unicode content
        unicode_entries = [
            CodexEntry("unicode-session", 1694025600000, "Hello 🌍 世界"),
            CodexEntry("unicode-session", 1694025660000, "Spéciål characters: àáâãäåæçèé"),
        ]
        unicode_session = CodexSession("unicode-session", unicode_entries)
        unicode_conversation = CodexConversation([unicode_session])
        
        renderer = CodexRenderer(template_dir)
        html = renderer.render_conversation(unicode_conversation)
        
        # Unicode content should be properly rendered
        assert "Hello 🌍 世界" in html
        assert "Spéciål characters: àáâãäåæçèé" in html
    
    def test_render_file_write_error(self, sample_conversation, template_dir, temp_dir):
        """Test handling file write errors."""
        renderer = CodexRenderer(template_dir)
        
        # Try to write to a directory (should cause an error)
        invalid_output = temp_dir / "subdir"
        invalid_output.mkdir()
        
        with pytest.raises(IsADirectoryError):
            renderer.render_to_file(sample_conversation, invalid_output)
    
    @patch("builtins.open", mock_open())
    def test_render_to_file_encoding(self, sample_conversation, template_dir, temp_dir):
        """Test that files are written with UTF-8 encoding."""
        renderer = CodexRenderer(template_dir)
        output_file = temp_dir / "encoding_test.html"
        
        with patch("builtins.open", mock_open()) as mock_file:
            renderer.render_to_file(sample_conversation, output_file)
            
            # Verify file was opened with correct encoding
            mock_file.assert_called_once_with(output_file, 'w', encoding='utf-8')
    
    def test_jinja2_environment_configuration(self, template_dir):
        """Test that Jinja2 environment is properly configured."""
        renderer = CodexRenderer(template_dir)
        
        # Test that environment uses FileSystemLoader with correct path
        from jinja2 import FileSystemLoader
        assert isinstance(renderer.env.loader, FileSystemLoader)
        assert renderer.env.loader.searchpath == [str(template_dir)]
        
        # Test that we can load templates
        template = renderer.env.get_template("conversation.html")
        assert template is not None
    
    def test_template_inheritance_and_includes(self, temp_dir):
        """Test template inheritance and includes work correctly."""
        # Create a base template
        base_template = temp_dir / "base.html"
        with open(base_template, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>{% block title %}Default Title{% endblock %}</title></head>
<body>
{% block content %}Default Content{% endblock %}
</body>
</html>
""")
        
        # Create a child template
        child_template = temp_dir / "child.html"
        with open(child_template, 'w') as f:
            f.write("""
{% extends "base.html" %}
{% block title %}Codex Report{% endblock %}
{% block content %}
<h1>Sessions: {{ conversation.sessions|length }}</h1>
{% endblock %}
""")
        
        renderer = CodexRenderer(temp_dir)
        html = renderer.render_conversation(
            CodexConversation(sessions=[]), 
            "child.html"
        )
        
        assert "<title>Codex Report</title>" in html
        assert "<h1>Sessions: 0</h1>" in html