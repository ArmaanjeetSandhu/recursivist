"""
Integration tests for the Recursivist directory visualization tool.

This module contains tests that verify multiple features working together correctly. These tests combine various functionalities like filtering, exporting, comparison, and visualization to ensure they work together as expected in real-world scenarios.
"""

import json
import os
import re

import pytest
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.compare import (
    compare_directory_structures,
    export_comparison,
)
from recursivist.core import (
    export_structure,
    get_directory_structure,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def complex_directory(temp_dir):
    """
    Create a complex directory structure for testing multiple features together.

    Structure:
    temp_dir/
    ├── .gitignore
    ├── .env
    ├── README.md
    ├── setup.py
    ├── requirements.txt
    ├── docs/
    │   ├── index.md
    │   ├── api.md
    │   └── assets/
    │       ├── logo.png
    │       └── diagram.svg
    ├── src/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── utils/
    │   │   ├── __init__.py
    │   │   └── helpers.py
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_main.py
    │       └── test_utils.py
    ├── build/
    │   ├── lib/
    │   │   └── compiled.so
    │   └── temp/
    │       └── cache.tmp
    └── dist/
        ├── project-1.0.0.tar.gz
        └── project-1.0.0-py3-none-any.whl
    """
    with open(os.path.join(temp_dir, ".gitignore"), "w") as f:
        f.write("*.pyc\n__pycache__/\n*.so\n*.tmp\nbuild/\ndist/\n")
    with open(os.path.join(temp_dir, ".env"), "w") as f:
        f.write("SECRET_KEY=test_key\nDEBUG=True\n")
    with open(os.path.join(temp_dir, "README.md"), "w") as f:
        f.write("# Test Project\nThis is a test project for integration testing.\n")
    with open(os.path.join(temp_dir, "setup.py"), "w") as f:
        f.write(
            "from setuptools import setup\nsetup(name='test-project', version='1.0.0')\n"
        )
    with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
        f.write("pytest>=7.0.0\ntyper>=0.4.0\nrich>=12.0.0\n")
    docs_dir = os.path.join(temp_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "index.md"), "w") as f:
        f.write("# Documentation\nWelcome to the documentation.\n")
    with open(os.path.join(docs_dir, "api.md"), "w") as f:
        f.write("# API Reference\nThis is the API reference.\n")
    assets_dir = os.path.join(docs_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "logo.png"), "w") as f:
        f.write("PNG CONTENT")
    with open(os.path.join(assets_dir, "diagram.svg"), "w") as f:
        f.write("<svg>SVG CONTENT</svg>")
    src_dir = os.path.join(temp_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, "__init__.py"), "w") as f:
        f.write("# This file is intentionally left empty\n")
    with open(os.path.join(src_dir, "main.py"), "w") as f:
        f.write(
            "def main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()\n"
        )
    utils_dir = os.path.join(src_dir, "utils")
    os.makedirs(utils_dir, exist_ok=True)
    with open(os.path.join(utils_dir, "__init__.py"), "w") as f:
        f.write("# This file is intentionally left empty\n")
    with open(os.path.join(utils_dir, "helpers.py"), "w") as f:
        f.write("def helper_function():\n    return 'Helper function called'\n")
    tests_dir = os.path.join(src_dir, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
        f.write("# This file is intentionally left empty\n")
    with open(os.path.join(tests_dir, "test_main.py"), "w") as f:
        f.write("def test_main():\n    assert True\n")
    with open(os.path.join(tests_dir, "test_utils.py"), "w") as f:
        f.write("def test_helpers():\n    assert True\n")
    build_dir = os.path.join(temp_dir, "build")
    lib_dir = os.path.join(build_dir, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    with open(os.path.join(lib_dir, "compiled.so"), "w") as f:
        f.write("BINARY CONTENT")
    temp_build_dir = os.path.join(build_dir, "temp")
    os.makedirs(temp_build_dir, exist_ok=True)
    with open(os.path.join(temp_build_dir, "cache.tmp"), "w") as f:
        f.write("CACHE CONTENT")
    dist_dir = os.path.join(temp_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    with open(os.path.join(dist_dir, "project-1.0.0.tar.gz"), "w") as f:
        f.write("TAR CONTENT")
    with open(os.path.join(dist_dir, "project-1.0.0-py3-none-any.whl"), "w") as f:
        f.write("WHEEL CONTENT")
    return temp_dir


@pytest.fixture
def complex_directory_clone(complex_directory, temp_dir):
    """Create a slightly modified clone of the complex directory for comparison testing."""
    clone_dir = os.path.join(os.path.dirname(temp_dir), "complex_clone")
    if os.path.exists(clone_dir):
        import shutil

        shutil.rmtree(clone_dir)
    os.makedirs(clone_dir, exist_ok=True)
    files_to_copy = [
        ".gitignore",
        "README.md",
        "setup.py",
        "requirements.txt",
    ]
    for file in files_to_copy:
        with open(os.path.join(complex_directory, file), "r") as src:
            content = src.read()
            with open(os.path.join(clone_dir, file), "w") as dst:
                dst.write(content)
    with open(os.path.join(clone_dir, "CHANGELOG.md"), "w") as f:
        f.write("# Changelog\n\n## 1.0.0\n- Initial release\n")
    src_dir = os.path.join(clone_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, "__init__.py"), "w") as f:
        f.write("# This file is intentionally left empty\n")
    with open(os.path.join(src_dir, "main.py"), "w") as f:
        f.write(
            "def main():\n    print('Hello, world - changed!')\n\nif __name__ == '__main__':\n    main()\n"
        )
    docs_dir = os.path.join(clone_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "index.md"), "w") as f:
        f.write("# Documentation\nWelcome to the updated documentation.\n")
    return clone_dir


def test_cli_with_complex_structure(runner, complex_directory, output_dir):
    """
    Test the CLI with a complex directory structure, combining multiple options.

    This test verifies that the CLI can handle a complex directory structure with various filtering options and export formats.
    """
    result = runner.invoke(
        app,
        [
            "visualize",
            complex_directory,
            "--exclude",
            "build dist",
            "--exclude-ext",
            ".so .tmp",
            "--exclude-pattern",
            "__.*__",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert "build" not in result.stdout
    assert "dist" not in result.stdout
    assert "src" in result.stdout
    assert "docs" in result.stdout
    result = runner.invoke(
        app,
        [
            "export",
            complex_directory,
            "--format",
            "json md",
            "--output-dir",
            output_dir,
            "--prefix",
            "complex",
            "--exclude",
            "build dist",
            "--exclude-ext",
            ".so .tmp",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "complex.json"))
    assert os.path.exists(os.path.join(output_dir, "complex.md"))
    with open(os.path.join(output_dir, "complex.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "structure" in data
        assert "src" in data["structure"]
        assert "docs" in data["structure"]
        assert "build" not in data["structure"]
        assert "dist" not in data["structure"]


def test_regex_filtering_with_complex_directory(complex_directory):
    """
    Test regex filtering with a complex directory structure.

    This test ensures that regex patterns are correctly applied when filtering a complex directory structure.
    """
    include_patterns = [re.compile(r"\.py$")]
    structure, extensions = get_directory_structure(
        complex_directory,
        include_patterns=include_patterns,
    )
    assert ".py" in extensions
    assert ".md" not in extensions
    assert ".so" not in extensions
    assert ".tmp" not in extensions
    python_files_found = False
    non_python_files_found = False

    def check_files(structure):
        nonlocal python_files_found, non_python_files_found
        if "_files" in structure:
            for file in structure["_files"]:
                file_name = file if isinstance(file, str) else file[0]
                if file_name.endswith(".py"):
                    python_files_found = True
                else:
                    non_python_files_found = True
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                check_files(value)

    check_files(structure)
    assert python_files_found, "No Python files found in structure"
    assert not non_python_files_found, "Non-Python files found despite include pattern"


def test_comparison_with_complex_directories(
    complex_directory, complex_directory_clone, output_dir
):
    """
    Test comparison between two complex directory structures.

    This test verifies that the comparison functionality correctly identifies differences between two complex directory structures.
    """
    structure1, structure2, extensions = compare_directory_structures(
        complex_directory,
        complex_directory_clone,
        exclude_dirs=["build", "dist"],
        max_depth=3,
    )
    assert "src" in structure1
    assert "src" in structure2
    assert "docs" in structure1
    assert "docs" in structure2
    assert "build" not in structure1
    assert "dist" not in structure1
    assert "CHANGELOG.md" not in structure1.get("_files", [])
    if "_files" in structure2:
        changelog_found = False
        for file_item in structure2["_files"]:
            file_name = file_item if isinstance(file_item, str) else file_item[0]
            if file_name == "CHANGELOG.md":
                changelog_found = True
                break
        assert changelog_found, "CHANGELOG.md not found in structure2"
    output_path = os.path.join(output_dir, "comparison.html")
    export_comparison(
        complex_directory,
        complex_directory_clone,
        "html",
        output_path,
        exclude_dirs=["build", "dist"],
        max_depth=3,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Directory Comparison" in content
        assert os.path.basename(complex_directory) in content
        assert os.path.basename(complex_directory_clone) in content
        assert "CHANGELOG.md" in content


def test_full_path_display_with_complex_directory(complex_directory, output_dir):
    """
    Test full path display with a complex directory structure.

    This test verifies that the full path display functionality works correctly with a complex directory structure.
    """
    structure, _ = get_directory_structure(
        complex_directory,
        show_full_path=True,
        max_depth=3,
    )
    assert "_files" in structure
    for file_item in structure["_files"]:
        assert isinstance(file_item, tuple)
        file_name, full_path = file_item
        assert os.path.isabs(full_path.replace("/", os.sep))
        assert file_name in os.path.basename(full_path)
    output_path = os.path.join(output_dir, "full_path.json")
    export_structure(
        structure,
        complex_directory,
        "json",
        output_path,
        show_full_path=True,
    )
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "structure" in data
        assert "_files" in data["structure"]
        paths = data["structure"]["_files"]
        for path in paths:
            assert os.path.isabs(path.replace("/", os.sep))
            assert complex_directory.replace(os.sep, "/") in path.replace(os.sep, "/")


def test_depth_limit_with_complex_directory(complex_directory):
    """
    Test depth limiting with a complex directory structure.

    This test verifies that the depth limit functionality correctly limits the depth of the directory structure.
    """
    for depth in [1, 2, 3]:
        structure, _ = get_directory_structure(
            complex_directory,
            max_depth=depth,
        )

        def check_depth(structure, current_depth=0):
            if current_depth == depth:
                for key, value in structure.items():
                    if (
                        key != "_files"
                        and key != "_max_depth_reached"
                        and isinstance(value, dict)
                    ):
                        assert "_max_depth_reached" in value
                return
            for key, value in structure.items():
                if (
                    key != "_files"
                    and key != "_max_depth_reached"
                    and isinstance(value, dict)
                ):
                    if current_depth < depth - 1:
                        assert "_max_depth_reached" not in value
                    check_depth(value, current_depth + 1)

        check_depth(structure)


def test_cli_with_regex_patterns(runner, temp_dir):
    """Minimal test for CLI regex functionality."""
    with open(os.path.join(temp_dir, "test.txt"), "w") as f:
        f.write("Test file")
    with open(os.path.join(temp_dir, "test.py"), "w") as f:
        f.write("Python file")
    result = runner.invoke(app, ["visualize", temp_dir])
    assert result.exit_code == 0
    assert "test.txt" in result.stdout
    assert "test.py" in result.stdout
    result = runner.invoke(app, ["visualize", temp_dir, "--exclude-pattern", "*.py"])
    assert result.exit_code == 0
    assert "test.txt" in result.stdout


def test_gitignore_pattern_with_complex_directory(complex_directory):
    """
    Test handling of .gitignore patterns with a complex directory structure.

    This test verifies that the .gitignore patterns are correctly applied when filtering directory structures.
    """
    structure, _ = get_directory_structure(
        complex_directory,
        ignore_file=".gitignore",
    )
    assert "build" not in structure
    assert "dist" not in structure

    def check_extensions(structure):
        for key, value in structure.items():
            if key == "_files":
                for file in value:
                    file_name = file if isinstance(file, str) else file[0]
                    assert not file_name.endswith(".pyc")
                    assert not file_name.endswith(".so")
                    assert not file_name.endswith(".tmp")
            elif key != "_max_depth_reached" and isinstance(value, dict):
                check_extensions(value)

    check_extensions(structure)
