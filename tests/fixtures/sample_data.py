"""Sample data for testing Codex Log Converter."""

import json
from datetime import datetime, timedelta
from pathlib import Path


# Sample history.jsonl entries
SAMPLE_HISTORY_ENTRIES = [
    {
        "session_id": "session-python-help-001",
        "ts": 1694025600000,  # 2023-09-06 20:00:00
        "text": "I need help with Python file parsing. Can you help me read a CSV file?"
    },
    {
        "session_id": "session-python-help-001", 
        "ts": 1694025660000,  # 2023-09-06 20:01:00
        "text": "Here's my current code:\n\nimport csv\n\nwith open('data.csv', 'r') as f:\n    reader = csv.reader(f)\n    for row in reader:\n        print(row)"
    },
    {
        "session_id": "session-python-help-001",
        "ts": 1694025720000,  # 2023-09-06 20:02:00
        "text": "Thank you! That works perfectly. Can you also show me how to handle errors?"
    },
    {
        "session_id": "session-web-scraper-002",
        "ts": 1694026800000,  # 2023-09-06 20:20:00
        "text": "I'm building a web scraper with Python requests. How do I handle rate limiting?"
    },
    {
        "session_id": "session-web-scraper-002",
        "ts": 1694026860000,  # 2023-09-06 20:21:00
        "text": "I'm getting 429 errors when I make too many requests. Should I use time.sleep()?"
    },
    {
        "session_id": "session-web-scraper-002", 
        "ts": 1694026920000,  # 2023-09-06 20:22:00
        "text": "Perfect! I'll implement exponential backoff. Here's what I have now:\n\nimport requests\nimport time\nimport random\n\ndef make_request_with_backoff(url, max_retries=3):\n    for attempt in range(max_retries):\n        try:\n            response = requests.get(url)\n            if response.status_code == 429:\n                wait_time = (2 ** attempt) + random.uniform(0, 1)\n                time.sleep(wait_time)\n                continue\n            return response\n        except requests.RequestException as e:\n            if attempt == max_retries - 1:\n                raise e\n            time.sleep(2 ** attempt)\n    return None"
    },
    {
        "session_id": "session-react-debug-003",
        "ts": 1694112000000,  # 2023-09-07 19:40:00
        "text": "I'm having trouble with React state not updating. Can you help debug this component?"
    },
    {
        "session_id": "session-react-debug-003",
        "ts": 1694112060000,  # 2023-09-07 19:41:00
        "text": "```jsx\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  \n  const increment = () => {\n    setCount(count + 1);\n    setCount(count + 1); // This doesn't work as expected\n  };\n  \n  return (\n    <div>\n      <p>Count: {count}</p>\n      <button onClick={increment}>Increment</button>\n    </div>\n  );\n}\n```"
    },
    {
        "session_id": "session-react-debug-003",
        "ts": 1694112120000,  # 2023-09-07 19:42:00
        "text": "Ah, I see! The issue is that state updates are batched and `count` doesn't change immediately. I should use the functional update pattern:\n\n```jsx\nconst increment = () => {\n  setCount(prev => prev + 1);\n  setCount(prev => prev + 1);\n};\n```\n\nThanks for explaining React's state batching!"
    }
]

# Sample session file data
SAMPLE_SESSION_DATA = {
    "session-python-help-001": {
        "metadata": {
            "id": "session-python-help-001",
            "git": {
                "repository_url": "https://github.com/user/data-processing-tools.git",
                "branch": "main", 
                "commit_hash": "abc123def456789"
            },
            "instructions": "You are a helpful Python programming assistant."
        },
        "messages": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "input_text",
                        "text": "<environment_context>\n<cwd>/home/user/projects/data-processing-tools</cwd>\n<platform>Linux</platform>\n</environment_context>\n\nI need help with Python file parsing."
                    }
                ]
            }
        ]
    },
    "session-web-scraper-002": {
        "metadata": {
            "id": "session-web-scraper-002",
            "git": {
                "repository_url": "git@github.com:user/web-scraper-toolkit.git",
                "branch": "feature/rate-limiting",
                "commit_hash": "def456abc789123"
            },
            "instructions": "You are an expert in web scraping and API interactions."
        },
        "messages": [
            {
                "type": "message", 
                "content": [
                    {
                        "type": "input_text",
                        "text": "<environment_context>\n<cwd>/home/user/projects/web-scraper-toolkit</cwd>\n<platform>Linux</platform>\n</environment_context>\n\nI'm building a web scraper with Python requests."
                    }
                ]
            }
        ]
    },
    "session-react-debug-003": {
        "metadata": {
            "id": "session-react-debug-003",
            "git": {
                "repository_url": "https://github.com/company/react-dashboard.git", 
                "branch": "bugfix/counter-component",
                "commit_hash": "789abc123def456"
            },
            "instructions": "You are a React.js expert who helps debug frontend issues."
        },
        "messages": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "input_text", 
                        "text": "<environment_context>\n<cwd>/home/user/projects/react-dashboard</cwd>\n<platform>Linux</platform>\n</environment_context>\n\nI'm having trouble with React state not updating."
                    }
                ]
            }
        ]
    }
}

