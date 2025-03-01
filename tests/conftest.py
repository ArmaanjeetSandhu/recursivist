"""Test fixtures for recursivist package."""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_directory(temp_dir):
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
def sample_with_logs(sample_directory):
    """Sample directory with log files."""
    log_file = os.path.join(sample_directory, "app.log")
    with open(log_file, "w") as f:
        f.write("Some log content")

    return sample_directory


@pytest.fixture
def output_dir(temp_dir):
    """Create an output directory for export tests."""
    output_path = os.path.join(temp_dir, "output")
    os.makedirs(output_path, exist_ok=True)
    return output_path
