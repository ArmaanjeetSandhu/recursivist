"""CLI command tests (recursivist.cli): visualize, export, compare, version."""

import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from typer.testing import CliRunner

from recursivist import cli as cli_module
from recursivist.cli import app, parse_list_option
from recursivist.exporters.markdown import _md_escape_text
from recursivist.exporters.rst import _rst_escape
from recursivist.scanner import get_directory_structure


def assert_path_info_in_output(output: str, directory: str) -> None:
    """Check if output contains full path information."""
    base_name = os.path.basename(directory)
    has_full_path = False
    sample_path = f"{base_name}/file1.txt".replace("/", os.sep)
    sample_path_alt = f"{base_name}\\file1.txt".replace("\\", os.sep)
    has_full_path = base_name in output and (
        "file1.txt" in output
        or "file2.py" in output
        or sample_path in output
        or sample_path_alt in output
    )
    assert has_full_path, "Full path information not found in output"


@pytest.mark.parametrize(
    "input_list,expected",
    [
        (["value1"], ["value1"]),
        (["value1", "value2", "value3"], ["value1", "value2", "value3"]),
        (["Application Support"], ["Application Support"]),
        (
            ["Application Support", "My Documents"],
            ["Application Support", "My Documents"],
        ),
        (["value1 value2", "value3 value4"], ["value1 value2", "value3 value4"]),
        (["  spaced  ", "", "   "], ["spaced"]),
        ([], []),
        (None, []),
    ],
)
def test_parse_list_option(input_list: list[str] | None, expected: list[str]) -> None:
    result = parse_list_option(input_list)
    assert result == expected


def test_visualize_command(runner: CliRunner, sample_directory: str) -> None:
    result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert os.path.basename(sample_directory) in result.stdout
    assert "file1.txt" in result.stdout
    assert "file2.py" in result.stdout
    assert "subdir" in result.stdout


def test_visualize_with_full_path(runner: CliRunner, sample_directory: str) -> None:
    result = runner.invoke(app, ["visualize", sample_directory, "--full-path"])
    assert result.exit_code == 0
    assert_path_info_in_output(result.stdout, sample_directory)


@pytest.mark.parametrize(
    "option_name,option_value,expected_missing",
    [
        ("--exclude", "exclude_me", ["exclude_me", "excluded.txt"]),
        ("--exclude-ext", ".py", ["file2.py"]),
        ("--include-pattern", "include_*", ["ignore_me.txt", "file1.txt", "file2.py"]),
        ("--exclude-pattern", "exclude_*", ["exclude_this.txt"]),
    ],
)
def test_visualize_with_filtering_options(
    runner: CliRunner,
    sample_directory: str,
    option_name: str,
    option_value: str,
    expected_missing: list[str],
) -> None:
    if "exclude_me" in expected_missing:
        exclude_dir = os.path.join(sample_directory, "exclude_me")
        os.makedirs(exclude_dir, exist_ok=True)
        with open(os.path.join(exclude_dir, "excluded.txt"), "w") as f:
            f.write("This should be excluded")
    if "exclude_this.txt" in expected_missing:
        with open(os.path.join(sample_directory, "exclude_this.txt"), "w") as f:
            f.write("This should be excluded")
        with open(os.path.join(sample_directory, "keep_this.txt"), "w") as f:
            f.write("This should be kept")
    if "include_*" in option_value:
        with open(os.path.join(sample_directory, "include_me.txt"), "w") as f:
            f.write("This should be included")
        with open(os.path.join(sample_directory, "ignore_me.txt"), "w") as f:
            f.write("This should be ignored")
    result = runner.invoke(
        app, ["visualize", sample_directory, option_name, option_value]
    )
    assert result.exit_code == 0
    for item in expected_missing:
        assert item not in result.stdout
    if option_name == "--include-pattern":
        assert "include_me.txt" in result.stdout
    elif option_name == "--exclude-pattern":
        assert "keep_this.txt" in result.stdout


@pytest.mark.parametrize(
    "option_name,value1,value2",
    [
        ("--exclude", "exclude_me1", "exclude_me2"),
        ("--exclude-ext", ".py", ".log"),
        ("--include-pattern", "include_*", "also_*"),
        ("--exclude-pattern", "exclude_*", "also_*"),
    ],
)
def test_visualize_with_multiple_filtering_options(
    runner: CliRunner, sample_directory: str, option_name: str, value1: str, value2: str
) -> None:
    if option_name == "--exclude":
        exclude_dir1 = os.path.join(sample_directory, "exclude_me1")
        exclude_dir2 = os.path.join(sample_directory, "exclude_me2")
        os.makedirs(exclude_dir1, exist_ok=True)
        os.makedirs(exclude_dir2, exist_ok=True)
        with open(os.path.join(exclude_dir1, "excluded1.txt"), "w") as f:
            f.write("This should be excluded")
        with open(os.path.join(exclude_dir2, "excluded2.txt"), "w") as f:
            f.write("This should also be excluded")
    elif option_name == "--exclude-ext":
        with open(os.path.join(sample_directory, "test1.log"), "w") as f:
            f.write("Log content")
        with open(os.path.join(sample_directory, "test2.tmp"), "w") as f:
            f.write("Temp content")
    elif option_name == "--include-pattern":
        with open(os.path.join(sample_directory, "include_me.txt"), "w") as f:
            f.write("This should be included")
        with open(os.path.join(sample_directory, "also_include.py"), "w") as f:
            f.write("This should also be included")
        with open(os.path.join(sample_directory, "ignore_me.txt"), "w") as f:
            f.write("This should be ignored")
    elif option_name == "--exclude-pattern":
        with open(os.path.join(sample_directory, "exclude_this.txt"), "w") as f:
            f.write("This should be excluded")
        with open(os.path.join(sample_directory, "also_exclude.py"), "w") as f:
            f.write("This should also be excluded")
        with open(os.path.join(sample_directory, "keep_this.txt"), "w") as f:
            f.write("This should be kept")
    result = runner.invoke(
        app, ["visualize", sample_directory, option_name, f"{value1} {value2}"]
    )
    assert result.exit_code == 0
    result = runner.invoke(
        app, ["visualize", sample_directory, option_name, value1, option_name, value2]
    )
    assert result.exit_code == 0
    if option_name == "--exclude":
        for result_output in [result.stdout]:
            assert "exclude_me1" not in result_output
            assert "exclude_me2" not in result_output
            assert "excluded1.txt" not in result_output
            assert "excluded2.txt" not in result_output
    elif option_name == "--exclude-ext":
        for result_output in [result.stdout]:
            assert "file1.txt" in result_output
            assert "file2.py" not in result_output
            assert "test1.log" not in result_output
            assert "test2.tmp" in result_output
    elif option_name == "--include-pattern":
        for result_output in [result.stdout]:
            assert "include_me.txt" in result_output
            assert "also_include.py" in result_output
            assert "ignore_me.txt" not in result_output
    elif option_name == "--exclude-pattern":
        for result_output in [result.stdout]:
            assert "exclude_this.txt" not in result_output
            assert "also_exclude.py" not in result_output
            assert "keep_this.txt" in result_output


def test_visualize_exclude_directory_with_spaces(
    runner: CliRunner, sample_directory: str
) -> None:
    """A directory whose name contains spaces can be excluded via one flag."""
    spaced_dir = os.path.join(sample_directory, "Application Support")
    os.makedirs(spaced_dir, exist_ok=True)
    with open(os.path.join(spaced_dir, "prefs.plist"), "w") as f:
        f.write("should be excluded")
    kept_dir = os.path.join(sample_directory, "Application")
    os.makedirs(kept_dir, exist_ok=True)
    with open(os.path.join(kept_dir, "keep.txt"), "w") as f:
        f.write("should be kept")

    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude", "Application Support"]
    )
    assert result.exit_code == 0
    assert "Application Support" not in result.stdout
    assert "prefs.plist" not in result.stdout
    assert "Application" in result.stdout
    assert "keep.txt" in result.stdout


