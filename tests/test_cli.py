"""CLI command tests (recursivist.cli): visualize, export, compare, completion."""

import json
import os
import re
import shutil
from typing import Any

import pytest
from typer.testing import CliRunner

from recursivist.cli import app, parse_list_option
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
        (["value1 value2 value3"], ["value1", "value2", "value3"]),
        (["value1", "value2", "value3"], ["value1", "value2", "value3"]),
        (["value1 value2", "value3 value4"], ["value1", "value2", "value3", "value4"]),
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


def test_visualize_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str
) -> None:
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" in result.stdout
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" in result.stdout


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
    ["txt", "json", "html", "md", "jsx", "txt json", "txt json html md jsx"],
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
            assert os.path.basename(sample_directory) in content


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
    result = runner.invoke(app, ["export", sample_directory, "--format", "invalid"])
    assert result.exit_code == 1
    assert any(
        "Unsupported export format" in record.message for record in caplog.records
    )


def test_export_with_sort_options(
    runner: CliRunner, sample_directory: str, output_dir: str
) -> None:
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
            "--sort-by-size",
            "--sort-by-mtime",
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
    assert "(max depth reached)" in result.stdout
    assert "file2.txt" not in result.stdout
    assert "different.txt" not in result.stdout


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
    assert "Directory Comparison" in content
    assert "file1.txt" in content
    assert "dir1_only.txt" in content
    assert "dir2_only.txt" in content


def test_compare_with_full_path(
    runner: CliRunner, comparison_directories: tuple[str, str]
) -> None:
    dir1, dir2 = comparison_directories
    result = runner.invoke(app, ["compare", dir1, dir2, "--full-path"])

    assert result.exit_code == 0
    assert "dir1" in result.stdout
    assert "dir2" in result.stdout
    assert "Full file paths are shown" in result.stdout

    clean_output = "".join(result.stdout.split())
    dir1_clean = "".join(dir1.replace(os.sep, "/").split())
    dir2_clean = "".join(dir2.replace(os.sep, "/").split())

    has_full_path = dir1_clean in clean_output or dir2_clean in clean_output

    assert has_full_path, "No full paths found in the output"


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


def test_completion_command(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def mock_get_completion(shell: str) -> str:
        if shell not in ["bash", "zsh", "fish", "powershell"]:
            raise ValueError(f"Unsupported shell: {shell}")
        return f"# {shell} completion script"

    monkeypatch.setattr(
        "typer.completion.get_completion_inspect_parameters", mock_get_completion
    )
    for shell in ["bash", "zsh", "fish", "powershell"]:
        result = runner.invoke(app, ["completion", shell])
        assert result.exit_code == 0
    result = runner.invoke(app, ["completion", "invalid"])
    assert result.exit_code == 1
    assert any("Unsupported shell" in record.message for record in caplog.records)


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
    assert "(max depth reached)" in result.stdout
    assert "level2" not in result.stdout
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" in result.stdout
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
    assert "(max depth reached)" in result.stdout


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
    assert "Directory Comparison" in content
    assert "level1" in content
    assert "level2" in content
    assert "level1_file.txt" in content
    assert "different_root.txt" in content
    assert "level3" not in content or (
        "level3" in content and "max depth reached" in content
    )
    assert "(max depth reached)" in content


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
    assert "(max depth reached)" in result.stdout


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
                file_name = file if isinstance(file, str) else file[0]
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
            file_name = file_item if isinstance(file_item, str) else file_item[0]
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
    files_at_root = [
        f if isinstance(f, str) else f[0] for f in structure.get("_files", [])
    ]
    assert "test_file1.py" in files_at_root, "Root test_file1.py should be included"
    assert "regular_file.txt" not in files_at_root, (
        "Non-matching files should be excluded"
    )
    include_patterns = [re.compile(r"regular_file\.txt$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        files_at_root = [
            f if isinstance(f, str) else f[0] for f in structure.get("_files", [])
        ]
        assert "regular_file.txt" in files_at_root, "Regular file should be included"
        assert "test_file1.py" not in files_at_root, "Test file should be excluded"
    with open(os.path.join(pattern_test_directory, "unique_test_pattern.py"), "w") as f:
        f.write("# Unique test file")
    include_patterns = [re.compile(r"unique_test_pattern\.py$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        files = [f if isinstance(f, str) else f[0] for f in structure["_files"]]
        assert "unique_test_pattern.py" in files, "Unique test file should be included"
