#!/usr/bin/env python3
"""Test runner script for Codex Log Converter.

This script provides convenient commands for running different types of tests
with appropriate configurations.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description="Running command"):
    """Run a shell command and return the result."""
    print(f"\n{description}...")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run Codex Log Converter tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "cli", "coverage", "quick", "slow"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--markers", "-m",
        help="Run tests matching given mark expression"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    # Add common options
    if args.verbose:
        base_cmd.append("-v")
    if args.parallel:
        base_cmd.extend(["-n", "auto"])
    if args.failfast:
        base_cmd.append("-x")
    if args.markers:
        base_cmd.extend(["-m", args.markers])
    
    success = True
    
    # Run different test types
    if args.test_type == "all":
        # Run all tests with coverage
        cmd = base_cmd + [
            "--cov=codex_log",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "tests/"
        ]
        success = run_command(cmd, "Running all tests with coverage")
        
    elif args.test_type == "unit":
        cmd = base_cmd + ["tests/unit/"]
        success = run_command(cmd, "Running unit tests")
        
    elif args.test_type == "integration":
        cmd = base_cmd + ["tests/integration/"]
        success = run_command(cmd, "Running integration tests")
        
    elif args.test_type == "cli":
        cmd = base_cmd + ["tests/integration/test_cli.py"]
        success = run_command(cmd, "Running CLI tests")
        
    elif args.test_type == "coverage":
        # Run with detailed coverage reporting
        cmd = base_cmd + [
            "--cov=codex_log",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=80",
            "tests/"
        ]
        success = run_command(cmd, "Running tests with coverage requirements")
        
    elif args.test_type == "quick":
        # Run only fast tests
        cmd = base_cmd + ["-m", "not slow", "tests/"]
        success = run_command(cmd, "Running quick tests")
        
    elif args.test_type == "slow":
        # Run only slow tests
        cmd = base_cmd + ["-m", "slow", "tests/"]
        success = run_command(cmd, "Running slow tests")
    
    # Run code quality checks if all tests passed
    if success and args.test_type in ["all", "coverage"]:
        print("\n" + "="*60)
        print("Running code quality checks...")
        
        # Type checking
        type_cmd = ["python", "-m", "mypy", "codex_log/"]
        run_command(type_cmd, "Running type checks")
        
        # Linting
        lint_cmd = ["python", "-m", "flake8", "codex_log/"]
        run_command(lint_cmd, "Running linting")
    
    if success:
        print(f"\n🎉 All tests passed!")
        if args.test_type in ["all", "coverage"]:
            print("📊 Coverage report generated in htmlcov/")
            print("🔍 Open htmlcov/index.html to view detailed coverage")
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()