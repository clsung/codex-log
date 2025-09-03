"""Parser for Codex session files with project grouping."""

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime

from .models import CodexEntry, CodexSession, CodexConversation, CodexProject, GitInfo


class CodexSessionParser:
    """Parser for Codex session files with project grouping support."""
    
    def parse_sessions_directory(self, sessions_dir: Path) -> CodexConversation:
        """Parse all session files in the sessions directory."""
        sessions = []
        session_files = list(sessions_dir.rglob("*.jsonl"))
        
        print(f"Found {len(session_files)} session files")
        
        for session_file in session_files:
            session = self._parse_session_file(session_file)
            if session:
                sessions.append(session)
        
        # Sort sessions by start time
        sessions.sort(key=lambda x: x.start_time)
        
        # Group by projects
        projects = self._group_sessions_by_project(sessions)
        
        return CodexConversation(sessions=sessions, projects=projects)
    
    def _parse_session_file(self, session_file: Path) -> Optional[CodexSession]:
        """Parse a single session file."""
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            if not lines:
                return None
            
            # Parse first line for session metadata
            first_line = json.loads(lines[0])
            session_id = first_line.get('id')
            if not session_id:
                print(f"Warning: No session ID in {session_file}")
                return None
            
            # Extract git and environment info
            git_info = self._parse_git_info(first_line.get('git'))
            working_directory = self._extract_working_directory(lines)
            instructions = first_line.get('instructions')
            
            # Find corresponding entries in history.jsonl
            entries = self._find_matching_entries(session_id)
            
            return CodexSession(
                session_id=session_id,
                entries=entries,
                working_directory=working_directory,
                git_info=git_info,
                instructions=instructions
            )
            
        except Exception as e:
            print(f"Warning: Failed to parse session file {session_file}: {e}")
            return None
    
    def _parse_git_info(self, git_data: Optional[dict]) -> Optional[GitInfo]:
        """Parse git information from session metadata."""
        if not git_data:
            return None
        
        return GitInfo(
            repository_url=git_data.get('repository_url'),
            branch=git_data.get('branch'),
            commit_hash=git_data.get('commit_hash')
        )
    
    def _extract_working_directory(self, lines: List[str]) -> Optional[str]:
        """Extract working directory from environment_context in session lines."""
        for line in lines:
            try:
                data = json.loads(line)
                if data.get('type') == 'message':
                    content = data.get('content', [])
                    for item in content:
                        if item.get('type') == 'input_text':
                            text = item.get('text', '')
                            if '<environment_context>' in text and '<cwd>' in text:
                                # Extract cwd from the environment context
                                start = text.find('<cwd>') + 5
                                end = text.find('</cwd>')
                                if start > 4 and end > start:
                                    return text[start:end]
            except (json.JSONDecodeError, KeyError):
                continue
        return None
    
    def _find_matching_entries(self, session_id: str) -> List[CodexEntry]:
        """Find entries in history.jsonl matching this session ID."""
        history_file = Path.home() / ".codex" / "history.jsonl"
        entries = []
        
        if not history_file.exists():
            return entries
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if data.get('session_id') == session_id:
                            entry = CodexEntry(
                                session_id=data['session_id'],
                                timestamp=data['ts'],
                                text=data['text']
                            )
                            entries.append(entry)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            print(f"Warning: Failed to read history.jsonl: {e}")
        
        # Sort by timestamp
        entries.sort(key=lambda x: x.timestamp)
        return entries
    
    def _group_sessions_by_project(self, sessions: List[CodexSession]) -> List[CodexProject]:
        """Group sessions by project based on git repository or working directory."""
        project_groups: Dict[str, List[CodexSession]] = defaultdict(list)
        
        for session in sessions:
            project_key = self._get_project_key(session)
            project_groups[project_key].append(session)
        
        projects = []
        for project_key, project_sessions in project_groups.items():
            # Determine project name and repository URL
            first_session = project_sessions[0]
            if first_session.git_info and first_session.git_info.repository_url:
                name = first_session.git_info.project_name
                repo_url = first_session.git_info.repository_url
            else:
                name = project_key
                repo_url = None
            
            # Use the most common working directory
            working_dirs = [s.working_directory for s in project_sessions if s.working_directory]
            working_directory = working_dirs[0] if working_dirs else None
            
            project = CodexProject(
                name=name,
                repository_url=repo_url,
                sessions=project_sessions,
                working_directory=working_directory
            )
            projects.append(project)
        
        # Sort projects by name
        projects.sort(key=lambda x: x.name.lower())
        return projects
    
    def _get_project_key(self, session: CodexSession) -> str:
        """Get a unique key for grouping sessions by project."""
        if session.git_info and session.git_info.repository_url:
            return session.git_info.repository_url
        
        if session.working_directory:
            # Use the directory name as project key
            return Path(session.working_directory).name
        
        return "Unknown Project"