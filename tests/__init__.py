"""Test package for Codex Log Converter.

This package contains comprehensive tests for all components of the Codex Log Converter,
including unit tests, integration tests, and CLI tests.

Test Structure:
- unit/: Unit tests for individual components
  - test_models.py: Data model tests
  - test_parser.py: Basic parser tests  
  - test_session_parser.py: Session parser tests
  - test_renderer.py: HTML renderer tests
  - test_edge_cases.py: Edge cases and error handling
- integration/: Integration tests for component interactions
  - test_converter.py: End-to-end converter tests
  - test_cli.py: CLI interface tests
- fixtures/: Test data and fixtures
- conftest.py: Shared pytest configuration and fixtures

To run tests:
    pytest                          # Run all tests
    pytest tests/unit/             # Run only unit tests
    pytest tests/integration/     # Run only integration tests  
    pytest -m "not slow"          # Skip slow tests
    pytest -v --tb=short          # Verbose output with short tracebacks
    pytest --cov=codex_log        # With coverage report
"""