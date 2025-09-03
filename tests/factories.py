"""Test data factories using factory-boy for maintainable test data generation."""

from __future__ import annotations

import factory
import factory.fuzzy
from datetime import datetime, timedelta
from typing import List

from codex_log.models import CodexEntry, CodexSession, CodexConversation, GitInfo, CodexProject


class GitInfoFactory(factory.Factory):
    """Factory for GitInfo objects."""
    
    class Meta:
        model = GitInfo
    
    repository_url = factory.Faker(
        'random_element', 
        elements=[
            'https://github.com/user/project.git',
            'git@github.com:user/project.git',
            'https://gitlab.com/user/project.git',
            'git@gitlab.com:user/project.git'
        ]
    )
    branch = factory.Faker('random_element', elements=['main', 'master', 'development', 'feature/test'])
    commit_hash = factory.Faker('sha1')


class CodexEntryFactory(factory.Factory):
    """Factory for CodexEntry objects."""
    
    class Meta:
        model = CodexEntry
    
    session_id = factory.Faker('uuid4')
    timestamp = factory.fuzzy.FuzzyInteger(
        low=int((datetime.now() - timedelta(days=30)).timestamp() * 1000),
        high=int(datetime.now().timestamp() * 1000)
    )
    text = factory.Faker('paragraph', nb_sentences=3)
    
    @factory.lazy_attribute
    def session_id(self):
        """Generate session ID that can be shared across entries."""
        return f"session-{factory.Faker('random_int', min=1, max=10).evaluate(None, None, {})}"


class CodexSessionFactory(factory.Factory):
    """Factory for CodexSession objects."""
    
    class Meta:
        model = CodexSession
    
    session_id = factory.Faker('uuid4')
    entries = factory.SubFactory(CodexEntryFactory)
    git_info = factory.SubFactory(GitInfoFactory)
    working_directory = factory.Faker('file_path', depth=3)
    instructions = factory.Faker('paragraph', nb_sentences=5)
    
    @factory.post_generation
    def create_entries(self, create, extracted, **kwargs):
        """Create multiple entries for the session."""
        if not create:
            return
            
        # Ensure entries have the same session_id
        num_entries = extracted or factory.fuzzy.FuzzyInteger(2, 8).fuzz()
        base_timestamp = int((datetime.now() - timedelta(hours=2)).timestamp() * 1000)
        
        entries = []
        for i in range(num_entries):
            entry = CodexEntryFactory.build(
                session_id=self.session_id,
                timestamp=base_timestamp + (i * 60000)  # 1 minute apart
            )
            entries.append(entry)
        
        self.entries = entries


class CodexProjectFactory(factory.Factory):
    """Factory for CodexProject objects."""
    
    class Meta:
        model = CodexProject
    
    name = factory.Faker('word')
    repository_url = factory.LazyAttribute(lambda obj: f"https://github.com/user/{obj.name}.git")
    working_directory = factory.LazyAttribute(lambda obj: f"/Users/user/projects/{obj.name}")
    
    @factory.post_generation
    def create_sessions(self, create, extracted, **kwargs):
        """Create multiple sessions for the project."""
        if not create:
            return
            
        num_sessions = extracted or factory.fuzzy.FuzzyInteger(1, 5).fuzz()
        sessions = []
        
        for i in range(num_sessions):
            # Create git info that matches the project
            git_info = GitInfoFactory.build(
                repository_url=self.repository_url,
                branch='main'
            )
            
            session = CodexSessionFactory.build(
                git_info=git_info,
                working_directory=self.working_directory,
                create_entries=factory.fuzzy.FuzzyInteger(2, 6).fuzz()
            )
            sessions.append(session)
        
        self.sessions = sessions


