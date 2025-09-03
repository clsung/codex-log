# Codex Log Converter Test Suite

This directory contains comprehensive tests for the Codex Log Converter project. The test suite covers all components with unit tests, integration tests, CLI tests, and edge case testing.

## Test Structure

```
tests/
├── README.md                   # This file
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest fixtures and configuration
├── run_tests.py               # Test runner script
├── unit/                      # Unit tests for individual components
│   ├── __init__.py
│   ├── test_models.py         # Data model tests
│   ├── test_parser.py         # Basic parser tests
│   ├── test_session_parser.py # Session parser tests
│   ├── test_renderer.py       # HTML renderer tests
│   └── test_edge_cases.py     # Edge cases and error handling
├── integration/               # Integration tests
│   ├── __init__.py
│   ├── test_converter.py      # End-to-end converter tests
│   └── test_cli.py           # CLI interface tests
├── fixtures/                  # Test data and utilities
│   └── sample_data.py        # Sample data generators
└── data/                     # Generated test data files
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

### Quick Start

Run all tests:
```bash
pytest
```

Or use the test runner script:
```bash
python run_tests.py
```

### Test Categories

#### Unit Tests
Test individual components in isolation:
```bash
pytest tests/unit/
# or
python run_tests.py unit
```

#### Integration Tests
Test component interactions and end-to-end workflows:
```bash
pytest tests/integration/
# or
python run_tests.py integration
```

#### CLI Tests
Test command-line interface:
```bash
pytest tests/integration/test_cli.py
# or
python run_tests.py cli
```

### Test Markers

Tests are marked with categories for selective running:

```bash
pytest -m unit           # Run only unit tests
pytest -m integration    # Run only integration tests  
pytest -m cli           # Run only CLI tests
pytest -m parser        # Run only parser tests
pytest -m renderer      # Run only renderer tests
pytest -m models        # Run only model tests
pytest -m edge_case     # Run only edge case tests
pytest -m "not slow"    # Skip slow tests
pytest -m slow          # Run only slow tests
```

### Coverage Reports

Run tests with coverage:
```bash
pytest --cov=codex_log --cov-report=html
# or
python run_tests.py coverage
```

View coverage report:
```bash
open htmlcov/index.html
```

### Parallel Execution

Run tests in parallel for speed:
```bash
pytest -n auto
# or
python run_tests.py --parallel
```

### Advanced Options

#### Verbose Output
```bash
pytest -v
# or
python run_tests.py --verbose
```

#### Stop on First Failure
```bash
pytest -x
# or
python run_tests.py --failfast
```

#### Run Specific Tests
```bash
pytest tests/unit/test_models.py::TestCodexEntry::test_create_entry
pytest tests/integration/test_converter.py -k "test_convert_basic"
```

#### Custom Markers
```bash
pytest -m "parser and not slow"
pytest -m "integration or cli"
```

## Test Data

The test suite uses several types of test data:

### Sample Data
- **Valid JSONL entries**: Realistic Codex conversation data
- **Session files**: Mock session files with git info and environment context  
- **Unicode content**: Multi-language text with emojis and special characters
- **Large datasets**: Performance testing with thousands of entries

### Edge Case Data
- **Malformed JSON**: Invalid JSON entries for error handling
- **Missing fields**: Entries with missing required fields
- **Empty files**: Zero-length and whitespace-only files
- **Encoding issues**: Different text encodings and null bytes

### Fixtures

Shared test fixtures are defined in `conftest.py`:

- `sample_entries`: Basic CodexEntry objects
- `sample_sessions`: CodexSession objects with git info
- `sample_conversation`: Complete CodexConversation
- `sample_projects`: CodexProject groupings
- `temp_dir`: Temporary directory for test files
- `template_dir`: Test HTML templates
- Various file fixtures (history.jsonl, session files, etc.)

## Writing New Tests

### Test Organization

- **Unit tests**: Test individual methods and classes in isolation
- **Integration tests**: Test component interactions and workflows  
- **CLI tests**: Use Click's testing utilities
- **Edge cases**: Focus on error handling and boundary conditions

### Test Naming

Use descriptive test names that explain what is being tested:
```python
def test_parse_valid_history_file(self):
def test_render_conversation_with_unicode_content(self):  
def test_cli_handles_missing_input_file(self):
def test_session_parser_with_malformed_git_info(self):
```

### Using Fixtures

Leverage the shared fixtures from `conftest.py`:
```python
def test_my_feature(self, sample_conversation, temp_dir):
    # Use sample_conversation and temp_dir fixtures
    pass
```

### Assertions

Use descriptive assertions:
```python
# Good
assert len(conversation.sessions) == 2
assert "Hello world" in html_output
assert session.project_name == "my-project"

# Better  
assert len(conversation.sessions) == 2, "Should have exactly 2 sessions"
assert "Hello world" in html_output, "HTML should contain entry text"
assert session.project_name == "my-project", "Project name should be extracted from git URL"
```

### Mocking

Use pytest-mock for mocking external dependencies:
```python
def test_with_mock(self, mocker):
    mock_open = mocker.patch('builtins.open', mock_open(read_data="test data"))
    # Test code that uses open()
```

## Continuous Integration

The test suite is designed to run in CI environments:

- All tests should be deterministic and not flaky
- Tests use temporary directories and cleanup after themselves
- No external dependencies or network calls in tests
- Timeouts prevent hanging tests

## Performance Considerations

- Unit tests should complete in milliseconds
- Integration tests should complete in seconds
- Mark slow tests with `@pytest.mark.slow`
- Use `pytest-xdist` for parallel execution
- Mock expensive operations in unit tests

## Debugging Tests

### Failed Test Debugging
```bash
pytest --tb=long --capture=no -v tests/path/to/test.py
```

### Interactive Debugging
```bash
pytest --pdb tests/path/to/test.py
```

### Print Debugging
```bash
pytest -s tests/path/to/test.py  # Don't capture stdout
```

## Test Coverage Goals

- **Overall coverage**: 90%+
- **Critical paths**: 100% (parsers, converters)
- **Error handling**: 100% (exception paths)
- **CLI interface**: 95%+ (all user-facing functionality)

Run coverage reports regularly to identify gaps:
```bash
python run_tests.py coverage
```