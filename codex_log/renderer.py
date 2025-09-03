"""HTML renderer for Codex conversations."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from .models import CodexConversation


class CodexRenderer:
    """Renders Codex conversations to HTML."""
    
    def __init__(self, template_dir: Path = None):
        """Initialize renderer with template directory."""
        if template_dir is None:
            # Default to templates directory relative to this file
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def render_conversation(self, conversation: CodexConversation, template_name: str = "conversation.html") -> str:
        """Render a CodexConversation to HTML string."""
        template = self.env.get_template(template_name)
        return template.render(conversation=conversation)
    
    def render_to_file(self, conversation: CodexConversation, output_path: Path, template_name: str = "conversation.html") -> None:
        """Render a CodexConversation to an HTML file."""
        html_content = self.render_conversation(conversation, template_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_path}")