def test_visualize_exclude_pattern_with_spaces(
    runner: CliRunner, sample_directory: str
) -> None:
    """A glob pattern containing a space is matched as a single pattern."""
    with open(os.path.join(sample_directory, "final report.pdf"), "w") as f:
        f.write("should be excluded")
    with open(os.path.join(sample_directory, "notes.pdf"), "w") as f:
        f.write("should be kept")

    result = runner.invoke(
        app,
        ["visualize", sample_directory, "--exclude-pattern", "* report.pdf"],
    )
    assert result.exit_code == 0
    assert "final report.pdf" not in result.stdout
    assert "notes.pdf" in result.stdout


def test_visualize_with_regex_patterns(
    runner: CliRunner, sample_directory: str
) -> None:
    with open(os.path.join(sample_directory, "test123.txt"), "w") as f:
        f.write("This should be excluded with regex")
    with open(os.path.join(sample_directory, "test456.txt"), "w") as f:
        f.write("This should be excluded with regex")
    with open(os.path.join(sample_directory, "keep789.txt"), "w") as f:
        f.write("This should be kept")
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--exclude-pattern",
            "test\\d+\\.txt",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "test123.txt" not in result.stdout
    assert "test456.txt" not in result.stdout
    assert "keep789.txt" in result.stdout


def test_visualize_with_ignore_file(runner: CliRunner, sample_with_logs: str) -> None:
    result = runner.invoke(
        app, ["visualize", sample_with_logs, "--ignore-file", ".gitignore"]
    )
    assert result.exit_code == 0
    assert "app.log" not in result.stdout
    assert "node_modules" not in result.stdout


def test_visualize_include_pattern_keeps_ignored_dirs_pruned(
    runner: CliRunner, sample_with_logs: str
) -> None:
    """--include-pattern overrides ignore files for matching files only; it must
    not re-open directories the ignore file prunes."""
    with open(os.path.join(sample_with_logs, "node_modules", "dep.json"), "w") as f:
        f.write("{}")
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_with_logs,
            "--ignore-file",
            ".gitignore",
            "--include-pattern",
            "*.json",
        ],
    )
    assert result.exit_code == 0
    assert "node_modules" not in result.stdout
    assert "dep.json" not in result.stdout
    assert "package.json" not in result.stdout


def test_visualize_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str
) -> None:
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" not in result.stdout
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" not in result.stdout


def test_visualize_invalid_directory(
    runner: CliRunner, temp_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    invalid_dir = os.path.join(temp_dir, "nonexistent")
    result = runner.invoke(app, ["visualize", invalid_dir])
    assert result.exit_code == 1
    assert any("not a valid directory" in record.message for record in caplog.records)


def test_visualize_with_verbose_mode(
    runner: CliRunner, sample_directory: str, caplog: pytest.LogCaptureFixture
) -> None:
    result = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    assert result.exit_code == 0
    assert any("Verbose mode enabled" in record.message for record in caplog.records)


@pytest.mark.parametrize(
    "option,expected_in_output",
    [
        ("--sort-by-loc", "lines"),
        ("--sort-by-size", ["B", "KB", "MB"]),
        (
            "--sort-by-mtime",
            ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}", r"\w{3} \d{1,2}"],
        ),
    ],
)
def test_visualize_with_sort_options(
    runner: CliRunner,
    sample_directory: str,
    option: str,
    expected_in_output: str | list[str],
) -> None:
    result = runner.invoke(app, ["visualize", sample_directory, option])
    assert result.exit_code == 0
    if isinstance(expected_in_output, list):
        match_found = False
        for pattern in expected_in_output:
            if re.search(pattern, result.stdout):
                match_found = True
                break
        assert match_found, (
            f"None of the expected patterns {expected_in_output} found in output"
        )
    else:
        assert expected_in_output in result.stdout


@pytest.mark.parametrize(
    "format_option",
    [
        "txt",
        "json",
        "html",
        "md",
        "rst",
        "txt json",
        "txt json html md rst",
    ],
)
def test_export_command(
    runner: CliRunner, sample_directory: str, output_dir: str, format_option: str
) -> None:
    prefix = "test_export"
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            format_option,
            "--output-dir",
            output_dir,
            "--prefix",
            prefix,
        ],
    )
    assert result.exit_code == 0
    formats = format_option.split()
    for fmt in formats:
        export_file = os.path.join(output_dir, f"{prefix}.{fmt}")
        assert os.path.exists(export_file), f"File {export_file} does not exist"
        with open(export_file, encoding="utf-8") as f:
            content = f.read()
            root_name = os.path.basename(sample_directory)
            if fmt == "md":
                root_name = _md_escape_text(root_name)
            elif fmt == "rst":
                root_name = _rst_escape(root_name)
            assert root_name in content


def test_export_with_multiple_format_flags(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt",
            "--format",
            "json",
            "--format",
            "html",
            "--output-dir",
            output_dir,
            "--prefix",
            "multi_format",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "multi_format.txt"))
    assert os.path.exists(os.path.join(output_dir, "multi_format.json"))
    assert os.path.exists(os.path.join(output_dir, "multi_format.html"))


