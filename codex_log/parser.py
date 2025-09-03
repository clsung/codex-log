"""Parser for Codex JSONL log files."""

import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from .models import CodexEntry, CodexSession, CodexConversation


class CodexParser:
    """Parser for Codex history.jsonl files."""
    
    def parse_file(self, file_path: Path) -> CodexConversation:
        """Parse a Codex JSONL file into a CodexConversation object."""
        entries = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    entry = self._parse_entry(data)
                    if entry:
                        entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
        
        # Group entries by session_id
        sessions_dict: Dict[str, List[CodexEntry]] = defaultdict(list)
        for entry in entries:
            sessions_dict[entry.session_id].append(entry)
        
        # Create CodexSession objects
        sessions = []
        for session_id, session_entries in sessions_dict.items():
            # Sort entries by timestamp within each session
            session_entries.sort(key=lambda x: x.timestamp)
            sessions.append(CodexSession(session_id=session_id, entries=session_entries))
        
        # Sort sessions by start time
        sessions.sort(key=lambda x: x.start_time)
        
        return CodexConversation(sessions=sessions)
    
    def _parse_entry(self, data: dict) -> CodexEntry:
        """Parse a single JSON object into a CodexEntry."""
        try:
            return CodexEntry(
                session_id=data['session_id'],
                timestamp=data['ts'],
                text=data['text']
            )
        except KeyError as e:
            print(f"Warning: Missing required field {e} in entry")
            return None