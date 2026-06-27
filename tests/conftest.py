"""Test fixtures for recursivist package."""

import os
import shutil
import tempfile
import time
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from rich.tree import Tree
from typer.testing import CliRunner

FileInfo = (
    str
    | tuple[str, str]
    | tuple[str, str, int]
    | tuple[str, str, int, int]
    | tuple[str, str, int, int, float]
)
DirStructure = dict[str, Any]


@pytest.fixture
def runner() -> CliRunner:
    """Create a Typer test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_directory(temp_dir: str) -> str:
    """Create a sample directory structure for testing.
    Structure:
    temp_dir/
    ├── file1.txt
    ├── file2.py
    ├── .gitignore
    ├── node_modules/
    │   └── package.json
    └── subdir/
        ├── subfile1.md
        └── subfile2.json
    """
    with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
        f.write("Sample content")
    with open(os.path.join(temp_dir, "file2.py"), "w") as f:
        f.write("print('Hello, world!')")
    with open(os.path.join(temp_dir, ".gitignore"), "w") as f:
        f.write("*.log\nnode_modules/\n")
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir, exist_ok=True)
    with open(os.path.join(subdir, "subfile1.md"), "w") as f:
        f.write("# Markdown file")
    with open(os.path.join(subdir, "subfile2.json"), "w") as f:
        f.write('{"key": "value"}')
    node_modules = os.path.join(temp_dir, "node_modules")
    os.makedirs(node_modules, exist_ok=True)
    with open(os.path.join(node_modules, "package.json"), "w") as f:
        f.write('{"name": "test-package"}')
    return temp_dir


@pytest.fixture
def sample_with_logs(sample_directory: str) -> str:
    """Sample directory with log files."""
    log_file = os.path.join(sample_directory, "app.log")
    with open(log_file, "w") as f:
        f.write("Some log content")
    return sample_directory


@pytest.fixture
def output_dir(temp_dir: str) -> str:
    """Create an output directory for export tests."""
    output_path = os.path.join(temp_dir, "output")
    os.makedirs(output_path, exist_ok=True)
    return output_path


@pytest.fixture
def deeply_nested_directory(temp_dir: str) -> str:
    """Create a deeply nested directory structure for depth limit tests.
    Structure:
    temp_dir/
    ├── root_file.txt
    └── level1/
        ├── level1_file.txt
        ├── level1_dir1/
        │   ├── level2_file1.txt
        │   └── level2_file2.txt
        └── level2/
            ├── level2_file.txt
            └── level3/
                ├── level3_file.txt
                └── level4/
                    ├── level4_file.txt
                    └── level5/
                        ├── level5_file.txt
                        └── level6/
                            └── level6_file.txt
    """
    level1 = os.path.join(temp_dir, "level1")
    level1_dir1 = os.path.join(level1, "level1_dir1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    level4 = os.path.join(level3, "level4")
    level5 = os.path.join(level4, "level5")
    level6 = os.path.join(level5, "level6")
    for directory in [level1, level1_dir1, level2, level3, level4, level5, level6]:
        os.makedirs(directory, exist_ok=True)
    file_paths = [
        os.path.join(temp_dir, "root_file.txt"),
        os.path.join(level1, "level1_file.txt"),
        os.path.join(level1_dir1, "level2_file1.txt"),
        os.path.join(level1_dir1, "level2_file2.txt"),
        os.path.join(level2, "level2_file.txt"),
        os.path.join(level3, "level3_file.txt"),
        os.path.join(level4, "level4_file.txt"),
        os.path.join(level5, "level5_file.txt"),
        os.path.join(level6, "level6_file.txt"),
    ]
    for i, path in enumerate(file_paths):
        with open(path, "w") as f:
            f.write(f"Level {i} file content")
    return temp_dir


@pytest.fixture
def pattern_test_directory(temp_dir: str) -> str:
    """Create a directory structure for pattern matching tests.
    Structure includes various file types and patterns to test
    include/exclude functionality.
    """
    os.makedirs(os.path.join(temp_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "tests", "unit"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "tests", "integration"), exist_ok=True)
    files = {
        "regular_file.txt": "Regular file content",
        "test_file1.py": "Test file 1 content",
        "test_file2.js": "Test file 2 content",
        "spec.file.js": "Spec file content",
        ".hidden.file": "Hidden file content",
        "config.json": '{"key": "value"}',
        "data_20230101.csv": "date,value\n2023-01-01,100",
        "data_20230102.csv": "date,value\n2023-01-02,200",
        os.path.join("logs", "app.log"): "App log content",
        os.path.join("logs", "error.log"): "Error log content",
        os.path.join("logs", "debug.log"): "Debug log content",
        os.path.join("tests", "unit", "test_unit.py"): "Unit test content",
        os.path.join(
            "tests", "integration", "test_integration.py"
        ): "Integration test content",
    }
    for file_path, content in files.items():
        full_path = os.path.join(temp_dir, file_path)
        with open(full_path, "w") as f:
            f.write(content)
    return temp_dir


@pytest.fixture
def comparison_directories(temp_dir: str) -> tuple[str, str]:
    """Create two directories for comparison testing.
    Creates two directories with some common files and some
    unique files to each directory for comparison testing.
    """
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(os.path.join(dir1, "common_dir"), exist_ok=True)
    os.makedirs(os.path.join(dir1, "dir1_only"), exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    os.makedirs(os.path.join(dir2, "common_dir"), exist_ok=True)
    os.makedirs(os.path.join(dir2, "dir2_only"), exist_ok=True)
    with open(os.path.join(dir1, "file1.txt"), "w") as f:
        f.write("File in both dirs")
    with open(os.path.join(dir1, "dir1_only.txt"), "w") as f:
        f.write("Only in dir1")
    with open(os.path.join(dir1, "common_dir", "common_file.py"), "w") as f:
        f.write("print('Common file')")
    with open(os.path.join(dir2, "file1.txt"), "w") as f:
        f.write("File in both dirs")
    with open(os.path.join(dir2, "dir2_only.txt"), "w") as f:
        f.write("Only in dir2")
    with open(os.path.join(dir2, "common_dir", "common_file.py"), "w") as f:
        f.write("print('Common file')")
    with open(os.path.join(dir2, "common_dir", "dir2_only.py"), "w") as f:
        f.write("print('Only in dir2')")
    return dir1, dir2


@pytest.fixture
def complex_directory(temp_dir: str) -> str:
    """Create a complex directory structure for testing.
    Creates a complex directory structure with multiple levels,
    different file types, and various content.
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
    with open(os.path.join(docs_dir, "examples.md"), "w") as f:
        f.write("# Examples\nHere are some examples of using the library.\n")
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
    with open(os.path.join(src_dir, "utils.py"), "w") as f:
        f.write("def utility_function():\n    return 'Utility function called'\n")
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
def complex_directory_clone(complex_directory: str, temp_dir: str) -> str:
    """Create a modified clone of the complex directory.
    Creates a clone of the complex directory with some files modified
    and some new files added to test comparison functionality.
    """
    clone_dir = os.path.join(os.path.dirname(temp_dir), "complex_clone")
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
    os.makedirs(clone_dir, exist_ok=True)
    files_to_copy = [
        ".gitignore",
        "README.md",
        "setup.py",
        "requirements.txt",
    ]
    for file in files_to_copy:
        with open(os.path.join(complex_directory, file)) as src:
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
    with open(os.path.join(src_dir, "new_module.py"), "w") as f:
        f.write("def new_function():\n    return 'New function called'\n")
    docs_dir = os.path.join(clone_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "index.md"), "w") as f:
        f.write("# Documentation\nWelcome to the updated documentation.\n")
    return clone_dir