def test_export_json_content(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """Specific test for JSON export content validation."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "json_validate",
        ],
    )
    assert result.exit_code == 0
    json_file = os.path.join(output_dir, "json_validate.json")
    with open(json_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert "root" in data
    assert "structure" in data
    assert data["root"] == os.path.basename(sample_directory)
    assert "_files" in data["structure"]
    file_names = data["structure"]["_files"]
    assert "file1.txt" in file_names
    assert "file2.py" in file_names
    assert "subdir" in data["structure"]


def test_export_with_full_path(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt",
            "--output-dir",
            output_dir,
            "--prefix",
            "test_export_full_path",
            "--full-path",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "test_export_full_path.txt")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        content = f.read()
    assert_path_info_in_output(content, sample_directory)


def test_export_with_filtering_options(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    exclude_dir = os.path.join(sample_directory, "exclude_me")
    os.makedirs(exclude_dir, exist_ok=True)
    with open(os.path.join(exclude_dir, "excluded.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(sample_directory, "test123.txt"), "w") as f:
        f.write("This should be excluded with pattern")
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "filtered_export",
            "--exclude",
            "exclude_me",
            "--exclude-pattern",
            "test*",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "filtered_export.json")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert "structure" in data
    assert "exclude_me" not in data["structure"]
    if "_files" in data["structure"]:
        for file in data["structure"]["_files"]:
            if isinstance(file, str):
                assert not file.startswith("test")
            else:
                assert not file[0].startswith("test")


def test_export_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str, output_dir: str
) -> None:
    result = runner.invoke(
        app,
        [
            "export",
            deeply_nested_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "depth_limited",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "depth_limited.json")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert "structure" in data
    assert "level1" in data["structure"]
    assert "level2" in data["structure"]["level1"]
    assert "_max_depth_reached" in data["structure"]["level1"]["level2"]


def test_export_invalid_format(
    runner: CliRunner, sample_directory: str, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch("recursivist.cli.get_directory_structure") as scan:
        result = runner.invoke(app, ["export", sample_directory, "--format", "invalid"])
    assert result.exit_code == 1
    assert any(
        "Unsupported export format" in record.message for record in caplog.records
    )
    scan.assert_not_called()
    assert not any(record.message == "Error: 1" for record in caplog.records)


def test_export_failure_exits_nonzero_without_traceback(
    runner: CliRunner,
    sample_directory: str,
    temp_dir: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    out = os.path.join(temp_dir, "out")
    os.makedirs(os.path.join(out, "structure.txt"))
    result = runner.invoke(
        app,
        ["export", sample_directory, "-f", "txt", "-f", "json", "-o", out],
    )
    assert result.exit_code == 1
    failures = [r for r in caplog.records if r.message.startswith("Failed to export")]
    assert len(failures) == 1
    assert not failures[0].exc_info
    assert os.path.isfile(os.path.join(out, "structure.json"))


def test_github_error_is_reported_without_traceback(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    from recursivist.github import GitHubError

    with mock.patch(
        "recursivist.cli.checkout_repository",
        side_effect=GitHubError("Repository 'o/r' was not found."),
    ):
        result = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    assert result.exit_code == 1
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert [r.message for r in errors] == ["Error: Repository 'o/r' was not found."]
    assert not errors[0].exc_info


def test_export_with_sort_options(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """Sorting by loc plus display-only --size/--mtime annotates all three.

    One sorting flag (``--sort-by-loc``) sets the sort key and displays LOC,
    while display-only ``--size`` and ``--mtime`` add their columns, so the
    export shows all three metrics.
    """
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "sorted_export",
            "--sort-by-loc",
            "--size",
            "--mtime",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "sorted_export.json")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["show_loc"] is True
    assert data["show_size"] is True
    assert data["show_mtime"] is True
    assert data["sort_key"] == "loc"
    assert data["metric_order"] == ["loc", "size", "mtime"]


def test_export_multiple_sort_flags_collapse_to_one(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """Multiple --sort-by-* flags collapse to a single sort key; the rest are
    discarded and contribute no annotation."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "lr_export",
            "--sort-by-loc",
            "--sort-by-size",
            "--sort-by-mtime",
        ],
    )
    assert result.exit_code == 0
    with open(os.path.join(output_dir, "lr_export.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["sort_key"] == "loc"
    assert data["show_loc"] is True
    assert data["show_size"] is False
    assert data["show_mtime"] is False
    assert data["metric_order"] == ["loc"]


def test_export_display_only_flags_show_without_sorting(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """Display-only flags annotate their metrics, in command-line order, without
    setting a sort key."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "order_export",
            "--size",
            "--loc",
        ],
    )
    assert result.exit_code == 0
    with open(os.path.join(output_dir, "order_export.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["sort_key"] is None
    assert data["metric_order"] == ["size", "loc"]
    assert data["show_loc"] is True
    assert data["show_size"] is True


def test_export_git_status_display_flag(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """--git-status shows the Git column without sorting by it."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "git_export",
            "--git-status",
        ],
    )
    assert result.exit_code == 0
    with open(os.path.join(output_dir, "git_export.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["show_git_status"] is True
    assert data["sort_key"] is None


def test_export_sort_by_git_status(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """--sort-by-git-status sorts by Git status and shows the column."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "gitsort_export",
            "--sort-by-git-status",
        ],
    )
    assert result.exit_code == 0
    with open(os.path.join(output_dir, "gitsort_export.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["sort_key"] == "git_status"
    assert data["show_git_status"] is True


def test_compare_command(
    runner: CliRunner, comparison_directories: tuple[str, str]
) -> None:
    dir1, dir2 = comparison_directories
    result = runner.invoke(app, ["compare", dir1, dir2])
    assert result.exit_code == 0
    assert os.path.basename(dir1) in result.stdout
    assert os.path.basename(dir2) in result.stdout
    assert "common.txt" in result.stdout or "file1.txt" in result.stdout
    assert "unique1.txt" in result.stdout or "dir1_only.txt" in result.stdout
    assert "unique2.txt" in result.stdout or "dir2_only.txt" in result.stdout
    assert "Legend" in result.stdout


def test_compare_with_filtering_options(runner: CliRunner, temp_dir: str) -> None:
    dir1 = os.path.join(temp_dir, "compare_dir1")
    dir2 = os.path.join(temp_dir, "compare_dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    os.makedirs(os.path.join(dir1, "exclude_me"), exist_ok=True)
    os.makedirs(os.path.join(dir2, "exclude_me"), exist_ok=True)
    test_files = {
        os.path.join(dir1, "exclude_me", "file.txt"): "Should be excluded",
        os.path.join(dir2, "exclude_me", "file.txt"): "Should be excluded",
        os.path.join(dir1, "excluded.pyc"): "Should be excluded by extension",
        os.path.join(dir2, "excluded.pyc"): "Should be excluded by extension",
        os.path.join(dir1, "normal.txt"): "Normal file",
        os.path.join(dir2, "different.txt"): "Different file",
    }
    for path, content in test_files.items():
        with open(path, "w") as f:
            f.write(content)
    result = runner.invoke(
        app, ["compare", dir1, dir2, "--exclude", "exclude_me", "--exclude-ext", ".pyc"]
    )
    assert result.exit_code == 0
    assert os.path.basename(dir1) in result.stdout
    assert os.path.basename(dir2) in result.stdout
    assert "normal.txt" in result.stdout
    assert "different.txt" in result.stdout
    assert "exclude_me" not in result.stdout
    assert "excluded.pyc" not in result.stdout


def test_compare_with_depth_limit(runner: CliRunner, temp_dir: str) -> None:
    dir1 = os.path.join(temp_dir, "compare_depth_dir1")
    dir2 = os.path.join(temp_dir, "compare_depth_dir2")
    level1_dir1 = os.path.join(dir1, "level1")
    level2_dir1 = os.path.join(level1_dir1, "level2")
    os.makedirs(level2_dir1, exist_ok=True)
    level1_dir2 = os.path.join(dir2, "level1")
    level2_dir2 = os.path.join(level1_dir2, "level2")
    os.makedirs(level2_dir2, exist_ok=True)
    test_files = {
        os.path.join(level1_dir1, "file1.txt"): "Level 1 file in dir1",
        os.path.join(level2_dir1, "file2.txt"): "Level 2 file in dir1",
        os.path.join(level1_dir2, "file1.txt"): "Level 1 file in dir2",
        os.path.join(level2_dir2, "different.txt"): "Different file in dir2",
    }
    for path, content in test_files.items():
        with open(path, "w") as f:
            f.write(content)
    result = runner.invoke(app, ["compare", dir1, dir2, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" not in result.stdout
    assert "file2.txt" not in result.stdout
    assert "different.txt" not in result.stdout


def test_compare_same_directory_rejected(
    runner: CliRunner, temp_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    dir1 = os.path.join(temp_dir, "same_dir")
    os.makedirs(dir1, exist_ok=True)
    with open(os.path.join(dir1, "file.txt"), "w") as f:
        f.write("content")
    result = runner.invoke(app, ["compare", dir1, dir1])
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_same_directory_trailing_slash_rejected(
    runner: CliRunner, temp_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    dir1 = os.path.join(temp_dir, "same_dir_slash")
    os.makedirs(dir1, exist_ok=True)
    with open(os.path.join(dir1, "file.txt"), "w") as f:
        f.write("content")
    result = runner.invoke(app, ["compare", dir1, dir1 + os.sep])
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_same_directory_relative_spelling_rejected(
    runner: CliRunner, temp_dir: str, caplog: pytest.LogCaptureFixture
) -> None:
    dir1 = os.path.join(temp_dir, "same_dir_rel")
    os.makedirs(dir1, exist_ok=True)
    with open(os.path.join(dir1, "file.txt"), "w") as f:
        f.write("content")
    other_spelling = os.path.join(temp_dir, "same_dir_rel", "..", "same_dir_rel")
    result = runner.invoke(app, ["compare", dir1, other_spelling])
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_different_directories_not_rejected(
    runner: CliRunner, temp_dir: str
) -> None:
    dir1 = os.path.join(temp_dir, "distinct_a")
    dir2 = os.path.join(temp_dir, "distinct_b")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    with open(os.path.join(dir1, "a.txt"), "w") as f:
        f.write("a")
    with open(os.path.join(dir2, "b.txt"), "w") as f:
        f.write("b")
    result = runner.invoke(app, ["compare", dir1, dir2])
    assert result.exit_code == 0


def test_compare_same_github_repo_rejected(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    url = "https://github.com/owner/repo"
    result = runner.invoke(app, ["compare", url, url])
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_same_github_repo_case_insensitive_rejected(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    result = runner.invoke(
        app,
        [
            "compare",
            "github.com/ArmaanjeetSandhu/zoom-anchor",
            "github.com/armaanjeetsandhu/zoom-anchor",
        ],
    )
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_github_default_branch_matches_explicit_ref_rejected(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch(
        "recursivist.github.resolve_commit_shas", return_value=["a" * 40, "a" * 40]
    ):
        result = runner.invoke(
            app,
            [
                "compare",
                "github.com/ArmaanjeetSandhu/zoom-anchor",
                "github.com/ArmaanjeetSandhu/zoom-anchor/tree/main",
            ],
        )
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_github_distinct_refs_same_commit_rejected(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    with mock.patch(
        "recursivist.github.resolve_commit_shas",
        return_value=["abc1234" * 5 + "def12", "abc1234" * 5 + "def12"],
    ):
        result = runner.invoke(
            app,
            [
                "compare",
                "github.com/owner/repo/tree/main",
                "github.com/owner/repo/tree/v1.0",
            ],
        )
    assert result.exit_code == 1
    assert any("with itself" in record.message for record in caplog.records)


def test_compare_github_explicit_ref_differs_from_default_allowed(
    runner: CliRunner,
) -> None:
    with mock.patch(
        "recursivist.github.resolve_commit_shas", return_value=["a" * 40, "b" * 40]
    ):
        with mock.patch("recursivist.cli.display_comparison") as display:
            result = runner.invoke(
                app,
                [
                    "compare",
                    "github.com/owner/repo",
                    "github.com/owner/repo/tree/main",
                ],
            )
    assert result.exit_code == 0
    assert display.called


def test_compare_github_different_refs_different_commits_allowed(
    runner: CliRunner,
) -> None:
    with mock.patch(
        "recursivist.github.resolve_commit_shas", return_value=["a" * 40, "b" * 40]
    ):
        with mock.patch("recursivist.cli.display_comparison") as display:
            result = runner.invoke(
                app,
                [
                    "compare",
                    "github.com/owner/repo/tree/main",
                    "github.com/owner/repo/tree/dev",
                ],
            )
    assert result.exit_code == 0
    assert display.called


def test_compare_github_identical_refs_no_resolution(runner: CliRunner) -> None:
    with mock.patch("recursivist.github.resolve_commit_shas") as resolve:
        result = runner.invoke(
            app,
            [
                "compare",
                "github.com/owner/repo/tree/main",
                "github.com/owner/repo/tree/main",
            ],
        )
    assert result.exit_code == 1
    resolve.assert_not_called()
    resolve.assert_not_called()


def test_compare_export_to_html(
    runner: CliRunner, comparison_directories: tuple[str, str], output_dir: str
) -> None:
    dir1, dir2 = comparison_directories
    result = runner.invoke(
        app,
        [
            "compare",
            dir1,
            dir2,
            "--save",
            "--output-dir",
            output_dir,
            "--prefix",
            "html_comparison",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "html_comparison.html")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "<html>" in content
    assert "file1.txt" in content
    assert "dir1_only.txt" in content
    assert "dir2_only.txt" in content


def test_compare_with_full_path(
    runner: CliRunner, comparison_directories: tuple[str, str]
) -> None:
    dir1, dir2 = comparison_directories

    width = (max(len(dir1), len(dir2)) + 40) * 2
    env = {**os.environ, "COLUMNS": str(width)}
    result = runner.invoke(app, ["compare", dir1, dir2, "--full-path"], env=env)

    assert result.exit_code == 0
    assert "dir1" in result.stdout
    assert "dir2" in result.stdout
    assert "Full file paths are shown" in result.stdout

    clean_output = "".join(result.stdout.split())
    dir1_clean = "".join(dir1.replace(os.sep, "/").split())
    dir2_clean = "".join(dir2.replace(os.sep, "/").split())

    has_full_path = dir1_clean in clean_output or dir2_clean in clean_output

    assert has_full_path, "No full paths found in the output"


git_available = shutil.which("git") is not None
requires_git = pytest.mark.skipif(not git_available, reason="git is not installed")


def _init_repo_with_changes(path: str) -> None:
    """Create a git repo under *path* with one modified and one untracked file."""
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)
    with open(os.path.join(path, "tracked.txt"), "w") as f:
        f.write("initial\n")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=path, check=True)
    with open(os.path.join(path, "tracked.txt"), "w") as f:
        f.write("initial\nchanged\n")
    with open(os.path.join(path, "fresh.txt"), "w") as f:
        f.write("new\n")


@requires_git
def test_compare_git_status_flag(runner: CliRunner, tmp_path: Path) -> None:
    """--git-status annotates each side of the comparison with status markers."""
    dir1 = str(tmp_path / "gitcmp1")
    dir2 = str(tmp_path / "gitcmp2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    _init_repo_with_changes(dir1)
    _init_repo_with_changes(dir2)

    result = runner.invoke(app, ["compare", dir1, dir2, "--git-status", "-e", ".git"])
    assert result.exit_code == 0
    assert "Git status markers" in result.stdout
    assert "[M]" in result.stdout
    assert "[U]" in result.stdout


@requires_git
def test_compare_sort_by_git_status_flag(runner: CliRunner, tmp_path: Path) -> None:
    """--sort-by-git-status sorts and annotates even without --git-status."""
    dir1 = str(tmp_path / "gitsort1")
    dir2 = str(tmp_path / "gitsort2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    _init_repo_with_changes(dir1)
    _init_repo_with_changes(dir2)

    result = runner.invoke(
        app, ["compare", dir1, dir2, "--sort-by-git-status", "-e", ".git"]
    )
    assert result.exit_code == 0
    assert "Files sorted by Git status" in result.stdout
    assert "[M]" in result.stdout


@requires_git
def test_compare_git_status_html_export(
    runner: CliRunner, tmp_path: Path, output_dir: str
) -> None:
    """HTML export of a comparison carries git badges and a legend block."""
    dir1 = str(tmp_path / "githtml1")
    dir2 = str(tmp_path / "githtml2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    _init_repo_with_changes(dir1)
    _init_repo_with_changes(dir2)

    result = runner.invoke(
        app,
        [
            "compare",
            dir1,
            dir2,
            "--git-status",
            "-e",
            ".git",
            "--save",
            "--output-dir",
            output_dir,
            "--prefix",
            "git_comparison",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "git_comparison.html")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        content = f.read()
    assert 'class="git-badge' in content
    assert 'info-label">Git Status:' in content


@pytest.mark.parametrize(
    "option", ["--sort-by-loc", "--sort-by-size", "--sort-by-mtime"]
)
def test_compare_with_sort_options(
    runner: CliRunner, comparison_directories: tuple[str, str], option: str
) -> None:
    dir1, dir2 = comparison_directories
    result = runner.invoke(app, ["compare", dir1, dir2, option])
    assert result.exit_code == 0
    assert os.path.basename(dir1) in result.stdout
    assert os.path.basename(dir2) in result.stdout
    if option == "--sort-by-loc":
        assert "lines" in result.stdout
    elif option == "--sort-by-size":
        assert any(unit in result.stdout for unit in ["B", "KB", "MB"])
    elif option == "--sort-by-mtime":
        assert any(
            (indicator is not None and indicator in result.stdout)
            or (pattern is not None and re.search(pattern, result.stdout))
            for indicator, pattern in [
                ("Today", None),
                ("Yesterday", None),
                (None, r"\d{4}-\d{2}-\d{2}"),
            ]
        )


def test_version_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Recursivist version" in result.stdout


def test_verbose_mode(
    runner: CliRunner, sample_directory: str, caplog: pytest.LogCaptureFixture
) -> None:
    result = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    assert result.exit_code == 0
    assert any("Verbose mode enabled" in record.message for record in caplog.records)


def test_visualize_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str
) -> None:
    """Test CLI visualize command with depth limits."""
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" not in result.stdout
    assert "level2" not in result.stdout
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" not in result.stdout
    assert "level3" not in result.stdout


def test_export_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str, output_dir: str
) -> None:
    """Test CLI export command with depth limits."""
    result = runner.invoke(
        app,
        [
            "export",
            deeply_nested_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "depth_limited",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    export_file: str = os.path.join(output_dir, "depth_limited.json")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert "structure" in data
    assert "level1" in data["structure"]
    assert "level2" in data["structure"]["level1"]
    assert "_max_depth_reached" in data["structure"]["level1"]["level2"]


def test_compare_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str, temp_dir: str
) -> None:
    """Test CLI compare command with depth limits."""
    compare_dir: str = os.path.join(os.path.dirname(temp_dir), "compare_dir")
    if os.path.exists(compare_dir):
        shutil.rmtree(compare_dir)
    os.makedirs(compare_dir, exist_ok=True)
    level1: str = os.path.join(compare_dir, "level1")
    level2: str = os.path.join(level1, "level2")
    level3: str = os.path.join(level2, "level3")
    os.makedirs(level1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(compare_dir, "different_root.txt"), "w") as f:
        f.write("Different root file")
    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file with different content")
    with open(os.path.join(level2, "different_level2.txt"), "w") as f:
        f.write("Different level 2 file")
    with open(os.path.join(level3, "level3_file.txt"), "w") as f:
        f.write("Level 3 file")
    result = runner.invoke(
        app, ["compare", deeply_nested_directory, compare_dir, "--depth", "2"]
    )
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "level1_file.txt" in result.stdout
    assert "different_root.txt" in result.stdout
    assert "level3" not in result.stdout
    assert "level3_file.txt" not in result.stdout
    assert "(max depth reached)" not in result.stdout


def test_compare_export_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str, temp_dir: str, output_dir: str
) -> None:
    """Test exporting comparison with depth limits."""
    compare_dir: str = os.path.join(os.path.dirname(temp_dir), "compare_export_dir")
    if os.path.exists(compare_dir):
        shutil.rmtree(compare_dir)
    os.makedirs(compare_dir, exist_ok=True)
    level1: str = os.path.join(compare_dir, "level1")
    level2: str = os.path.join(level1, "level2")
    level3: str = os.path.join(level2, "level3")
    os.makedirs(level1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(compare_dir, "different_root.txt"), "w") as f:
        f.write("Different root file")
    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file with different content")
    with open(os.path.join(level2, "different_level2.txt"), "w") as f:
        f.write("Different level 2 file")
    with open(os.path.join(level3, "level3_file.txt"), "w") as f:
        f.write("Level 3 file")
    result = runner.invoke(
        app,
        [
            "compare",
            deeply_nested_directory,
            compare_dir,
            "--depth",
            "2",
            "--save",
            "--output-dir",
            output_dir,
            "--prefix",
            "depth_limited_compare",
        ],
    )
    assert result.exit_code == 0
    export_file: str = os.path.join(output_dir, "depth_limited_compare.html")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        content: str = f.read()
    assert "level1" in content
    assert "level2" in content
    assert "level1_file.txt" in content
    assert "different_root.txt" in content
    assert "level3" not in content
    assert "(max depth reached)" not in content
    assert 'directory">📂 level2' in content


def test_depth_combined_with_filters(
    runner: CliRunner, deeply_nested_directory: str
) -> None:
    """Test combining depth limits with other filters."""
    excluded_dir: str = os.path.join(deeply_nested_directory, "excluded")
    os.makedirs(excluded_dir, exist_ok=True)
    with open(os.path.join(excluded_dir, "excluded.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(deeply_nested_directory, "excluded_root.txt"), "w") as f:
        f.write("This should be excluded at root")
    result = runner.invoke(
        app,
        [
            "visualize",
            deeply_nested_directory,
            "--depth",
            "2",
            "--exclude",
            "excluded",
            "--exclude-pattern",
            "excluded_*",
        ],
    )
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "excluded" not in result.stdout
    assert "excluded_root.txt" not in result.stdout
    assert "(max depth reached)" not in result.stdout


@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_export_with_different_depth_limits(
    runner: CliRunner, deeply_nested_directory: str, output_dir: str, depth: int
) -> None:
    """Test exporting with different depth limits."""
    result = runner.invoke(
        app,
        [
            "export",
            deeply_nested_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            f"depth_{depth}",
            "--depth",
            str(depth),
        ],
    )
    assert result.exit_code == 0
    export_file: str = os.path.join(output_dir, f"depth_{depth}.json")
    assert os.path.exists(export_file)
    with open(export_file, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    current: dict[str, Any] = data["structure"]
    assert "level1" in current
    current = current["level1"]
    if depth == 1:
        assert "_max_depth_reached" in current
        return
    assert "level2" in current
    current = current["level2"]
    if depth == 2:
        assert "_max_depth_reached" in current
        return
    assert "level3" in current
    current = current["level3"]
    if depth == 3:
        assert "_max_depth_reached" in current
        return
    assert "level4" in current
    current = current["level4"]
    if depth == 4:
        assert "_max_depth_reached" in current
        return


def test_unlimited_depth(runner: CliRunner, deeply_nested_directory: str) -> None:
    """Test with unlimited depth (depth=0)."""
    level1: str = os.path.join(deeply_nested_directory, "level1")
    level2: str = os.path.join(level1, "level2")
    level3: str = os.path.join(level2, "level3")
    level4: str = os.path.join(level3, "level4")
    level5: str = os.path.join(level4, "level5")
    level6: str = os.path.join(level5, "level6")
    assert os.path.exists(level6), "Test setup error: level6 directory should exist"
    result = runner.invoke(
        app,
        [
            "visualize",
            deeply_nested_directory,
            "--depth",
            "0",
        ],
    )
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "level3" in result.stdout
    assert "level4" in result.stdout
    assert "level5" in result.stdout
    assert "level6" in result.stdout
    assert "level6_file.txt" in result.stdout
    assert "(max depth reached)" not in result.stdout


def test_cli_with_regex_patterns(
    runner: CliRunner, pattern_test_directory: str
) -> None:
    """Test CLI with regex pattern options."""
    result = runner.invoke(
        app,
        [
            "visualize",
            pattern_test_directory,
            "--include-pattern",
            r"data_\d{8}\.csv$",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "data_20230101.csv" in result.stdout
    assert "data_20230102.csv" in result.stdout
    assert "regular_file.txt" not in result.stdout
    assert "test_file1.py" not in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            pattern_test_directory,
            "--exclude-pattern",
            r"^test_|^\.hidden",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "test_file1.py" not in result.stdout
    assert "test_file2.js" not in result.stdout
    assert ".hidden.file" not in result.stdout
    assert "regular_file.txt" in result.stdout
    assert "data_20230101.csv" in result.stdout


def test_glob_patterns(pattern_test_directory: str) -> None:
    """Test glob-style pattern matching."""
    exclude_patterns = ["test_*", "*.log"]
    structure, _ = get_directory_structure(
        pattern_test_directory, exclude_patterns=exclude_patterns
    )
    test_files_found = False
    log_files_found = False

    def check_files(struct: dict[str, Any]) -> None:
        nonlocal test_files_found, log_files_found
        if "_files" in struct:
            for file in struct["_files"]:
                file_name = file.name
                if file_name.startswith("test_"):
                    test_files_found = True
                if file_name.endswith(".log"):
                    log_files_found = True
        for key, value in struct.items():
            if key != "_files" and isinstance(value, dict):
                check_files(value)

    check_files(structure)
    assert not test_files_found, "Test files were found despite glob exclude pattern"
    assert not log_files_found, "Log files were found despite glob exclude pattern"


def test_mixed_regex_and_glob_patterns(
    runner: CliRunner, pattern_test_directory: str
) -> None:
    """Test mixing regex and glob patterns."""
    with open(os.path.join(pattern_test_directory, "glob_match.txt"), "w") as f:
        f.write("Should match glob pattern")
    with open(os.path.join(pattern_test_directory, "regex_match.txt"), "w") as f:
        f.write("Should match regex pattern")
    result = runner.invoke(
        app, ["visualize", pattern_test_directory, "--exclude-pattern", "glob_*"]
    )
    assert result.exit_code == 0
    assert "glob_match.txt" not in result.stdout
    assert "regex_match.txt" in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            pattern_test_directory,
            "--exclude-pattern",
            r"regex_.*\.txt$",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "regex_match.txt" not in result.stdout
    assert "glob_match.txt" in result.stdout


def test_regex_pattern_escaping(pattern_test_directory: str) -> None:
    """Test regex patterns with special characters that need escaping."""
    special_file = os.path.join(pattern_test_directory, "file+[special].txt")
    with open(special_file, "w") as f:
        f.write("Special characters in filename")
    include_patterns = [re.compile(r"file\+\[special\]\.txt$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    found = False
    if "_files" in structure:
        for file_item in structure["_files"]:
            file_name = file_item.name
            if file_name == "file+[special].txt":
                found = True
                break
    assert found, "File with special characters not found with escaped regex pattern"


def test_regex_nested_directory_patterns(pattern_test_directory: str) -> None:
    """Test regular expressions for files in nested directories."""
    structure, _ = get_directory_structure(pattern_test_directory)
    assert "tests" in structure, "Base structure doesn't have tests directory"
    assert "unit" in structure["tests"], "Base structure doesn't have unit directory"
    assert "integration" in structure["tests"], (
        "Base structure doesn't have integration directory"
    )
    include_patterns = [re.compile(r"test_.*\.py$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    files_at_root = [f.name for f in structure.get("_files", [])]
    assert "test_file1.py" in files_at_root, "Root test_file1.py should be included"
    assert "regular_file.txt" not in files_at_root, (
        "Non-matching files should be excluded"
    )
    include_patterns = [re.compile(r"regular_file\.txt$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        files_at_root = [f.name for f in structure.get("_files", [])]
        assert "regular_file.txt" in files_at_root, "Regular file should be included"
        assert "test_file1.py" not in files_at_root, "Test file should be excluded"
    with open(os.path.join(pattern_test_directory, "unique_test_pattern.py"), "w") as f:
        f.write("# Unique test file")
    include_patterns = [re.compile(r"unique_test_pattern\.py$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        files = [f.name for f in structure["_files"]]
        assert "unique_test_pattern.py" in files, "Unique test file should be included"


def test_visualize_reports_unmatched_filters(
    runner: CliRunner, sample_directory: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="recursivist")
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--exclude",
            "does_not_exist",
            "--exclude-ext",
            "xyz",
            "--exclude-ext",
            "txt",
        ],
    )
    assert result.exit_code == 0
    messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert "No files or directories matched --exclude 'does_not_exist'" in messages
    assert "No files or directories matched --exclude-ext '.xyz'" in messages
    assert not any("'.txt'" in m for m in messages)


def test_export_attached_short_value_does_not_count_as_flag(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """In ``-xsd`` the ``s`` is part of -x's value, so it is not ``--sort-by-loc``."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "attached",
            "-xsd",
            "--sort-by-size",
            "-s",
        ],
    )
    assert result.exit_code == 0
    with open(os.path.join(output_dir, "attached.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["sort_key"] == "size"
    assert data["metric_order"] == ["size"]


def test_flag_order_comes_from_invocation_not_process_argv(
    runner: CliRunner,
    sample_directory: str,
    output_dir: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Called from code, the CLI orders flags by its own arguments, not sys.argv."""
    monkeypatch.setattr("sys.argv", ["host-program", "--sort-by-loc"])
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "from_code",
            "--sort-by-size",
            "--sort-by-loc",
        ],
    )
    assert result.exit_code == 0
    with open(os.path.join(output_dir, "from_code.json"), encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    assert data["sort_key"] == "size"


def test_visualize_short_value_consumes_next_token(
    runner: CliRunner, sample_directory: str, mocker: Any
) -> None:
    """A detached value that looks like a flag (``-p -s``) is not scanned as one."""
    spy = mocker.spy(cli_module, "resolve_display_options")
    result = runner.invoke(
        app, ["visualize", sample_directory, "-p", "-s", "--sort-by-size", "-s"]
    )
    assert result.exit_code == 0
    assert spy.spy_return.sort_key == "size"


def test_short_option_value_arity_is_per_command(
    runner: CliRunner, temp_dir: str, mocker: Any
) -> None:
    """``-f`` is a flag on ``compare`` (unlike ``export``), so ``-fm`` includes -m."""
    dir1 = os.path.join(temp_dir, "one")
    dir2 = os.path.join(temp_dir, "two")
    for path in (dir1, dir2):
        os.makedirs(path)
        with open(os.path.join(path, "a.txt"), "w", encoding="utf-8") as f:
            f.write("a")
    spy = mocker.spy(cli_module, "resolve_display_options")
    result = runner.invoke(
        app,
        ["compare", dir1, dir2, "-o", temp_dir, "-fm", "--sort-by-size"],
    )
    assert result.exit_code == 0
    assert spy.spy_return.sort_key == "mtime"


@pytest.mark.parametrize("command", ["visualize", "export", "compare"])
def test_icon_style_rejects_unknown_value(
    runner: CliRunner, sample_directory: str, command: str
) -> None:
    """``--icon-style`` accepts only the styles ``config set`` accepts."""
    args = [command, sample_directory]
    if command == "compare":
        args.append(sample_directory)
    result = runner.invoke(app, [*args, "--icon-style", "bogus"])
    assert result.exit_code == 2
    assert "'bogus' is not one of 'emoji', 'nerd'" in result.output


@pytest.mark.parametrize("style", ["emoji", "nerd"])
def test_icon_style_accepts_known_values(
    runner: CliRunner, sample_directory: str, style: str
) -> None:
    result = runner.invoke(app, ["visualize", sample_directory, "--icon-style", style])
    assert result.exit_code == 0


@pytest.fixture
def saved_config(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Capture what ``config set`` would write instead of touching the real file."""
    saved: dict[str, Any] = {}
    monkeypatch.setattr(cli_module, "read_config_file", lambda: {"icon_style": "emoji"})
    monkeypatch.setattr(cli_module, "save_config", saved.update)
    return saved


@pytest.mark.parametrize("key", ["icon-style", "icon_style"])
def test_config_set_icon_style(
    runner: CliRunner, saved_config: dict[str, Any], key: str
) -> None:
    result = runner.invoke(app, ["config", "set", key, "nerd"])
    assert result.exit_code == 0
    assert saved_config == {"icon_style": "nerd"}


def test_config_set_rejects_unknown_key(
    runner: CliRunner, saved_config: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="recursivist"):
        result = runner.invoke(app, ["config", "set", "colour", "blue"])
    assert result.exit_code == 1
    assert saved_config == {}
    assert "Unknown configuration key: colour" in caplog.text
    assert "icon-style" in caplog.text


def test_config_set_rejects_invalid_value(
    runner: CliRunner, saved_config: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="recursivist"):
        result = runner.invoke(app, ["config", "set", "icon-style", "bogus"])
    assert result.exit_code == 1
    assert saved_config == {}
    assert "Invalid value for icon-style: 'bogus'" in caplog.text


def test_importing_cli_has_no_side_effects(tmp_path: Path) -> None:
    """Importing the CLI configures no logging and creates no config directory."""
    script = (
        "import logging\n"
        "root = logging.getLogger()\n"
        "before = (list(root.handlers), root.level)\n"
        "import recursivist.cli\n"
        "assert (list(root.handlers), root.level) == before, 'root logger changed'\n"
        "package = logging.getLogger('recursivist')\n"
        "assert package.handlers == [], 'handler attached on import'\n"
        "assert package.level == logging.NOTSET, 'level set on import'\n"
    )
    home = str(tmp_path)
    env = {
        **os.environ,
        "HOME": home,
        "USERPROFILE": home,
        "APPDATA": home,
        "XDG_CONFIG_HOME": home,
    }
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("extra_args", [[], ["--verbose"]])
def test_logging_setup_does_not_outlive_the_command(
    runner: CliRunner, sample_directory: str, extra_args: list[str]
) -> None:
    """A run leaves the root and package loggers exactly as it found them."""
    root = logging.getLogger()
    package = logging.getLogger("recursivist")
    before = (list(root.handlers), root.level, list(package.handlers), package.level)
    result = runner.invoke(app, ["visualize", sample_directory, *extra_args])
    assert result.exit_code == 0
    after = (list(root.handlers), root.level, list(package.handlers), package.level)
    assert after == before


def test_logging_setup_is_undone_when_the_command_fails(
    runner: CliRunner, temp_dir: str
) -> None:
    package = logging.getLogger("recursivist")
    before = (list(package.handlers), package.level)
    result = runner.invoke(
        app, ["visualize", os.path.join(temp_dir, "nonexistent"), "--verbose"]
    )
    assert result.exit_code == 1
    assert (list(package.handlers), package.level) == before


def test_log_messages_reach_the_terminal(
    runner: CliRunner, saved_config: dict[str, Any]
) -> None:
    result = runner.invoke(app, ["config", "set", "icon-style", "bogus"])
    assert result.exit_code == 1
    assert "Invalid value for icon-style" in result.output


def test_debug_messages_shown_only_when_verbose(
    runner: CliRunner, sample_directory: str
) -> None:
    verbose = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    quiet = runner.invoke(app, ["visualize", sample_directory])
    assert "Verbose mode enabled" in verbose.output
    assert "Verbose mode enabled" not in quiet.output


def test_icon_style_config_read_when_command_runs(
    runner: CliRunner, sample_directory: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The saved icon style is read each time a command runs."""
    styles = iter(["emoji", "nerd"])
    monkeypatch.setattr(
        "recursivist.config.load_config", lambda: {"icon_style": next(styles)}
    )
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        first = runner.invoke(app, ["visualize", sample_directory])
        second = runner.invoke(app, ["visualize", sample_directory])
    assert first.exit_code == second.exit_code == 0
    seen = [call.kwargs["icon_style"] for call in display_tree.call_args_list]
    assert seen == ["emoji", "nerd"]


def test_explicit_icon_style_skips_config(
    runner: CliRunner, sample_directory: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolve_config = mock.Mock(return_value={"icon_style": "emoji"})
    monkeypatch.setattr(cli_module, "resolve_config", resolve_config)
    result = runner.invoke(app, ["visualize", sample_directory, "--icon-style", "nerd"])
    assert result.exit_code == 0
    resolve_config.assert_not_called()


def _write_project_config(directory: str, style: str, pyproject: bool = False) -> None:
    """Give *directory* a project configuration selecting the icon *style*."""
    if pyproject:
        name, text = "pyproject.toml", f'[tool.recursivist]\nicon-style = "{style}"\n'
    else:
        name, text = ".recursivist.toml", f'icon-style = "{style}"\n'
    Path(directory, name).write_text(text, encoding="utf-8")


@pytest.mark.parametrize("pyproject", [False, True], ids=["dedicated", "pyproject"])
def test_visualize_uses_project_icon_style(
    runner: CliRunner, sample_directory: str, pyproject: bool
) -> None:
    _write_project_config(sample_directory, "nerd", pyproject)
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert display_tree.call_args.kwargs["icon_style"] == "nerd"


def test_visualize_subdirectory_uses_parent_project_config(
    runner: CliRunner, sample_directory: str
) -> None:
    _write_project_config(sample_directory, "nerd")
    subdir = os.path.join(sample_directory, "subdir")
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        result = runner.invoke(app, ["visualize", subdir])
    assert result.exit_code == 0
    assert display_tree.call_args.kwargs["icon_style"] == "nerd"


def test_project_icon_style_overrides_user_config(
    runner: CliRunner, sample_directory: str
) -> None:
    assert runner.invoke(app, ["config", "set", "icon-style", "nerd"]).exit_code == 0
    _write_project_config(sample_directory, "emoji")
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert display_tree.call_args.kwargs["icon_style"] == "emoji"


def test_icon_style_flag_overrides_project_config(
    runner: CliRunner, sample_directory: str
) -> None:
    _write_project_config(sample_directory, "nerd")
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        result = runner.invoke(
            app, ["visualize", sample_directory, "--icon-style", "emoji"]
        )
    assert result.exit_code == 0
    assert display_tree.call_args.kwargs["icon_style"] == "emoji"


def test_project_icon_style_changes_rendered_tree(
    runner: CliRunner, sample_directory: str
) -> None:
    before = runner.invoke(app, ["visualize", sample_directory])
    _write_project_config(sample_directory, "nerd")
    after = runner.invoke(app, ["visualize", sample_directory])
    assert before.exit_code == after.exit_code == 0
    assert "📄" in before.output
    assert "📄" not in after.output


def test_invalid_project_config_warns_and_keeps_running(
    runner: CliRunner, sample_directory: str
) -> None:
    _write_project_config(sample_directory, "bogus")
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert "Ignoring invalid value for 'icon-style'" in result.output
    assert display_tree.call_args.kwargs["icon_style"] == "emoji"


def test_visualize_github_input_skips_project_config(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A GitHub input has no project layer, even when the working directory does."""
    from recursivist.github import GitHubError

    _write_project_config(str(tmp_path), "nerd")
    monkeypatch.chdir(tmp_path)
    resolve_config = mock.Mock(return_value={"icon_style": "emoji"})
    monkeypatch.setattr(cli_module, "resolve_config", resolve_config)
    with mock.patch("recursivist.cli.checkout_repository", side_effect=GitHubError("")):
        runner.invoke(app, ["visualize", "https://github.com/o/r"])
    resolve_config.assert_called_once_with(None)


def test_export_ignores_project_icon_style(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
    """Exports use emoji whatever the project sets, so the files render anywhere."""
    _write_project_config(sample_directory, "nerd")
    result = runner.invoke(
        app, ["export", sample_directory, "-f", "txt", "-o", output_dir]
    )
    assert result.exit_code == 0
    exported = Path(output_dir, "structure.txt").read_text(encoding="utf-8")
    assert "📄" in exported


def test_compare_uses_project_config_of_first_local_directory(
    runner: CliRunner, comparison_directories: tuple[str, str]
) -> None:
    dir1, dir2 = comparison_directories
    _write_project_config(dir1, "nerd")
    _write_project_config(dir2, "emoji")
    with mock.patch("recursivist.cli.display_comparison") as display:
        first = runner.invoke(app, ["compare", dir1, dir2])
        second = runner.invoke(app, ["compare", dir2, dir1])
    assert first.exit_code == second.exit_code == 0
    seen = [call.kwargs["icon_style"] for call in display.call_args_list]
    assert seen == ["nerd", "emoji"]


def test_compare_saved_html_ignores_project_icon_style(
    runner: CliRunner, comparison_directories: tuple[str, str], output_dir: str
) -> None:
    dir1, dir2 = comparison_directories
    _write_project_config(dir1, "nerd")
    with mock.patch("recursivist.cli.export_comparison") as export_comparison:
        result = runner.invoke(app, ["compare", dir1, dir2, "--save", "-o", output_dir])
    assert result.exit_code == 0
    assert export_comparison.call_args.kwargs["icon_style"] == "emoji"


def _user_config_path() -> Path:
    """Path of the user configuration file the test session is isolated to."""
    from recursivist import config as config_module

    return config_module.get_config_path()


def _write_user_config(text: str) -> Path:
    """Write *text* as the user configuration file, as a hand edit would."""
    path = _user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("stored", ['"bogus"', '"Nerd"', "3", "null", '["nerd"]'])
def test_invalid_user_icon_style_does_not_reach_the_renderer(
    runner: CliRunner, sample_directory: str, stored: str
) -> None:
    """A hand-edited bad value is reported and the default style is rendered."""
    _write_user_config(f'{{"icon_style": {stored}}}')
    result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert "Ignoring invalid value for 'icon_style'" in result.output
    assert "📄" in result.output


def test_invalid_user_icon_style_does_not_reach_compare(
    runner: CliRunner, comparison_directories: tuple[str, str]
) -> None:
    _write_user_config('{"icon_style": "bogus"}')
    dir1, dir2 = comparison_directories
    with mock.patch("recursivist.cli.display_comparison") as display:
        result = runner.invoke(app, ["compare", dir1, dir2])
    assert result.exit_code == 0
    assert display.call_args.kwargs["icon_style"] == "emoji"


def test_malformed_user_config_warns_and_uses_defaults(
    runner: CliRunner, sample_directory: str
) -> None:
    _write_user_config('{"icon_style": ')
    result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert "Ignoring user configuration" in result.output
    assert "📄" in result.output


def test_explicit_icon_style_does_not_read_user_config(
    runner: CliRunner, sample_directory: str
) -> None:
    """A flag settles the style, so a bad saved value is not even reported."""
    _write_user_config('{"icon_style": "bogus"}')
    result = runner.invoke(
        app, ["visualize", sample_directory, "--icon-style", "emoji"]
    )
    assert result.exit_code == 0
    assert "Ignoring" not in result.output


def test_config_set_repairs_invalid_value(runner: CliRunner) -> None:
    path = _write_user_config('{"icon_style": "bogus"}')
    result = runner.invoke(app, ["config", "set", "icon-style", "nerd"])
    assert result.exit_code == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {"icon_style": "nerd"}


def test_config_set_keeps_entries_it_does_not_recognize(runner: CliRunner) -> None:
    path = _write_user_config('{"colour": "blue", "icon_style": "emoji"}')
    result = runner.invoke(app, ["config", "set", "icon-style", "nerd"])
    assert result.exit_code == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "colour": "blue",
        "icon_style": "nerd",
    }


@pytest.mark.parametrize(
    "stored",
    ['{"icon-style": "emoji"}', '{"icon_style": "emoji", "icon-style": "emoji"}'],
    ids=["dashed", "both-spellings"],
)
def test_config_set_replaces_dashed_spelling(
    runner: CliRunner, sample_directory: str, stored: str
) -> None:
    """A hand-written ``icon-style`` entry must not shadow the saved value."""
    path = _write_user_config(stored)
    result = runner.invoke(app, ["config", "set", "icon-style", "nerd"])
    assert result.exit_code == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {"icon_style": "nerd"}
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        runner.invoke(app, ["visualize", sample_directory])
    assert display_tree.call_args.kwargs["icon_style"] == "nerd"


def test_config_set_replaces_malformed_file(runner: CliRunner) -> None:
    path = _write_user_config('{"icon_style": ')
    result = runner.invoke(app, ["config", "set", "icon-style", "nerd"])
    assert result.exit_code == 0
    assert "Ignoring user configuration" in result.output
    assert json.loads(path.read_text(encoding="utf-8")) == {"icon_style": "nerd"}


@pytest.mark.parametrize("key", ["icon-style", "icon_style"])
@pytest.mark.parametrize(
    "stored",
    ['{"icon_style": "nerd"}', '{"icon-style": "nerd"}', '{"icon_style": 3}'],
    ids=["underscored", "dashed", "invalid-value"],
)
def test_config_unset_removes_saved_value(
    runner: CliRunner, sample_directory: str, key: str, stored: str
) -> None:
    path = _write_user_config(stored)
    result = runner.invoke(app, ["config", "unset", key])
    assert result.exit_code == 0
    assert f"Configuration updated: {key} unset" in result.output
    assert json.loads(path.read_text(encoding="utf-8")) == {}
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        visualized = runner.invoke(app, ["visualize", sample_directory])
    assert "Ignoring" not in visualized.output
    assert display_tree.call_args.kwargs["icon_style"] == "emoji"


def test_config_unset_removes_both_spellings(runner: CliRunner) -> None:
    path = _write_user_config('{"icon_style": "nerd", "icon-style": "emoji"}')
    result = runner.invoke(app, ["config", "unset", "icon-style"])
    assert result.exit_code == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {}


def test_config_unset_removes_unrecognized_key_and_its_warning(
    runner: CliRunner, sample_directory: str
) -> None:
    """``unset`` takes keys ``set`` would reject, to clear an unrecognized entry."""
    path = _write_user_config('{"colour": "blue", "icon_style": "nerd"}')
    before = runner.invoke(app, ["visualize", sample_directory])
    assert "Ignoring unknown configuration key 'colour'" in before.output

    result = runner.invoke(app, ["config", "unset", "colour"])
    assert result.exit_code == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {"icon_style": "nerd"}
    after = runner.invoke(app, ["visualize", sample_directory])
    assert "Ignoring" not in after.output


def test_config_unset_falls_back_to_project_config(
    runner: CliRunner, sample_directory: str
) -> None:
    _write_user_config('{"icon_style": "emoji"}')
    _write_project_config(sample_directory, "nerd")
    assert runner.invoke(app, ["config", "unset", "icon-style"]).exit_code == 0
    with mock.patch.object(cli_module, "display_tree") as display_tree:
        runner.invoke(app, ["visualize", sample_directory])
    assert display_tree.call_args.kwargs["icon_style"] == "nerd"


def test_config_unset_key_that_is_not_saved_changes_nothing(
    runner: CliRunner,
) -> None:
    text = '{"colour": "blue",   "icon_style": "nerd"}'
    path = _write_user_config(text)
    result = runner.invoke(app, ["config", "unset", "colur"])
    assert result.exit_code == 0
    assert "Nothing to unset: colur is not saved" in result.output
    assert "saved keys: colour, icon_style" in result.output
    assert path.read_text(encoding="utf-8") == text


def test_config_unset_without_a_config_file_creates_nothing(
    runner: CliRunner,
) -> None:
    path = _user_config_path()
    result = runner.invoke(app, ["config", "unset", "icon-style"])
    assert result.exit_code == 0
    assert result.output.strip() == "Nothing to unset: icon-style is not saved"
    assert not path.exists()


def test_config_unset_leaves_an_unusable_file_alone(runner: CliRunner) -> None:
    text = '{"icon_style": '
    path = _write_user_config(text)
    result = runner.invoke(app, ["config", "unset", "icon-style"])
    assert result.exit_code == 0
    assert "Ignoring user configuration" in result.output
    assert "Nothing to unset" in result.output
    assert path.read_text(encoding="utf-8") == text


def test_config_unset_requires_a_key(runner: CliRunner) -> None:
    result = runner.invoke(app, ["config", "unset"])
    assert result.exit_code == 2


@pytest.mark.parametrize(
    "key", ["colour", "two words", "it's", "--depth", "-x", "a;b", ""]
)
def test_unknown_key_warning_gives_a_working_unset_command(
    runner: CliRunner, key: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Running the command from the warning removes the entry and the warning."""
    from recursivist.config import load_config

    path = _write_user_config(json.dumps({key: "blue", "icon_style": "nerd"}))
    with caplog.at_level(logging.WARNING, logger="recursivist"):
        load_config()
    command = caplog.messages[0].split("To remove it, run: ")[1]
    program, *args = shlex.split(command)
    assert program == "recursivist"

    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {"icon_style": "nerd"}
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="recursivist"):
        assert load_config() == {"icon_style": "nerd"}
    assert caplog.messages == []