# Edge case data for testing error handling
MALFORMED_ENTRIES = [
    '{"session_id": "valid", "ts": 1694025600000, "text": "This is valid"}',
    '{"session_id": "missing-ts", "text": "Missing timestamp field"}',  # Missing ts
    '{"session_id": "invalid-json", "ts": 1694025600000, "text": "Broken JSON"',  # Missing closing brace
    '',  # Empty line
    '   ',  # Whitespace only
    '{"ts": 1694025600000, "text": "Missing session_id"}',  # Missing session_id
    '{"session_id": "valid2", "ts": 1694025660000, "text": "Another valid entry"}',
]

# Unicode test data
UNICODE_ENTRIES = [
    {
        "session_id": "unicode-test",
        "ts": 1694025600000,
        "text": "Hello 🌍! This is a test with emojis 🚀 and unicode characters: café, naïve, résumé"
    },
    {
        "session_id": "unicode-test", 
        "ts": 1694025660000,
        "text": "Mathematical symbols: ∑ ∏ ∫ √ ∞ ≠ ≤ ≥ ± and Greek: α β γ δ ε ζ η θ ι κ λ μ"
    },
    {
        "session_id": "unicode-test",
        "ts": 1694025720000,
        "text": "Chinese: 你好世界, Japanese: こんにちは, Korean: 안녕하세요, Russian: Привет мир"
    }
]


def create_sample_history_file(file_path: Path) -> None:
    """Create a sample history.jsonl file for testing."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in SAMPLE_HISTORY_ENTRIES:
            f.write(json.dumps(entry) + '\n')


def create_malformed_history_file(file_path: Path) -> None:
    """Create a malformed history.jsonl file for testing error handling."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in MALFORMED_ENTRIES:
            f.write(entry + '\n')


def create_unicode_history_file(file_path: Path) -> None:
    """Create a history.jsonl file with unicode content for testing."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for entry in UNICODE_ENTRIES:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def create_sample_session_files(session_dir: Path) -> None:
    """Create sample session files for testing."""
    session_dir.mkdir(exist_ok=True)
    
    for session_id, session_data in SAMPLE_SESSION_DATA.items():
        session_file = session_dir / f"{session_id}.jsonl"
        
        with open(session_file, 'w', encoding='utf-8') as f:
            # Write metadata first
            f.write(json.dumps(session_data["metadata"]) + '\n')
            
            # Write messages
            for message in session_data["messages"]:
                f.write(json.dumps(message) + '\n')


def create_large_test_file(file_path: Path, num_sessions: int = 100, entries_per_session: int = 50) -> None:
    """Create a large test file for performance testing."""
    base_time = int(datetime.now().timestamp() * 1000)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for session_idx in range(num_sessions):
            session_id = f"large-test-session-{session_idx:03d}"
            
            for entry_idx in range(entries_per_session):
                timestamp = base_time + (session_idx * entries_per_session + entry_idx) * 60000  # 1 minute apart
                text = f"Entry {entry_idx + 1} in session {session_idx + 1}. This is some sample text content that simulates a real conversation entry with various details and information."
                
                entry = {
                    "session_id": session_id,
                    "ts": timestamp,
                    "text": text
                }
                
                f.write(json.dumps(entry) + '\n')