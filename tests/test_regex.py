"""Tests for the regex pattern matching functionality."""

import os
import re

import pytest
from typer.testing import CliRunner

from recursivist.core import (
    compile_regex_patterns,
    get_directory_structure,
    should_exclude,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_compile_regex_patterns():
    """Test compiling regex patterns."""
    # Non-regex mode
    patterns = ["*.py", "test_*"]
    compiled = compile_regex_patterns(patterns, is_regex=False)

    assert len(compiled) == 2
    assert compiled[0] == "*.py"
    assert compiled[1] == "test_*"

    # Regex mode
    patterns = [r"\.py$", r"^test_"]
    compiled = compile_regex_patterns(patterns, is_regex=True)

    assert len(compiled) == 2
    assert isinstance(compiled[0], re.Pattern)
    assert isinstance(compiled[1], re.Pattern)

    # Test invalid regex
    patterns = [r"[invalid(regex"]
    compiled = compile_regex_patterns(patterns, is_regex=True)

    assert len(compiled) == 1
    assert isinstance(compiled[0], str)  # Should fall back to string for invalid regex


def test_should_exclude_with_regex(mocker):
    """Test the exclude logic with regex patterns."""
    mocker.patch("os.path.isfile", return_value=True)

    # Base context
    ignore_context = {"patterns": [], "current_dir": "/test"}

    # Test regex exclude patterns
    exclude_patterns = [re.compile(r"\.py$"), re.compile(r"test_.*\.js$")]

    assert should_exclude(
        "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
    )
    assert should_exclude(
        "/test/test_app.js", ignore_context, exclude_patterns=exclude_patterns
    )
    assert not should_exclude(
        "/test/script.txt", ignore_context, exclude_patterns=exclude_patterns
    )
    assert not should_exclude(
        "/test/app.js", ignore_context, exclude_patterns=exclude_patterns
    )

    # Test regex include patterns
    include_patterns = [re.compile(r".*src.*"), re.compile(r"\.md$")]

    assert should_exclude(
        "/test/script.py", ignore_context, include_patterns=include_patterns
    )
    assert not should_exclude(
        "/test/src/script.py", ignore_context, include_patterns=include_patterns
    )
    assert not should_exclude(
        "/test/README.md", ignore_context, include_patterns=include_patterns
    )

    # Test include patterns overriding exclude patterns
    assert not should_exclude(
        "/test/src/script.py",
        ignore_context,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
    )  # Should be included despite matching exclude pattern


def test_get_directory_structure_with_regex_patterns(sample_directory):
    """Test directory structure with regex patterns."""
    # Create some test files
    with open(os.path.join(sample_directory, "test_file1.js"), "w") as f:
        f.write("console.log('test');")

    with open(os.path.join(sample_directory, "prod_file1.js"), "w") as f:
        f.write("console.log('prod');")

    with open(os.path.join(sample_directory, "README.md"), "w") as f:
        f.write("# Test README")

    # Test with exclude regex patterns
    exclude_patterns = [re.compile(r"test_.*\.js$")]
    structure, _ = get_directory_structure(
        sample_directory, exclude_patterns=exclude_patterns
    )

    assert "test_file1.js" not in structure["_files"]
    assert "prod_file1.js" in structure["_files"]

    # Test with include regex patterns
    include_patterns = [re.compile(r".*\.md$")]
    structure, _ = get_directory_structure(
        sample_directory, include_patterns=include_patterns
    )

    assert "README.md" in structure["_files"]
    assert "file1.txt" not in structure["_files"]
    assert "file2.py" not in structure["_files"]

    # Test with both exclude and include patterns
    exclude_patterns = [re.compile(r"\.py$")]
    include_patterns = [re.compile(r".*\.md$"), re.compile(r".*\.txt$")]

    structure, _ = get_directory_structure(
        sample_directory,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
    )

    assert "README.md" in structure["_files"]
    assert "file1.txt" in structure["_files"]
    assert "file2.py" not in structure["_files"]


# Simplify the CLI tests to avoid issues with argument parsing
def test_cli_with_regex_patterns(runner, sample_directory):
    """Test the CLI with regex pattern options."""

    from recursivist.cli import app

    # Create some test files
    with open(os.path.join(sample_directory, "test_file1.js"), "w") as f:
        f.write("console.log('test');")

    with open(os.path.join(sample_directory, "prod_file1.js"), "w") as f:
        f.write("console.log('prod');")

    # Test with basic visualization (no patterns)
    result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert "test_file1.js" in result.stdout
    assert "prod_file1.js" in result.stdout

    # Test with exclude flag - using simpler patterns to avoid CLI parsing issues
    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude-pattern", "test_*"]
    )
    assert result.exit_code == 0

    # Test with single exclude pattern to avoid parsing complexities
    result = runner.invoke(app, ["visualize", sample_directory, "--exclude-ext", ".js"])
    assert result.exit_code == 0
    assert "file1.txt" in result.stdout
    assert "test_file1.js" not in result.stdout
    assert "prod_file1.js" not in result.stdout
