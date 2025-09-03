"""Unit tests for Codex Log data models."""

import pytest
from datetime import datetime
from codex_log.models import CodexEntry, GitInfo, CodexSession, CodexProject, CodexConversation


@pytest.mark.unit
@pytest.mark.models
class TestCodexEntry:
    """Test cases for CodexEntry model."""
    
    def test_create_entry(self):
        """Test creating a basic CodexEntry."""
        entry = CodexEntry("session-1", 1694025600000, "Hello world")
        
        assert entry.session_id == "session-1"
        assert entry.timestamp == 1694025600000
        assert entry.text == "Hello world"
    
    def test_datetime_property(self):
        """Test timestamp to datetime conversion."""
        entry = CodexEntry("session-1", 1694025600000, "Hello")
        expected_datetime = datetime.fromtimestamp(1694025600)  # Milliseconds to seconds
        
        assert entry.datetime == expected_datetime
    
    def test_datetime_with_milliseconds(self):
        """Test datetime conversion handles milliseconds correctly."""
        # Test with milliseconds precision
        timestamp_ms = 1694025661500  # 1.5 seconds after the minute
        entry = CodexEntry("session-1", timestamp_ms, "Test")
        expected_datetime = datetime.fromtimestamp(1694025661.5)
        
        assert entry.datetime == expected_datetime


class TestGitInfo:
    """Test cases for GitInfo model."""
    
    def test_create_empty_git_info(self):
        """Test creating empty GitInfo."""
        git_info = GitInfo()
        
        assert git_info.repository_url is None
        assert git_info.branch is None
        assert git_info.commit_hash is None
        assert git_info.project_name == "Unknown Project"
    
    def test_create_full_git_info(self):
        """Test creating GitInfo with all fields."""
        git_info = GitInfo(
            repository_url="https://github.com/user/repo.git",
            branch="main",
            commit_hash="abc123"
        )
        
        assert git_info.repository_url == "https://github.com/user/repo.git"
        assert git_info.branch == "main"
        assert git_info.commit_hash == "abc123"
    
    @pytest.mark.parametrize("url,expected_name", [
        ("https://github.com/user/awesome-project.git", "awesome-project"),
        ("git@github.com:user/my-tool.git", "my-tool"),
        ("https://gitlab.com/team/web-app.git", "web-app"),
        ("https://github.com/user/repo", "repo"),
        ("git@bitbucket.org:company/service.git", "service"),
        (None, "Unknown Project"),
        ("", "Unknown Project"),
    ])
    def test_project_name_extraction(self, url, expected_name):
        """Test project name extraction from various URL formats."""
        git_info = GitInfo(repository_url=url)
        assert git_info.project_name == expected_name
    
    def test_project_name_edge_cases(self):
        """Test project name extraction edge cases."""
        # URL without .git extension
        git_info = GitInfo(repository_url="https://github.com/user/project")
        assert git_info.project_name == "project"
        
        # Complex path
        git_info = GitInfo(repository_url="https://git.company.com/team/group/project.git")
        assert git_info.project_name == "project"