@pytest.fixture
def mock_tree() -> MagicMock:
    """Create a mock Rich Tree object."""
    return MagicMock(spec=Tree)


@pytest.fixture
def mock_subtree() -> MagicMock:
    """Create a mock Tree that can be returned by mock_tree.add()."""
    return MagicMock(spec=Tree)


@pytest.fixture
def color_map() -> dict[str, str]:
    """Create a sample color map for file extensions."""
    return {
        ".py": "#FF0000",
        ".txt": "#00FF00",
        ".md": "#0000FF",
        ".json": "#FFFF00",
        ".js": "#FF00FF",
    }


@pytest.fixture
def simple_structure() -> DirStructure:
    """Create a simple directory structure for testing."""
    return {
        "_files": ["file1.txt", "file2.py", "file3.md"],
    }


@pytest.fixture
def nested_structure() -> DirStructure:
    """Create a nested directory structure for testing."""
    return {
        "_files": ["root_file1.txt", "root_file2.py"],
        "subdir1": {
            "_files": ["subdir1_file1.txt", "subdir1_file2.js"],
        },
        "subdir2": {
            "_files": ["subdir2_file1.md"],
            "nested": {
                "_files": ["nested_file1.json"],
            },
        },
    }


@pytest.fixture
def structure_with_stats() -> DirStructure:
    """Create a directory structure with file statistics."""
    now = time.time()
    return {
        "_loc": 100,
        "_size": 1024,
        "_mtime": now,
        "_files": [
            ("file1.txt", "/path/to/file1.txt", 50, 512, now - 100),
            ("file2.py", "/path/to/file2.py", 30, 256, now - 200),
        ],
        "subdir": {
            "_loc": 20,
            "_size": 256,
            "_mtime": now - 300,
            "_files": [
                ("subfile.md", "/path/to/subdir/subfile.md", 20, 256, now - 400),
            ],
        },
    }


@pytest.fixture
def max_depth_structure() -> DirStructure:
    """Create a structure with max depth indicator."""
    return {
        "_files": ["root_file.txt"],
        "subdir": {
            "_max_depth_reached": True,
        },
    }
