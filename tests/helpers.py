"""Shared assertion and file helpers (currently unused by the suite; kept for reuse)."""

import json
import os
from typing import Any

FileInfo = (
    str
    | tuple[str, str]
    | tuple[str, str, int]
    | tuple[str, str, int, int]
    | tuple[str, str, int, int, float]
)
DirStructure = dict[str, Any]


def create_test_file(
    path: str, content: str = "Test content", size: int | None = None
) -> str:
    """Helper function to create a test file with specified content or size."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if size is not None:
        with open(path, "wb") as f:
            f.write(b"x" * size)
    else:
        with open(path, "w") as f:
            f.write(content)
    return path


def assert_structure_has_files(
    structure: DirStructure, expected_files: list[str]
) -> None:
    """Assert that a structure contains the expected files."""
    assert "_files" in structure
    file_names = [file_item.name for file_item in structure["_files"]]
    for expected_file in expected_files:
        assert expected_file in file_names


def assert_structure_has_dirs(
    structure: DirStructure, expected_dirs: list[str]
) -> None:
    """Assert that a structure contains the expected directories."""
    for expected_dir in expected_dirs:
        assert expected_dir in structure
        assert isinstance(structure[expected_dir], dict)


def assert_stats_in_structure(structure: DirStructure) -> None:
    """Assert that a structure contains statistics."""
    assert "_loc" in structure
    assert "_size" in structure
    assert "_mtime" in structure
    if "_files" in structure:
        for file_item in structure["_files"]:
            assert isinstance(file_item.loc, int)
            assert isinstance(file_item.size, int)
            assert isinstance(file_item.mtime, float)


def assert_json_export_valid(file_path: str, root_name: str) -> dict[str, Any]:
    """Assert that a JSON export file is valid and contains expected structure."""
    assert os.path.exists(file_path)
    with open(file_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert "root" in data
    assert data["root"] == root_name
    assert "structure" in data
    return data


def assert_html_export_valid(file_path: str, root_name: str) -> str:
    """Assert that an HTML export file is valid and contains expected structure."""
    assert os.path.exists(file_path)
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "<html" in content
    assert "</html>" in content
    assert root_name in content
    return content


def assert_text_based_export_valid(
    file_path: str, root_name: str, format_name: str
) -> str:
    """Assert that a text-based export (txt, md) is valid."""
    assert os.path.exists(file_path)
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    if format_name == "txt":
        assert f"📂 {root_name}" in content
    elif format_name == "md":
        assert f"# 📂 {root_name}" in content
    return content


def assert_cli_command_success(
    result: Any,
    expected_items: list[str] | None = None,
    unexpected_items: list[str] | None = None,
) -> None:
    """Assert that a CLI command succeeded and contains expected output."""
    assert result.exit_code == 0
    if expected_items:
        for item in expected_items:
            assert item in result.stdout
    if unexpected_items:
        for item in unexpected_items:
            assert item not in result.stdout
