"""Main converter module for Codex logs."""

import click
from pathlib import Path

from .parser import CodexParser
from .session_parser import CodexSessionParser
from .renderer import CodexRenderer


class CodexConverter:
    """Main converter class for Codex logs."""
    
    def __init__(self):
        self.parser = CodexParser()
        self.session_parser = CodexSessionParser()
        self.renderer = CodexRenderer()
    
    def convert(self, input_path: Path, output_path: Path) -> None:
        """Convert a Codex JSONL file to HTML."""
        print(f"Parsing Codex log: {input_path}")
        conversation = self.parser.parse_file(input_path)
        
        print(f"Found {len(conversation.sessions)} sessions with {conversation.total_entries} total entries")
        
        print(f"Rendering HTML: {output_path}")
        self.renderer.render_to_file(conversation, output_path)
    
    def convert_sessions(self, sessions_dir: Path, output_path: Path) -> None:
        """Convert Codex session files to HTML with project grouping."""
        print(f"Parsing Codex sessions from: {sessions_dir}")
        conversation = self.session_parser.parse_sessions_directory(sessions_dir)
        
        print(f"Found {len(conversation.sessions)} sessions with {conversation.total_entries} total entries")
        if conversation.has_projects:
            print(f"Organized into {len(conversation.projects)} projects")
        
        print(f"Rendering HTML: {output_path}")
        template = "projects.html" if conversation.has_projects else "conversation.html"
        self.renderer.render_to_file(conversation, output_path, template)


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option('--sessions', is_flag=True, help='Parse session files for project grouping')
def main(input_file: Path, output_file: Path, sessions: bool):
    """Convert Codex JSONL log file to HTML.
    
    INPUT_FILE: Path to Codex history.jsonl file or sessions directory
    OUTPUT_FILE: Path for the output HTML file
    """
    converter = CodexConverter()
    
    if sessions or input_file.is_dir():
        # Parse session files for project grouping
        sessions_dir = input_file if input_file.is_dir() else Path.home() / ".codex" / "sessions"
        converter.convert_sessions(sessions_dir, output_file)
    else:
        # Parse history.jsonl file
        converter.convert(input_file, output_file)


if __name__ == "__main__":
    main()