class TestCodexSession:
    """Test cases for CodexSession model."""
    
    def test_create_basic_session(self, sample_entries):
        """Test creating a basic session."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession("session-1", session_entries)
        
        assert session.session_id == "session-1"
        assert len(session.entries) == 3
        assert session.working_directory is None
        assert session.git_info is None
        assert session.instructions is None
    
    def test_create_full_session(self, sample_entries, sample_git_info):
        """Test creating a session with all fields."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession(
            session_id="session-1",
            entries=session_entries,
            working_directory="/home/user/project",
            git_info=sample_git_info,
            instructions="You are helpful"
        )
        
        assert session.session_id == "session-1"
        assert session.working_directory == "/home/user/project"
        assert session.git_info == sample_git_info
        assert session.instructions == "You are helpful"
    
    def test_start_time_property(self, sample_entries):
        """Test start_time property calculation."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession("session-1", session_entries)
        
        expected_start = min(entry.datetime for entry in session_entries)
        assert session.start_time == expected_start
    
    def test_end_time_property(self, sample_entries):
        """Test end_time property calculation."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession("session-1", session_entries)
        
        expected_end = max(entry.datetime for entry in session_entries)
        assert session.end_time == expected_end
    
    def test_empty_session_times(self):
        """Test time properties with empty entries."""
        session = CodexSession("session-1", [])
        
        # Both should return current time (approximately)
        now = datetime.now()
        assert abs((session.start_time - now).total_seconds()) < 1
        assert abs((session.end_time - now).total_seconds()) < 1
    
    def test_project_name_from_git_info(self, sample_entries, sample_git_info):
        """Test project name extraction from git info."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession("session-1", session_entries, git_info=sample_git_info)
        
        assert session.project_name == "awesome-project"
    
    def test_project_name_from_working_directory(self, sample_entries):
        """Test project name extraction from working directory."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession(
            "session-1", 
            session_entries, 
            working_directory="/home/user/my-awesome-project"
        )
        
        assert session.project_name == "my-awesome-project"
    
    def test_project_name_priority(self, sample_entries, sample_git_info):
        """Test that git info takes priority over working directory for project name."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession(
            "session-1",
            session_entries,
            working_directory="/home/user/different-project",
            git_info=sample_git_info
        )
        
        # Git info should take priority
        assert session.project_name == "awesome-project"
    
    def test_project_name_unknown_fallback(self, sample_entries):
        """Test project name fallback to 'Unknown Project'."""
        session_entries = [e for e in sample_entries if e.session_id == "session-1"]
        session = CodexSession("session-1", session_entries)
        
        assert session.project_name == "Unknown Project"


class TestCodexProject:
    """Test cases for CodexProject model."""
    
    def test_create_project(self, sample_sessions):
        """Test creating a CodexProject."""
        project_sessions = [s for s in sample_sessions if s.project_name == "awesome-project"]
        project = CodexProject(
            name="awesome-project",
            repository_url="https://github.com/user/awesome-project.git",
            sessions=project_sessions
        )
        
        assert project.name == "awesome-project"
        assert project.repository_url == "https://github.com/user/awesome-project.git"
        assert len(project.sessions) == 1
        assert project.working_directory is None
    
    def test_total_entries_property(self, sample_sessions):
        """Test total_entries calculation across sessions."""
        project = CodexProject(
            name="test-project",
            repository_url=None,
            sessions=sample_sessions
        )
        
        expected_total = sum(len(session.entries) for session in sample_sessions)
        assert project.total_entries == expected_total
    
    def test_total_entries_empty_sessions(self):
        """Test total_entries with no sessions."""
        project = CodexProject(
            name="empty-project",
            repository_url=None,
            sessions=[]
        )
        
        assert project.total_entries == 0
    
    def test_date_range_property(self, sample_sessions):
        """Test date_range calculation across sessions."""
        project = CodexProject(
            name="test-project",
            repository_url=None,
            sessions=sample_sessions
        )
        
        expected_start = min(session.start_time for session in sample_sessions)
        expected_end = max(session.end_time for session in sample_sessions)
        
        start, end = project.date_range
        assert start == expected_start
        assert end == expected_end
    
    def test_date_range_empty_sessions(self):
        """Test date_range with no sessions."""
        project = CodexProject(
            name="empty-project",
            repository_url=None,
            sessions=[]
        )
        
        start, end = project.date_range
        now = datetime.now()
        
        # Both should be approximately now
        assert abs((start - now).total_seconds()) < 1
        assert abs((end - now).total_seconds()) < 1


class TestCodexConversation:
    """Test cases for CodexConversation model."""
    
    def test_create_basic_conversation(self, sample_sessions):
        """Test creating a basic conversation."""
        conversation = CodexConversation(sessions=sample_sessions)
        
        assert len(conversation.sessions) == len(sample_sessions)
        assert conversation.projects is None
        assert not conversation.has_projects
    
    def test_create_conversation_with_projects(self, sample_sessions, sample_projects):
        """Test creating a conversation with projects."""
        conversation = CodexConversation(sessions=sample_sessions, projects=sample_projects)
        
        assert len(conversation.sessions) == len(sample_sessions)
        assert len(conversation.projects) == len(sample_projects)
        assert conversation.has_projects
    
    def test_total_entries_property(self, sample_sessions):
        """Test total_entries calculation."""
        conversation = CodexConversation(sessions=sample_sessions)
        
        expected_total = sum(len(session.entries) for session in sample_sessions)
        assert conversation.total_entries == expected_total
    
    def test_total_entries_empty_sessions(self):
        """Test total_entries with no sessions."""
        conversation = CodexConversation(sessions=[])
        
        assert conversation.total_entries == 0
    
    def test_has_projects_property(self, sample_sessions, sample_projects):
        """Test has_projects property in various scenarios."""
        # No projects
        conversation1 = CodexConversation(sessions=sample_sessions)
        assert not conversation1.has_projects
        
        # Empty projects list
        conversation2 = CodexConversation(sessions=sample_sessions, projects=[])
        assert not conversation2.has_projects
        
        # With projects
        conversation3 = CodexConversation(sessions=sample_sessions, projects=sample_projects)
        assert conversation3.has_projects