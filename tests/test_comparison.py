import html
import os
import re

import pytest
from pytest_mock import MockerFixture
from rich.text import Text

from recursivist.compare import (
    build_comparison_tree,
    compare_directory_structures,
    display_comparison,
    export_comparison,
)


def test_compare_directory_structures(comparison_directories: tuple[str, str]):
    dir1, dir2 = comparison_directories
    structure1, structure2, extensions = compare_directory_structures(dir1, dir2)
    assert "_files" in structure1
    assert "_files" in structure2
    assert "common_dir" in structure1
    assert "common_dir" in structure2
    assert "dir1_only" in structure1
    assert "dir1_only" not in structure2
    assert "dir2_only" not in structure1
    assert "dir2_only" in structure2
    assert "file1.txt" in structure1["_files"]
    assert "file1.txt" in structure2["_files"]
    assert "dir1_only.txt" in structure1["_files"]
    assert "dir1_only.txt" not in structure2.get("_files", [])
    assert "dir2_only.txt" not in structure1.get("_files", [])
    assert "dir2_only.txt" in structure2["_files"]
    assert ".txt" in extensions
    assert ".py" in extensions


@pytest.mark.parametrize(
    "option_name,option_value,expected_result",
    [
        ("show_full_path", True, "file1.txt"),
        ("exclude_dirs", ["exclude_me"], "exclude_me"),
        ("exclude_patterns", [re.compile(r"test_.*")], "test_exclude"),
        ("include_patterns", ["*.txt"], ".py"),
    ],
)
def test_compare_directory_structures_with_options(
    comparison_directories: tuple[str, str],
    option_name: str,
    option_value,
    expected_result: str,
):
    dir1, dir2 = comparison_directories
    if option_name == "exclude_dirs":
        exclude_dir_path1 = os.path.join(dir1, "exclude_me")
        exclude_dir_path2 = os.path.join(dir2, "exclude_me")
        os.makedirs(exclude_dir_path1, exist_ok=True)
        os.makedirs(exclude_dir_path2, exist_ok=True)
        with open(os.path.join(exclude_dir_path1, "excluded1.txt"), "w") as f:
            f.write("This should be excluded")
        with open(os.path.join(exclude_dir_path2, "excluded2.txt"), "w") as f:
            f.write("This should be excluded too")
    elif option_name == "exclude_patterns":
        with open(os.path.join(dir1, "test_exclude1.py"), "w") as f:
            f.write("This should be excluded by pattern")
        with open(os.path.join(dir2, "test_exclude2.py"), "w") as f:
            f.write("This should be excluded by pattern too")
    elif option_name == "include_patterns":
        with open(os.path.join(dir1, "include_me.txt"), "w") as f:
            f.write("This should be included")
        with open(os.path.join(dir1, "exclude_me.log"), "w") as f:
            f.write("This should be excluded")
        with open(os.path.join(dir2, "include_me_too.txt"), "w") as f:
            f.write("This should be included too")
        with open(os.path.join(dir2, "exclude_me_too.log"), "w") as f:
            f.write("This should be excluded too")
    kwargs = {option_name: option_value}
    structure1, structure2, _ = compare_directory_structures(dir1, dir2, **kwargs)
    if option_name == "show_full_path":
        assert "_files" in structure1
        assert "_files" in structure2
        assert isinstance(structure1["_files"][0], tuple)
        assert len(structure1["_files"][0]) == 2
        found = False
        for filename, full_path in structure1["_files"]:
            if filename == "file1.txt":
                found = True
                assert (
                    os.path.basename(dir1) in os.path.dirname(full_path)
                    or "file1.txt" in full_path
                )
        assert found, "Could not find file1.txt with full path in structure1"
    elif option_name == "exclude_dirs":
        assert expected_result not in structure1
        assert expected_result not in structure2
    elif option_name == "exclude_patterns":
        assert not any(
            f.startswith(expected_result) for f in structure1.get("_files", [])
        )
        assert not any(
            f.startswith(expected_result) for f in structure2.get("_files", [])
        )
    elif option_name == "include_patterns":
        for file_name in structure1.get("_files", []):
            actual_name = file_name if isinstance(file_name, str) else file_name[0]
            assert actual_name.endswith(".txt"), (
                f"Non-txt file {actual_name} was included"
            )
        for file_name in structure2.get("_files", []):
            actual_name = file_name if isinstance(file_name, str) else file_name[0]
            assert actual_name.endswith(".txt"), (
                f"Non-txt file {actual_name} was included"
            )
        assert "include_me.txt" in [
            f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
        ]
        assert "exclude_me.log" not in [
            f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
        ]