class CodexConversationFactory(factory.Factory):
    """Factory for CodexConversation objects."""
    
    class Meta:
        model = CodexConversation
    
    @factory.post_generation  
    def create_sessions_and_projects(self, create, extracted, **kwargs):
        """Create sessions and optionally group into projects."""
        if not create:
            return
            
        # Create standalone sessions
        num_sessions = factory.fuzzy.FuzzyInteger(5, 15).fuzz()
        sessions = [CodexSessionFactory.build() for _ in range(num_sessions)]
        self.sessions = sessions
        
        # Optionally create project groupings
        create_projects = kwargs.get('with_projects', True)
        if create_projects:
            num_projects = factory.fuzzy.FuzzyInteger(2, 4).fuzz()
            projects = [CodexProjectFactory.build() for _ in range(num_projects)]
            
            # Add project sessions to main session list
            for project in projects:
                self.sessions.extend(project.sessions)
                
            self.projects = projects
        else:
            self.projects = None


# Specialized factories for specific test scenarios
class LargeDatasetFactory(factory.Factory):
    """Factory for large dataset testing."""
    
    class Meta:
        model = CodexConversation
    
    @factory.post_generation
    def create_large_dataset(self, create, extracted, **kwargs):
        """Create large dataset for performance testing."""
        if not create:
            return
            
        num_sessions = kwargs.get('num_sessions', 100)
        entries_per_session = kwargs.get('entries_per_session', 50)
        
        sessions = []
        base_timestamp = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        
        for session_idx in range(num_sessions):
            session_id = f"large-session-{session_idx:04d}"
            
            entries = []
            for entry_idx in range(entries_per_session):
                timestamp = base_timestamp + (session_idx * entries_per_session + entry_idx) * 60000
                entry = CodexEntry(
                    session_id=session_id,
                    timestamp=timestamp,
                    text=f"Large dataset test message {entry_idx} in session {session_idx}"
                )
                entries.append(entry)
                
            session = CodexSession(
                session_id=session_id,
                entries=entries,
                git_info=GitInfoFactory.build() if session_idx % 3 == 0 else None,
                working_directory=f"/test/project-{session_idx % 5}"
            )
            sessions.append(session)
            
        self.sessions = sessions
        self.projects = None


class EdgeCaseFactory:
    """Factory for edge case test data."""
    
    @staticmethod
    def empty_conversation() -> CodexConversation:
        """Create conversation with no sessions."""
        return CodexConversation(sessions=[], projects=None)
    
    @staticmethod
    def session_with_no_entries() -> CodexSession:
        """Create session with empty entries list."""
        return CodexSession(
            session_id="empty-session",
            entries=[],
            git_info=None,
            working_directory=None
        )
    
    @staticmethod
    def malformed_git_info() -> GitInfo:
        """Create git info with edge case values."""
        return GitInfo(
            repository_url="not-a-valid-url",
            branch="",
            commit_hash=None
        )
    
    @staticmethod
    def unicode_heavy_entry() -> CodexEntry:
        """Create entry with unicode and special characters."""
        return CodexEntry(
            session_id="unicode-session",
            timestamp=int(datetime.now().timestamp() * 1000),
            text="Testing unicode: 测试 🚀 émojis and spécial charactèrs ñoña"
        )
    
    @staticmethod
    def extreme_timestamps() -> List[CodexEntry]:
        """Create entries with extreme timestamp values."""
        return [
            CodexEntry("extreme-session", 0, "Epoch start"),
            CodexEntry("extreme-session", 2147483647000, "Near max 32-bit timestamp"),
            CodexEntry("extreme-session", int(datetime(2099, 12, 31).timestamp() * 1000), "Future date")
        ]


# Convenient builder functions
def build_sample_conversation(num_sessions: int = 5, with_projects: bool = True) -> CodexConversation:
    """Build a sample conversation with specified parameters."""
    return CodexConversationFactory.build(with_projects=with_projects)


def build_test_project(name: str, num_sessions: int = 3) -> CodexProject:
    """Build a test project with specified parameters."""
    return CodexProjectFactory.build(name=name, create_sessions=num_sessions)


def build_session_with_git(repo_url: str, branch: str = "main") -> CodexSession:
    """Build a session with specific git information."""
    git_info = GitInfo(repository_url=repo_url, branch=branch, commit_hash="abc123")
    return CodexSessionFactory.build(git_info=git_info)