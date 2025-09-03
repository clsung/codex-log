"""Data models for Codex conversations."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path


@dataclass
class CodexEntry:
    """A single entry from Codex history.jsonl."""
    session_id: str
    timestamp: int
    text: str
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp / 1000)  # Convert from milliseconds


@dataclass
class GitInfo:
    """Git repository information from Codex session."""
    repository_url: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    
    @property
    def project_name(self) -> str:
        """Extract project name from repository URL."""
        if not self.repository_url:
            return "Unknown Project"
        # Extract from git@github.com:user/repo.git or https://github.com/user/repo.git
        if self.repository_url.endswith('.git'):
            return self.repository_url.split('/')[-1][:-4]  # Remove .git
        return self.repository_url.split('/')[-1]


@dataclass
class CodexSession:
    """A group of Codex entries from the same session."""
    session_id: str
    entries: List[CodexEntry]
    working_directory: Optional[str] = None
    git_info: Optional[GitInfo] = None
    instructions: Optional[str] = None
    
    @property
    def start_time(self) -> datetime:
        """Get the start time of this session."""
        if not self.entries:
            return datetime.now()
        return min(entry.datetime for entry in self.entries)
    
    @property
    def end_time(self) -> datetime:
        """Get the end time of this session."""
        if not self.entries:
            return datetime.now()
        return max(entry.datetime for entry in self.entries)
    
    @property
    def project_name(self) -> str:
        """Get project name from git info or working directory."""
        if self.git_info and self.git_info.project_name != "Unknown Project":
            return self.git_info.project_name
        if self.working_directory:
            return Path(self.working_directory).name
        return "Unknown Project"


@dataclass
class CodexProject:
    """A project grouping of Codex sessions."""
    name: str
    repository_url: Optional[str]
    sessions: List[CodexSession]
    working_directory: Optional[str] = None
    
    @property
    def total_entries(self) -> int:
        """Total number of entries across all sessions in this project."""
        return sum(len(session.entries) for session in self.sessions)
    
    @property
    def date_range(self) -> tuple[datetime, datetime]:
        """Start and end dates for this project."""
        if not self.sessions:
            now = datetime.now()
            return now, now
        start = min(session.start_time for session in self.sessions)
        end = max(session.end_time for session in self.sessions)
        return start, end


@dataclass  
class CodexConversation:
    """Collection of all Codex sessions, optionally grouped by projects."""
    sessions: List[CodexSession]
    projects: Optional[List[CodexProject]] = None
    
    @property
    def total_entries(self) -> int:
        """Total number of entries across all sessions."""
        return sum(len(session.entries) for session in self.sessions)
    
    @property
    def has_projects(self) -> bool:
        """Whether this conversation has project groupings."""
        return self.projects is not None and len(self.projects) > 0