def test_compare_directory_structures_with_statistics(
    comparison_directories: tuple[str, str],
):
    dir1, dir2 = comparison_directories
    structure1, structure2, _ = compare_directory_structures(
        dir1, dir2, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    for structure in [structure1, structure2]:
        assert "_loc" in structure
        assert "_size" in structure
        assert "_mtime" in structure
    if "_files" in structure1 and structure1["_files"]:
        file_item = structure1["_files"][0]
        if isinstance(file_item, tuple):
            assert len(file_item) > 4


def test_display_comparison(
    comparison_directories: tuple[str, str], capsys: pytest.CaptureFixture[str]
):
    dir1, dir2 = comparison_directories
    display_comparison(dir1, dir2)
    captured = capsys.readouterr()
    assert os.path.basename(dir1) in captured.out
    assert os.path.basename(dir2) in captured.out
    assert "Legend" in captured.out


@pytest.mark.parametrize(
    "option_name,option_value,expected_in_output,expected_not_in_output",
    [
        ("show_full_path", True, "Full file paths are shown", None),
        ("exclude_dirs", ["exclude_me"], None, ["exclude_me", "excluded.txt"]),
        ("exclude_patterns", ["*.log"], None, "test_pattern.log"),
        ("sort_by_loc", True, "lines", None),
        ("sort_by_size", True, ["B", "KB", "MB"], None),
        ("sort_by_mtime", True, ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}"], None),
    ],
)
def test_display_comparison_with_options(
    comparison_directories: tuple[str, str],
    capsys: pytest.CaptureFixture[str],
    option_name: str,
    option_value,
    expected_in_output,
    expected_not_in_output,
):
    dir1, dir2 = comparison_directories
    if option_name == "exclude_dirs":
        exclude_dir1 = os.path.join(dir1, "exclude_me")
        exclude_dir2 = os.path.join(dir2, "exclude_me")
        os.makedirs(exclude_dir1, exist_ok=True)
        os.makedirs(exclude_dir2, exist_ok=True)
        with open(os.path.join(exclude_dir1, "excluded.txt"), "w") as f:
            f.write("This should be excluded")
    elif option_name == "exclude_patterns":
        with open(os.path.join(dir1, "test_pattern.log"), "w") as f:
            f.write("This should be excluded by pattern")
    kwargs = {option_name: option_value}
    display_comparison(dir1, dir2, **kwargs)
    captured = capsys.readouterr()
    if expected_in_output:
        if isinstance(expected_in_output, list):
            assert any(expected in captured.out for expected in expected_in_output), (
                f"None of {expected_in_output} found in output"
            )
        else:
            assert expected_in_output in captured.out, (
                f"{expected_in_output} not found in output"
            )
    if expected_not_in_output:
        if isinstance(expected_not_in_output, list):
            for item in expected_not_in_output:
                assert item not in captured.out, (
                    f"{item} found in output but shouldn't be"
                )
        else:
            assert expected_not_in_output not in captured.out, (
                f"{expected_not_in_output} found in output but shouldn't be"
            )


def test_export_comparison_txt(
    comparison_directories: tuple[str, str], output_dir: str
):
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.txt")
    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "txt", output_path)
    assert "Only HTML format is supported for comparison export" in str(excinfo.value)


def test_export_comparison_html(
    comparison_directories: tuple[str, str], output_dir: str
):
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.html")
    export_comparison(dir1, dir2, "html", output_path)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "<html>" in content
    assert "Directory Comparison" in content
    assert os.path.basename(dir1) in content
    assert os.path.basename(dir2) in content
    assert "dir1_only" in content
    assert "dir2_only" in content


@pytest.mark.parametrize(
    "option_name,option_value,expected_in_output,expected_not_in_output",
    [
        ("show_full_path", True, None, None),
        ("exclude_dirs", ["exclude_me"], None, ["exclude_me", "excluded.txt"]),
        ("exclude_patterns", ["*.log"], None, "test_pattern.log"),
        ("sort_by_loc", True, "lines", None),
        ("sort_by_size", True, ["B", "KB", "MB"], None),
        (
            "sort_by_mtime",
            True,
            ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}", r"format_timestamp"],
            None,
        ),
    ],
)
def test_export_comparison_with_options(
    comparison_directories: tuple[str, str],
    output_dir: str,
    option_name: str,
    option_value,
    expected_in_output,
    expected_not_in_output,
):
    dir1, dir2 = comparison_directories
    if option_name == "exclude_dirs":
        exclude_dir1 = os.path.join(dir1, "exclude_me")
        exclude_dir2 = os.path.join(dir2, "exclude_me")
        os.makedirs(exclude_dir1, exist_ok=True)
        os.makedirs(exclude_dir2, exist_ok=True)
        with open(os.path.join(exclude_dir1, "excluded.txt"), "w") as f:
            f.write("This should be excluded")
    elif option_name == "exclude_patterns":
        with open(os.path.join(dir1, "test_pattern.log"), "w") as f:
            f.write("This should be excluded by pattern")
    output_path = os.path.join(output_dir, f"comparison_{option_name}.html")
    kwargs = {option_name: option_value}
    export_comparison(dir1, dir2, "html", output_path, **kwargs)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    if expected_in_output:
        if isinstance(expected_in_output, list):
            assert any(
                re.search(expected, content) for expected in expected_in_output
            ), f"None of {expected_in_output} found in output"
        else:
            assert expected_in_output in content, (
                f"{expected_in_output} not found in output"
            )
    if expected_not_in_output:
        if isinstance(expected_not_in_output, list):
            for item in expected_not_in_output:
                assert item not in content, f"{item} found in output but shouldn't be"
        else:
            assert expected_not_in_output not in content, (
                f"{expected_not_in_output} found in output but shouldn't be"
            )
    if option_name == "show_full_path":
        file1_path = os.path.join(dir1, "file1.txt").replace(os.sep, "/")
        dir1_only_path = os.path.join(dir1, "dir1_only.txt").replace(os.sep, "/")
        dir2_only_path = os.path.join(dir2, "dir2_only.txt").replace(os.sep, "/")
        found_at_least_one_full_path = False
        for path in [file1_path, dir1_only_path, dir2_only_path]:
            if path in content or html.escape(path) in content:
                found_at_least_one_full_path = True
                break
        if not found_at_least_one_full_path:
            base_name_dir1 = os.path.basename(dir1)
            base_name_dir2 = os.path.basename(dir2)
            for line in content.split("\n"):
                if ("📄" in line or "file" in line) and (
                    base_name_dir1 in line or base_name_dir2 in line
                ):
                    if "/" in line or "\\" in line:
                        found_at_least_one_full_path = True
                        break
        assert found_at_least_one_full_path, "No full paths found in the HTML export"


def test_export_comparison_unsupported_format(
    comparison_directories: tuple[str, str], output_dir: str
):
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.unsupported")
    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "unsupported", output_path)
    assert "Only HTML format is supported for comparison export" in str(excinfo.value)


def test_complex_comparison(
    complex_directory: str, complex_directory_clone: str, output_dir: str
):
    structure1, structure2, _ = compare_directory_structures(
        complex_directory, complex_directory_clone
    )
    assert "src" in structure1
    assert "src" in structure2
    assert "docs" in structure1
    assert "docs" in structure2
    assert "CHANGELOG.md" not in get_file_names(structure1)
    assert "CHANGELOG.md" in get_file_names(structure2)
    assert "utils.py" in get_file_names(structure1, ["src"])
    assert "utils.py" not in get_file_names(structure2, ["src"])
    assert "new_module.py" not in get_file_names(structure1, ["src"])
    assert "new_module.py" in get_file_names(structure2, ["src"])
    output_path = os.path.join(output_dir, "complex_comparison.html")
    export_comparison(complex_directory, complex_directory_clone, "html", output_path)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert "CHANGELOG.md" in content
    assert "utils.py" in content
    assert "new_module.py" in content
    assert "examples.md" in content


def test_build_comparison_tree(
    comparison_directories: tuple[str, str],
    mocker: MockerFixture,
):
    dir1, dir2 = comparison_directories
    structure1, structure2, extensions = compare_directory_structures(dir1, dir2)
    color_map = {ext: f"#{i:06x}" for i, ext in enumerate(extensions)}
    mock_tree = mocker.MagicMock()
    build_comparison_tree(structure1, structure2, mock_tree, color_map)
    assert mock_tree.add.called
    calls = [
        call for call in mock_tree.add.call_args_list if isinstance(call.args[0], Text)
    ]
    has_green_highlight = False
    for call in calls:
        text = call.args[0]
        if hasattr(text.style, "__contains__") and "on green" in text.style:
            has_green_highlight = True
            break
    assert has_green_highlight, "No green highlighting found for unique items"


def test_comparison_with_statistics(
    comparison_directories: tuple[str, str], output_dir: str
):
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison_with_stats.html")
    export_comparison(
        dir1,
        dir2,
        "html",
        output_path,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert "lines" in content
    assert "B" in content or "KB" in content
    has_time_indicator = False
    if re.search(r"Today|Yesterday|\d{4}-\d{2}-\d{2}|format_timestamp", content):
        has_time_indicator = True
    assert has_time_indicator, "No time indicators found in the comparison"


def get_file_names(structure, path=None):
    """Extract file names from a structure, optionally at a specific path."""
    if path is None:
        return [f if isinstance(f, str) else f[0] for f in structure.get("_files", [])]
    else:
        current = structure
        for segment in path:
            if segment in current:
                current = current[segment]
            else:
                return []
        return [f if isinstance(f, str) else f[0] for f in current.get("_files", [])]
