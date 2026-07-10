"""Tests for recursivist.compare: compare_directory_structures, build_comparison_tree, display/export comparison."""

import html
import os
import re
import time
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture
from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist._models import FileEntry
from recursivist.compare import (
    _identity_spec_for,
    build_comparison_tree,
    compare_directory_structures,
    display_comparison,
    export_comparison,
)
from recursivist.flags import (
    METRIC_GIT,
    METRIC_LOC,
    METRIC_MTIME,
    METRIC_SIZE,
    DisplayOptions,
)
from tests.strategies import simple_directory_structure

_METRIC_SPECS = {
    "sort_by_loc": DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,)),
    "sort_by_size": DisplayOptions(sort_key=METRIC_SIZE, metrics=(METRIC_SIZE,)),
    "sort_by_mtime": DisplayOptions(sort_key=METRIC_MTIME, metrics=(METRIC_MTIME,)),
}
_ALL_METRICS_SPEC = DisplayOptions(
    sort_key=METRIC_LOC, metrics=(METRIC_LOC, METRIC_SIZE, METRIC_MTIME)
)


def get_file_names(
    structure: dict[str, Any],
    path: list[str] | None = None,
) -> list[str]:
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


@st.composite
def comparison_structure(draw: st.DrawFn, ensure_files: bool = False) -> dict[str, Any]:
    """Generate a structure for comparison testing."""
    structure: dict[str, Any] = {}
    file_list: list[Any] = []
    if ensure_files:
        filename = "sample.txt"
        file_path = "/path/to/sample.txt"
        loc = 100
        size = 1024
        mtime = 1600000000.0
        file_list.append((filename, file_path, loc, size, mtime))
    for _ in range(draw(st.integers(min_value=0, max_value=5))):
        filename = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=20,
            )
        ) + draw(st.sampled_from([".txt", ".py", ".md", ".json", ".js"]))
        if draw(st.booleans()):
            file_path = "/path/to/" + filename
            loc = draw(st.integers(min_value=1, max_value=1000))
            size = draw(st.integers(min_value=1, max_value=10 * 1024 * 1024))
            mtime = draw(st.floats(min_value=1000000, max_value=1672531200))
            file_list.append((filename, file_path, loc, size, mtime))
        else:
            file_list.append(filename)
    structure["_files"] = file_list
    if draw(st.booleans()):
        structure["_loc"] = draw(st.integers(min_value=0, max_value=10000))
    if draw(st.booleans()):
        structure["_size"] = draw(st.integers(min_value=0, max_value=100 * 1024 * 1024))
    if draw(st.booleans()):
        structure["_mtime"] = draw(st.floats(min_value=1000000, max_value=1672531200))
    for _ in range(draw(st.integers(min_value=0, max_value=3))):
        dir_name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=10,
            )
        )
        if draw(st.booleans()) and draw(st.booleans()):
            structure[dir_name] = {"_max_depth_reached": True}
        else:
            sub_structure: dict[str, Any] = {}
            sub_file_list: list[Any] = []
            for _ in range(draw(st.integers(min_value=0, max_value=3))):
                sub_filename = draw(
                    st.text(
                        alphabet=st.characters(
                            whitelist_categories=("Lu", "Ll", "Nd"),
                            whitelist_characters="_-",
                        ),
                        min_size=1,
                        max_size=15,
                    )
                ) + draw(st.sampled_from([".txt", ".py", ".md"]))
                sub_file_list.append(sub_filename)
            sub_structure["_files"] = sub_file_list
            if draw(st.booleans()):
                sub_structure["_loc"] = draw(st.integers(min_value=0, max_value=5000))
            if draw(st.booleans()):
                sub_structure["_size"] = draw(
                    st.integers(min_value=0, max_value=50 * 1024 * 1024)
                )
            if draw(st.booleans()):
                sub_structure["_mtime"] = draw(
                    st.floats(min_value=1000000, max_value=1672531200)
                )
            structure[dir_name] = sub_structure
    return structure


@st.composite
def comparison_pair(
    draw: st.DrawFn, ensure_files: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate a pair of related structures for comparison testing."""
    base_structure: dict[str, Any] = draw(
        comparison_structure(ensure_files=ensure_files)
    )
    modified_structure: dict[str, Any] = {}
    if "_files" in base_structure:
        modified_files: list[Any] = []
        for file_item in base_structure["_files"]:
            if draw(st.booleans()):
                modified_files.append(file_item)
        for _ in range(draw(st.integers(min_value=0, max_value=3))):
            new_filename = draw(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd"),
                        whitelist_characters="_-",
                    ),
                    min_size=1,
                    max_size=15,
                )
            ) + draw(st.sampled_from([".txt", ".py", ".md", ".json", ".js"]))
            if draw(st.booleans()):
                file_path = "/path/to/" + new_filename
                loc = draw(st.integers(min_value=1, max_value=1000))
                size = draw(st.integers(min_value=1, max_value=10 * 1024 * 1024))
                mtime = draw(st.floats(min_value=1000000, max_value=1672531200))
                modified_files.append((new_filename, file_path, loc, size, mtime))
            else:
                modified_files.append(new_filename)
        modified_structure["_files"] = modified_files
    if (
        "_loc" in base_structure
        and isinstance(base_structure["_loc"], int)
        and draw(st.booleans())
    ):
        modified_structure["_loc"] = base_structure["_loc"] + draw(
            st.integers(min_value=-100, max_value=100)
        )
    if (
        "_size" in base_structure
        and isinstance(base_structure["_size"], int)
        and draw(st.booleans())
    ):
        modified_structure["_size"] = base_structure["_size"] + draw(
            st.integers(min_value=-1024, max_value=1024)
        )
    if (
        "_mtime" in base_structure
        and isinstance(base_structure["_mtime"], (int, float))
        and draw(st.booleans())
    ):
        modified_structure["_mtime"] = base_structure["_mtime"] + draw(
            st.floats(min_value=-86400, max_value=86400)
        )
    for key, value in base_structure.items():
        if key not in ["_files", "_loc", "_size", "_mtime", "_max_depth_reached"]:
            if draw(st.booleans()):
                modified_structure[key] = value
    for _ in range(draw(st.integers(min_value=0, max_value=2))):
        dir_name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=10,
            )
        )
        if dir_name not in modified_structure:
            modified_structure[dir_name] = draw(comparison_structure())
    return (base_structure, modified_structure)


safe_path = st.text(
    alphabet=st.characters(
        blacklist_characters='\0\n\r\\/:*?"<>|',
    ),
    min_size=1,
    max_size=20,
)


def test_compare_directory_structures(comparison_directories: tuple[str, str]) -> None:
    dir1, dir2 = comparison_directories
    structure1, structure2 = compare_directory_structures(dir1, dir2)
    assert "_files" in structure1
    assert "_files" in structure2
    assert "common_dir" in structure1
    assert "common_dir" in structure2
    assert "dir1_only" in structure1
    assert "dir1_only" not in structure2
    assert "dir2_only" not in structure1
    assert "dir2_only" in structure2
    names1 = [f if isinstance(f, str) else f[0] for f in structure1["_files"]]
    names2 = [f if isinstance(f, str) else f[0] for f in structure2["_files"]]
    names1_get = [
        f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
    ]
    names2_get = [
        f if isinstance(f, str) else f[0] for f in structure2.get("_files", [])
    ]
    assert "file1.txt" in names1
    assert "file1.txt" in names2
    assert "dir1_only.txt" in names1
    assert "dir1_only.txt" not in names2_get
    assert "dir2_only.txt" not in names1_get
    assert "dir2_only.txt" in names2


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
    option_value: Any,
    expected_result: str,
) -> None:
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
    structure1, structure2 = compare_directory_structures(dir1, dir2, **kwargs)
    if option_name == "show_full_path":
        assert "_files" in structure1
        assert "_files" in structure2
        assert isinstance(structure1["_files"][0], tuple)
        assert len(structure1["_files"][0]) >= 2
        found = False
        for entry in structure1["_files"]:
            filename, full_path = entry[0], entry[1]
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
        names1 = [
            f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
        ]
        names2 = [
            f if isinstance(f, str) else f[0] for f in structure2.get("_files", [])
        ]
        assert not any(n.startswith(expected_result) for n in names1)
        assert not any(n.startswith(expected_result) for n in names2)
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
) -> None:
    dir1, dir2 = comparison_directories
    structure1, structure2 = compare_directory_structures(
        dir1, dir2, spec=_ALL_METRICS_SPEC
    )
    for structure in [structure1, structure2]:
        assert "_loc" in structure
        assert "_size" in structure
        assert "_mtime" in structure
    if "_files" in structure1 and structure1["_files"]:
        file_item = structure1["_files"][0]
        if isinstance(file_item, tuple):
            assert file_item[4] is not None


def test_display_comparison(
    comparison_directories: tuple[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    dir1, dir2 = comparison_directories
    display_comparison(dir1, dir2)
    captured = capsys.readouterr()
    assert os.path.basename(dir1) in captured.out
    assert os.path.basename(dir2) in captured.out
    assert "Legend" in captured.out


def test_display_comparison_stays_side_by_side_when_names_are_long(
    tmp_path: Any,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Long filenames wrap so the two panels stay side by side.

    A filename wider than half the terminal must break across lines rather than
    widen its panel, so the two directory panels remain on the same terminal
    line regardless of entry length.
    """
    long_name = "a_very_long_filename_that_far_exceeds_half_the_terminal_width.py"
    dir1 = tmp_path / "left"
    dir2 = tmp_path / "right"
    dir1.mkdir()
    dir2.mkdir()
    (dir1 / long_name).write_text("x")
    (dir2 / "short.py").write_text("y")

    monkeypatch.setenv("COLUMNS", "70")
    display_comparison(str(dir1), str(dir2))
    out = capsys.readouterr().out

    header_lines = [
        line
        for line in out.splitlines()
        if "Directory 1:" in line and "Directory 2:" in line
    ]
    assert header_lines, "the two directory panels are not on the same line"

    assert long_name not in out, "the long filename was not wrapped"
    assert "a_very_long_filename" in out, "the wrapped filename is missing entirely"


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
    option_value: Any,
    expected_in_output: str | list[str] | None,
    expected_not_in_output: str | list[str] | None,
) -> None:
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
    if option_name in _METRIC_SPECS:
        display_comparison(dir1, dir2, spec=_METRIC_SPECS[option_name])
    else:
        display_comparison(dir1, dir2, **{option_name: option_value})
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
) -> None:
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.txt")
    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "txt", output_path)
    assert "Only HTML format is supported for comparison export" in str(excinfo.value)


def test_export_comparison_html(
    comparison_directories: tuple[str, str], output_dir: str
) -> None:
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
    option_value: Any,
    expected_in_output: str | list[str] | None,
    expected_not_in_output: str | list[str] | None,
) -> None:
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
    if option_name in _METRIC_SPECS:
        export_comparison(
            dir1, dir2, "html", output_path, spec=_METRIC_SPECS[option_name]
        )
    else:
        export_comparison(
            dir1, dir2, "html", output_path, **{option_name: option_value}
        )
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
) -> None:
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.unsupported")
    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "unsupported", output_path)
    assert "Only HTML format is supported for comparison export" in str(excinfo.value)


def test_complex_comparison(
    complex_directory: str, complex_directory_clone: str, output_dir: str
) -> None:
    structure1, structure2 = compare_directory_structures(
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
) -> None:
    dir1, dir2 = comparison_directories
    structure1, structure2 = compare_directory_structures(dir1, dir2)
    mock_tree = mocker.MagicMock()
    build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
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
) -> None:
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison_with_stats.html")
    export_comparison(
        dir1,
        dir2,
        "html",
        output_path,
        spec=_ALL_METRICS_SPEC,
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


class TestCompareDirectoryStructures:
    """Property-based tests for compare_directory_structures function."""

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=10)
    def test_comparison_returns_structures(self, dir1: str, dir2: str) -> None:
        """Test that compare_directory_structures returns valid structures."""
        with patch("recursivist.compare.get_directory_structure") as mock_get_structure:
            mock_get_structure.side_effect = [
                ({"_files": ["file1.txt"]}, {".txt"}),
                ({"_files": ["file2.txt"]}, {".txt"}),
            ]
            structure1, structure2 = compare_directory_structures(dir1, dir2)
            assert structure1 == {"_files": ["file1.txt"]}, (
                "Should return structure1 from get_directory_structure"
            )
            assert structure2 == {"_files": ["file2.txt"]}, (
                "Should return structure2 from get_directory_structure"
            )
            assert mock_get_structure.call_count == 2, (
                "get_directory_structure should be called twice"
            )
            mock_get_structure.assert_any_call(
                dir1,
                None,
                None,
                None,
                exclude_patterns=None,
                include_patterns=None,
                max_depth=0,
                show_full_path=False,
                sort_by_loc=False,
                sort_by_size=False,
                sort_by_mtime=False,
                show_git_status=False,
                git_status_map=None,
            )
            mock_get_structure.assert_any_call(
                dir2,
                None,
                None,
                None,
                exclude_patterns=None,
                include_patterns=None,
                max_depth=0,
                show_full_path=False,
                sort_by_loc=False,
                sort_by_size=False,
                sort_by_mtime=False,
                show_git_status=False,
                git_status_map=None,
            )

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=5)
    def test_comparison_with_options(self, dir1: str, dir2: str) -> None:
        """Test compare_directory_structures with various options."""
        with patch("recursivist.compare.get_directory_structure") as mock_get_structure:
            mock_get_structure.side_effect = [
                ({"_files": ["file1.txt"]}, {".txt"}),
                ({"_files": ["file2.txt"]}, {".txt"}),
            ]
            exclude_dirs = ["node_modules", "dist"]
            exclude_extensions = {".pyc", ".log"}
            exclude_patterns = [r"\.tmp$", r"^test_"]
            include_patterns = [r"\.py$"]
            max_depth = 2
            compare_directory_structures(
                dir1,
                dir2,
                exclude_dirs,
                ".gitignore",
                exclude_extensions,
                exclude_patterns=exclude_patterns,
                include_patterns=include_patterns,
                max_depth=max_depth,
                show_full_path=True,
                spec=_ALL_METRICS_SPEC,
            )
            mock_get_structure.assert_any_call(
                dir1,
                exclude_dirs,
                ".gitignore",
                exclude_extensions,
                exclude_patterns=ANY,
                include_patterns=ANY,
                max_depth=max_depth,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
                show_git_status=False,
                git_status_map=None,
            )


class TestBuildComparisonTree:
    """Property-based tests for build_comparison_tree function."""

    @given(
        structures=comparison_pair(ensure_files=True),
    )
    @settings(max_examples=10)
    def test_build_comparison_tree(
        self,
        structures: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Test that build_comparison_tree builds a valid tree."""
        structure1, structure2 = structures
        mock_tree = MagicMock()
        mock_tree.add.return_value = mock_tree
        build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
        assert mock_tree.add.call_count > 0, "Tree.add should have been called"

    @given(
        structures=comparison_pair(ensure_files=True),
    )
    @settings(max_examples=5)
    def test_build_comparison_tree_with_options(
        self,
        structures: tuple[dict[str, Any], dict[str, Any]],
    ) -> None:
        """Test build_comparison_tree with various options."""
        structure1, structure2 = structures
        mock_tree = MagicMock()
        mock_tree.add.return_value = mock_tree
        build_comparison_tree(
            structure1,
            structure2,
            mock_tree,
            _ALL_METRICS_SPEC,
            show_full_path=True,
        )
        assert mock_tree.add.call_count > 0, "Tree.add should have been called"


class TestDisplayComparison:
    """Property-based tests for display_comparison function."""

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=5)
    def test_display_comparison(self, dir1: str, dir2: str) -> None:
        """Test that display_comparison calls the necessary functions."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare.Console") as mock_console,
            patch("recursivist.compare.build_comparison_tree") as mock_build_tree,
            patch("recursivist.compare.Tree") as mock_tree,
        ):
            mock_console.return_value.width = 100
            mock_compare.return_value = ({"_files": []}, {"_files": []})
            display_comparison(dir1, dir2)
            mock_compare.assert_called_once()
            mock_tree.assert_called()
            mock_build_tree.assert_called()
            mock_console.return_value.print.assert_called()

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=5)
    def test_display_comparison_with_options(self, dir1: str, dir2: str) -> None:
        """Test display_comparison with various options."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []})
            display_comparison(
                dir1,
                dir2,
                exclude_dirs=["node_modules"],
                ignore_file=".gitignore",
                exclude_extensions={".log"},
                exclude_patterns=["test_*"],
                include_patterns=["*.py"],
                use_regex=True,
                max_depth=2,
                show_full_path=True,
                spec=_ALL_METRICS_SPEC,
            )
            mock_compare.assert_called_once_with(
                dir1,
                dir2,
                ["node_modules"],
                ".gitignore",
                {".log"},
                exclude_patterns=ANY,
                include_patterns=ANY,
                max_depth=2,
                show_full_path=True,
                spec=_ALL_METRICS_SPEC,
            )


class TestExportComparison:
    """Property-based tests for export_comparison function."""

    @given(
        dir1=safe_path,
        dir2=safe_path,
        output_path=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison(self, dir1: str, dir2: str, output_path: str) -> None:
        """Test that export_comparison exports to HTML."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare._export_comparison_to_html") as mock_export_html,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []})
            export_comparison(dir1, dir2, "html", output_path)
            mock_export_html.assert_called_once()

    @given(
        dir1=safe_path,
        dir2=safe_path,
        output_path=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison_invalid_format(
        self, dir1: str, dir2: str, output_path: str
    ) -> None:
        """Test that export_comparison raises an error for invalid formats."""
        with pytest.raises(ValueError) as excinfo:
            export_comparison(dir1, dir2, "invalid", output_path)
        assert "Only HTML format is supported" in str(excinfo.value)

    @given(
        dir1=safe_path,
        dir2=safe_path,
        output_path=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison_with_options(
        self, dir1: str, dir2: str, output_path: str
    ) -> None:
        """Test export_comparison with various options."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare._export_comparison_to_html") as _,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []})
            export_comparison(
                dir1,
                dir2,
                "html",
                output_path,
                exclude_dirs=["node_modules"],
                ignore_file=".gitignore",
                exclude_extensions={".log"},
                exclude_patterns=["test_*"],
                include_patterns=["*.py"],
                use_regex=True,
                max_depth=2,
                show_full_path=True,
                spec=_ALL_METRICS_SPEC,
            )
            mock_compare.assert_called_once_with(
                dir1,
                dir2,
                ["node_modules"],
                ".gitignore",
                {".log"},
                exclude_patterns=ANY,
                include_patterns=ANY,
                max_depth=2,
                show_full_path=True,
                spec=_ALL_METRICS_SPEC,
            )


class TestExportComparisonToHTML:
    """Property-based tests for _export_comparison_to_html function."""

    @given(
        structures=comparison_pair(),
        dir1_name=safe_path,
        dir2_name=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison_to_html(
        self,
        structures: tuple[dict[str, Any], dict[str, Any]],
        dir1_name: str,
        dir2_name: str,
    ) -> None:
        """Test that _export_comparison_to_html creates a valid HTML file."""
        structure1, structure2 = structures
        comparison_data: dict[str, Any] = {
            "dir1": {
                "path": f"/path/to/{dir1_name}",
                "name": dir1_name,
                "structure": structure1,
            },
            "dir2": {
                "path": f"/path/to/{dir2_name}",
                "name": dir2_name,
                "structure": structure2,
            },
            "metadata": {
                "exclude_patterns": [],
                "include_patterns": [],
                "pattern_type": "glob",
                "max_depth": 0,
                "show_full_path": False,
                "metrics": [],
                "sort_key": None,
                "show_loc": False,
                "show_size": False,
                "show_mtime": False,
            },
        }
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            from recursivist.compare import _export_comparison_to_html

            with patch.object(mock_file, "write") as mock_write:
                _export_comparison_to_html(comparison_data, "output.html")
                mock_open.assert_called_once_with("output.html", "w", encoding="utf-8")
                assert mock_write.call_count > 0, "No data was written to the file"


class TestBuildComparisonTreeProperties:
    """Property-based tests for build_comparison_tree function."""

    @given(
        structure1=simple_directory_structure(),
        structure2=simple_directory_structure(),
    )
    @settings(max_examples=20)
    def test_build_comparison_tree(
        self,
        structure1: dict[str, Any],
        structure2: dict[str, Any],
    ) -> None:
        """Test that build_comparison_tree successfully builds a tree."""
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree

        def count_files_and_folders(struct: dict[str, Any]) -> int:
            count = 0
            if "_files" in struct:
                count += len(struct["_files"])
            for key, value in struct.items():
                if (
                    key != "_files"
                    and key != "_loc"
                    and key != "_size"
                    and key != "_mtime"
                    and key != "_max_depth_reached"
                    and isinstance(value, dict)
                ):
                    count += 1
                    count += count_files_and_folders(value)
            return count

        expected_calls = count_files_and_folders(structure1) + count_files_and_folders(
            structure2
        )
        build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
        if expected_calls > 0:
            assert mock_tree.add.call_count > 0, (
                "build_comparison_tree should make at least one call to tree.add when there are files or folders"
            )
        else:
            pass


class TestBuildComparisonTreeStructures:
    def test_identical_structures(
        self,
        mock_tree: MagicMock,
        simple_structure: dict[str, Any],
    ) -> None:
        """Test comparing identical structures."""
        build_comparison_tree(
            simple_structure, simple_structure, mock_tree, DisplayOptions()
        )
        assert mock_tree.add.call_count == 3
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        styles = [str(call.args[0].style) for call in calls]
        assert not any("on green" in style for style in styles)
        assert not any("on red" in style for style in styles)

    def test_different_files(self, mock_tree: MagicMock) -> None:
        """Test comparing structures with different files."""
        structure1 = {"_files": ["file1.txt", "common.py"]}
        structure2 = {"_files": ["file2.txt", "common.py"]}
        build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        texts_and_styles = [
            (call.args[0].plain, str(call.args[0].style)) for call in calls
        ]
        assert any(
            "file1.txt" in text and "on green" in style
            for text, style in texts_and_styles
        )
        assert any(
            "common.py" in text and "on green" not in style and "on red" not in style
            for text, style in texts_and_styles
        )

    def test_different_directories(
        self, mock_tree: MagicMock, mock_subtree: MagicMock
    ) -> None:
        """Test comparing structures with different directories."""
        structure1 = {
            "dir1": {"_files": ["file1.txt"]},
            "common_dir": {"_files": ["common.py"]},
        }
        structure2 = {
            "dir2": {"_files": ["file2.txt"]},
            "common_dir": {"_files": ["common.py"]},
        }
        mock_tree.add.return_value = mock_subtree
        build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
        dir_calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        dir_texts_styles = [
            (call.args[0].plain, str(call.args[0].style))
            for call in dir_calls
            if "📁" in call.args[0].plain
        ]
        assert any(
            "dir1" in text and "green" in style for text, style in dir_texts_styles
        )
        common_dir_calls = [
            call
            for call in mock_tree.add.call_args_list
            if not isinstance(call.args[0], Text) and "common_dir" in str(call.args[0])
        ]
        assert len(common_dir_calls) > 0

    def test_with_statistics(self, mock_tree: MagicMock) -> None:
        """Test comparison tree with statistics."""
        now = time.time()
        structure1 = {
            "_loc": 100,
            "_size": 1024,
            "_mtime": now,
            "_files": [("file1.txt", "/path/to/file1.txt", 50, 512, now)],
        }
        structure2 = {
            "_loc": 200,
            "_size": 2048,
            "_mtime": now,
            "_files": [("file2.txt", "/path/to/file2.txt", 100, 1024, now)],
        }
        build_comparison_tree(
            structure1,
            structure2,
            mock_tree,
            _ALL_METRICS_SPEC,
        )
        calls = [
            str(call.args[0])
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        has_stats = False
        for call in calls:
            if (
                "lines" in call
                and "B" in call
                and (
                    "Today" in call
                    or "Yesterday" in call
                    or re.search(r"\d{4}-\d{2}-\d{2}", call)
                )
            ):
                has_stats = True
                break
        assert has_stats, "No statistics indicators found in comparison tree"

    def test_with_complex_structures(
        self, mock_tree: MagicMock, mock_subtree: MagicMock
    ) -> None:
        """Test comparison with complex nested structures."""
        structure1 = {
            "_files": ["common1.txt", "only1.txt"],
            "dir1": {
                "_files": ["dir1_file.txt"],
                "nested1": {"_files": ["nested1_file.txt"]},
            },
            "common_dir": {"_files": ["common_file.txt", "only_in_1.txt"]},
        }
        structure2 = {
            "_files": ["common1.txt", "only2.txt"],
            "dir2": {
                "_files": ["dir2_file.txt"],
                "nested2": {"_files": ["nested2_file.txt"]},
            },
            "common_dir": {"_files": ["common_file.txt", "only_in_2.txt"]},
        }
        all_calls = []

        def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
            all_calls.append((args, kwargs))
            return mock_subtree

        mock_tree.add.side_effect = side_effect
        mock_subtree.add.side_effect = side_effect
        build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
        file_texts_styles = []
        for args, _ in all_calls:
            if args and isinstance(args[0], Text) and "📄" in args[0].plain:
                file_texts_styles.append((args[0].plain, str(args[0].style)))
        assert any(
            "only1.txt" in text and "on green" in style
            for text, style in file_texts_styles
        )
        assert any(
            "only_in_1.txt" in text and "on green" in style
            for text, style in file_texts_styles
        )
        assert any(
            "common1.txt" in text and "on green" not in style and "on red" not in style
            for text, style in file_texts_styles
        )

    def test_with_max_depth(
        self, mock_tree: MagicMock, mock_subtree: MagicMock
    ) -> None:
        """Test comparison tree with max depth indicators."""
        structure1 = {
            "_files": ["file1.txt"],
            "subdir": {
                "_max_depth_reached": True,
            },
        }
        structure2 = {"_files": ["file2.txt"], "subdir": {"_files": ["subfile.txt"]}}
        mock_tree.add.return_value = mock_subtree
        build_comparison_tree(structure1, structure2, mock_tree, DisplayOptions())
        subtree_calls = [
            call.args[0]
            for call in mock_subtree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        assert any("max depth reached" in text.plain for text in subtree_calls)


_GIT_SPEC_DISPLAY = DisplayOptions(show_git_status=True)
_GIT_SPEC_SORT = DisplayOptions(sort_key=METRIC_GIT, show_git_status=True)


def _plain_texts(mock_tree: MagicMock) -> list[str]:
    """Collect the plain text of every rich ``Text`` added to a mock tree."""
    return [
        call.args[0].plain
        for call in mock_tree.add.call_args_list
        if call.args and isinstance(call.args[0], Text)
    ]


class TestCompareGitStatus:
    """Git-status support for the compare command (display, sort, export)."""

    def test_compare_directory_structures_fetches_git_per_directory(
        self, mocker: MockerFixture
    ) -> None:
        """With git enabled, get_git_status is called once per directory and
        each map is threaded into the matching scan."""
        gs = mocker.patch(
            "recursivist.compare.get_git_status",
            side_effect=[{"a.py": "M"}, {"b.py": "U"}],
        )
        scan = mocker.patch(
            "recursivist.compare.get_directory_structure",
            side_effect=[({"_files": []}, set()), ({"_files": []}, set())],
        )
        compare_directory_structures("d1", "d2", spec=_GIT_SPEC_DISPLAY)

        assert gs.call_count == 2
        gs.assert_any_call("d1")
        gs.assert_any_call("d2")
        first, second = scan.call_args_list
        assert first.kwargs["show_git_status"] is True
        assert first.kwargs["git_status_map"] == {"a.py": "M"}
        assert second.kwargs["git_status_map"] == {"b.py": "U"}

    def test_compare_directory_structures_no_git_when_not_requested(
        self, mocker: MockerFixture
    ) -> None:
        """Without git flags, git status is never looked up and scans are told
        not to compute it."""
        gs = mocker.patch("recursivist.compare.get_git_status")
        scan = mocker.patch(
            "recursivist.compare.get_directory_structure",
            side_effect=[({"_files": []}, set()), ({"_files": []}, set())],
        )
        compare_directory_structures("d1", "d2", spec=DisplayOptions())

        gs.assert_not_called()
        for call in scan.call_args_list:
            assert call.kwargs["show_git_status"] is False
            assert call.kwargs["git_status_map"] is None

    def test_sort_by_git_status_fetches_status_without_display_flag(
        self, mocker: MockerFixture
    ) -> None:
        """A git *sort* alone (no --git-status) still triggers status lookup."""
        gs = mocker.patch(
            "recursivist.compare.get_git_status",
            side_effect=[{}, {}],
        )
        mocker.patch(
            "recursivist.compare.get_directory_structure",
            side_effect=[({"_files": []}, set()), ({"_files": []}, set())],
        )
        compare_directory_structures(
            "d1", "d2", spec=DisplayOptions(sort_key=METRIC_GIT)
        )
        assert gs.call_count == 2

    def test_build_comparison_tree_renders_git_badges(self) -> None:
        """Files carry their status badge; deleted files are struck through."""
        structure = {
            "_files": ["mod.py", "del.py"],
            "_git_markers": {"mod.py": "M", "del.py": "D"},
        }
        tree = MagicMock()
        tree.add.return_value = tree
        build_comparison_tree(structure, {}, tree, _GIT_SPEC_DISPLAY)

        texts = _plain_texts(tree)
        assert any("mod.py" in t and "[M]" in t for t in texts)
        assert any("del.py" in t and "[D]" in t for t in texts)

        deleted_text = next(
            call.args[0]
            for call in tree.add.call_args_list
            if call.args
            and isinstance(call.args[0], Text)
            and "del.py" in call.args[0].plain
        )
        assert "strike" in str(deleted_text.style)

    def test_build_comparison_tree_no_badges_without_flag(self) -> None:
        """Markers present in the structure are ignored when git is off."""
        structure = {
            "_files": ["mod.py"],
            "_git_markers": {"mod.py": "M"},
        }
        tree = MagicMock()
        tree.add.return_value = tree
        build_comparison_tree(structure, {}, tree, DisplayOptions())
        assert all("[M]" not in t for t in _plain_texts(tree))

    def test_build_comparison_tree_badges_on_other_side_files(self) -> None:
        """Files unique to the *other* structure use the other side's markers."""
        this_structure: dict[str, Any] = {"_files": []}
        other_structure = {
            "_files": ["only_other.py"],
            "_git_markers": {"only_other.py": "A"},
        }
        tree = MagicMock()
        tree.add.return_value = tree
        build_comparison_tree(this_structure, other_structure, tree, _GIT_SPEC_DISPLAY)
        assert any("only_other.py" in t and "[A]" in t for t in _plain_texts(tree))

    def test_build_comparison_tree_git_sort_order(self) -> None:
        """git_status sort orders files modified, added, deleted, untracked,
        then clean."""
        structure = {
            "_files": ["clean.py", "unt.py", "del.py", "add.py", "mod.py"],
            "_git_markers": {
                "unt.py": "U",
                "del.py": "D",
                "add.py": "A",
                "mod.py": "M",
            },
        }
        tree = MagicMock()
        tree.add.return_value = tree
        build_comparison_tree(structure, {}, tree, _GIT_SPEC_SORT)

        names = _plain_texts(tree)
        seq = ["mod.py", "add.py", "del.py", "unt.py", "clean.py"]
        positions = [next(i for i, t in enumerate(names) if s in t) for s in seq]
        assert positions == sorted(positions)

    def test_export_comparison_html_includes_git_badges(
        self, mocker: MockerFixture, tmp_path: Any
    ) -> None:
        """Exported HTML contains Git badges, a legend block, and a
        struck-through deleted file."""
        mocker.patch(
            "recursivist.compare.get_git_status",
            side_effect=[{"mod.py": "M", "del.py": "D"}, {}],
        )
        mocker.patch(
            "recursivist.compare.compile_regex_patterns",
            side_effect=lambda patterns, use_regex: list(patterns),
        )

        def fake_scan(
            directory: str, *args: Any, **kwargs: Any
        ) -> tuple[dict[str, Any], set[str]]:
            if kwargs.get("git_status_map"):
                return (
                    {
                        "_files": [
                            FileEntry(name="mod.py", path="mod.py"),
                            FileEntry(name="del.py", path="del.py"),
                        ],
                        "_git_markers": {"mod.py": "M", "del.py": "D"},
                    },
                    {".py"},
                )
            return ({"_files": []}, set())

        mocker.patch(
            "recursivist.compare.get_directory_structure", side_effect=fake_scan
        )
        out = str(tmp_path / "cmp.html")
        export_comparison("d1", "d2", "html", out, spec=_GIT_SPEC_DISPLAY)

        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert 'class="git-badge git-m"' in content
        assert 'class="git-badge git-d"' in content
        assert 'info-label">Git Status:' in content
        assert "line-through" in content

    def test_export_comparison_html_no_git_section_without_flag(
        self, mocker: MockerFixture, tmp_path: Any
    ) -> None:
        """No git legend block appears when git status is disabled."""
        mocker.patch(
            "recursivist.compare.compile_regex_patterns",
            side_effect=lambda patterns, use_regex: list(patterns),
        )
        mocker.patch(
            "recursivist.compare.get_directory_structure",
            side_effect=[({"_files": []}, set()), ({"_files": []}, set())],
        )
        out = str(tmp_path / "cmp.html")
        export_comparison("d1", "d2", "html", out, spec=DisplayOptions())
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert 'info-label">Git Status:' not in content

    def test_display_comparison_legend_mentions_git(
        self, mocker: MockerFixture
    ) -> None:
        """The terminal legend gains a git-status marker line when enabled."""
        mocker.patch("recursivist.compare.get_git_status", side_effect=[{}, {}])
        mocker.patch(
            "recursivist.compare.get_directory_structure",
            side_effect=[({"_files": []}, set()), ({"_files": []}, set())],
        )
        recorded: dict[str, Console] = {}

        def capture_console() -> Console:
            console = Console(record=True, width=200)
            recorded["console"] = console
            return console

        mocker.patch("recursivist.compare.Console", side_effect=capture_console)
        display_comparison("d1", "d2", spec=_GIT_SPEC_DISPLAY)
        text = recorded["console"].export_text()
        assert "Git status markers" in text


def _styles_by_text(mock_tree: MagicMock) -> dict[str, str]:
    """Map each added ``Text``'s plain content to its style string."""
    return {
        call.args[0].plain: str(call.args[0].style)
        for call in mock_tree.add.call_args_list
        if call.args and isinstance(call.args[0], Text)
    }


class TestCompareAnnotationAwareDifferences:
    """A differing annotation on identically named files marks them unique.

    The comparison highlight keys on the *displayed* annotation, so two files
    that share a name but differ in an active metric (LOC/size/mtime) or Git
    status are shown as unique to their side rather than silently treated as
    equal, while files whose annotations match stay shared.
    """

    def _render(
        self, structure: dict[str, Any], other: dict[str, Any], spec: DisplayOptions
    ) -> dict[str, str]:
        tree = MagicMock()
        tree.add.return_value = tree
        build_comparison_tree(structure, other, tree, spec)
        return _styles_by_text(tree)

    def test_differing_loc_marks_same_named_file_unique(self) -> None:
        """Same name, different LOC under --sort-by-loc: highlighted, not shared."""
        spec = DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,))
        this = {"_files": [FileEntry(name="shared.py", path="shared.py", loc=3)]}
        other = {"_files": [FileEntry(name="shared.py", path="shared.py", loc=1)]}

        styles = self._render(this, other, spec)
        assert styles["📄 shared.py (3 lines)"] == "on green"
        assert styles["📄 shared.py (1 line)"] == "on red"

    def test_matching_loc_keeps_same_named_file_shared(self) -> None:
        """Same name, identical LOC: not highlighted (still shared)."""
        spec = DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,))
        this = {"_files": [FileEntry(name="shared.py", path="shared.py", loc=5)]}
        other = {"_files": [FileEntry(name="shared.py", path="shared.py", loc=5)]}

        styles = self._render(this, other, spec)
        assert styles["📄 shared.py (5 lines)"] == ""

    def test_no_annotation_ignores_metric_differences(self) -> None:
        """Without an active metric, stored LOC differences do not split files."""
        this = {"_files": [FileEntry(name="shared.py", path="shared.py", loc=3)]}
        other = {"_files": [FileEntry(name="shared.py", path="shared.py", loc=1)]}

        styles = self._render(this, other, DisplayOptions())
        assert styles["📄 shared.py"] == ""

    def test_differing_git_status_marks_same_named_file_unique(self) -> None:
        """Same name, different Git status: highlighted on each side."""
        this = {
            "_files": [FileEntry(name="foo.py", path="foo.py")],
            "_git_markers": {"foo.py": "M"},
        }
        other = {
            "_files": [FileEntry(name="foo.py", path="foo.py")],
            "_git_markers": {},
        }

        styles = self._render(this, other, _GIT_SPEC_DISPLAY)
        assert styles["📄 foo.py [M]"] == "on green"
        assert styles["📄 foo.py"] == "on red"

    def test_matching_git_status_keeps_same_named_file_shared(self) -> None:
        """Same name, identical Git status: not highlighted."""
        this = {
            "_files": [FileEntry(name="foo.py", path="foo.py")],
            "_git_markers": {"foo.py": "M"},
        }
        other = {
            "_files": [FileEntry(name="foo.py", path="foo.py")],
            "_git_markers": {"foo.py": "M"},
        }

        styles = self._render(this, other, _GIT_SPEC_DISPLAY)
        assert styles["📄 foo.py [M]"] == ""

    def test_html_export_marks_differing_loc_unique(
        self, mocker: MockerFixture, tmp_path: Any
    ) -> None:
        """The HTML exporter tags a same-named, differing-LOC file as unique."""
        mocker.patch(
            "recursivist.compare.compile_regex_patterns",
            side_effect=lambda patterns, use_regex: list(patterns),
        )
        mocker.patch(
            "recursivist.compare.get_directory_structure",
            side_effect=[
                (
                    {"_files": [FileEntry(name="shared.py", path="shared.py", loc=3)]},
                    {".py"},
                ),
                (
                    {"_files": [FileEntry(name="shared.py", path="shared.py", loc=1)]},
                    {".py"},
                ),
            ],
        )
        out = str(tmp_path / "cmp.html")
        export_comparison(
            "d1",
            "d2",
            "html",
            out,
            spec=DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,)),
        )
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert 'class="file-unique-left"' in content
        assert 'class="file-unique-right"' in content


_GITHUB_URL = "https://github.com/owner/repo"


class TestCompareRemoteIdentity:
    """Local-vs-remote comparisons drop remote-unsupported annotations from
    identity.

    A hosted repository cannot supply a meaningful per-file modification time
    or Git status, so those annotations must not split otherwise-matching files
    when one side is a GitHub repository — even though they are still displayed.
    Line count and size, which are computed from file contents, keep splitting.
    """

    def _render_with_identity(
        self,
        structure: dict[str, Any],
        other: dict[str, Any],
        spec: DisplayOptions,
        identity_spec: DisplayOptions,
    ) -> dict[str, str]:
        tree = MagicMock()
        tree.add.return_value = tree
        build_comparison_tree(structure, other, tree, spec, identity_spec=identity_spec)
        return _styles_by_text(tree)

    def test_identity_spec_local_vs_local_is_full_spec(self) -> None:
        """With two local paths, identity uses the full display spec."""
        spec = DisplayOptions(metrics=(METRIC_LOC, METRIC_MTIME), show_git_status=True)
        assert _identity_spec_for("/a", "/b", spec) is spec

    def test_identity_spec_drops_mtime_and_git_for_github_side(self) -> None:
        """With a GitHub side, mtime and Git status leave the identity."""
        spec = DisplayOptions(
            metrics=(METRIC_LOC, METRIC_SIZE, METRIC_MTIME), show_git_status=True
        )
        reduced = _identity_spec_for("/local", _GITHUB_URL, spec)
        assert reduced.metrics == (METRIC_LOC, METRIC_SIZE)
        assert reduced.show_git_status is False

    def test_identity_spec_reduced_when_first_side_is_github(self) -> None:
        """The GitHub side may be either argument."""
        spec = DisplayOptions(metrics=(METRIC_MTIME,), show_git_status=True)
        reduced = _identity_spec_for(_GITHUB_URL, "/local", spec)
        assert reduced.metrics == ()
        assert reduced.show_git_status is False

    def test_mtime_difference_does_not_split_when_dropped(self) -> None:
        """Same name and LOC, differing mtime: shared once identity drops mtime."""
        spec = DisplayOptions(metrics=(METRIC_LOC, METRIC_MTIME))
        identity_spec = spec.without_remote_unsupported()
        this = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=1.6e9)]}
        remote = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=0.0)]}

        styles = self._render_with_identity(this, remote, spec, identity_spec)

        assert all(style == "" for style in styles.values())
        assert sum("a.py" in text for text in styles) == 1

    def test_mtime_difference_still_splits_when_identity_keeps_it(self) -> None:
        """The same inputs *do* split when identity keeps mtime (local-vs-local)."""
        spec = DisplayOptions(metrics=(METRIC_LOC, METRIC_MTIME))
        this = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=1.6e9)]}
        other = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=0.0)]}

        styles = self._render_with_identity(this, other, spec, spec)
        assert "on green" in styles.values()
        assert "on red" in styles.values()

    def test_loc_difference_still_splits_with_github_side(self) -> None:
        """LOC is content-derived, so it keeps splitting even against a remote."""
        spec = DisplayOptions(metrics=(METRIC_LOC,))
        identity_spec = spec.without_remote_unsupported()
        this = {"_files": [FileEntry(name="a.py", path="a.py", loc=5)]}
        remote = {"_files": [FileEntry(name="a.py", path="a.py", loc=9)]}

        styles = self._render_with_identity(this, remote, spec, identity_spec)
        assert styles["📄 a.py (5 lines)"] == "on green"
        assert styles["📄 a.py (9 lines)"] == "on red"

    def test_display_comparison_threads_reduced_identity_for_github(
        self, mocker: MockerFixture
    ) -> None:
        """The terminal entry point passes the reduced identity spec downstream."""
        mocker.patch(
            "recursivist.compare.compare_directory_structures",
            return_value=({"_files": []}, {"_files": []}),
        )
        mock_console = MagicMock()
        mock_console.width = 100
        mocker.patch("recursivist.compare.Console", return_value=mock_console)
        captured: dict[str, DisplayOptions | None] = {}
        real = build_comparison_tree

        def spy(*args: Any, **kwargs: Any) -> None:
            captured.setdefault("identity_spec", kwargs.get("identity_spec"))
            return real(*args, **kwargs)

        mocker.patch("recursivist.compare.build_comparison_tree", side_effect=spy)
        display_comparison(
            "/local",
            _GITHUB_URL,
            spec=DisplayOptions(
                metrics=(METRIC_LOC, METRIC_MTIME), show_git_status=True
            ),
        )
        identity_spec = captured["identity_spec"]
        assert identity_spec is not None
        assert identity_spec.metrics == (METRIC_LOC,)
        assert identity_spec.show_git_status is False

    def test_export_html_github_side_ignores_mtime_for_identity(
        self, mocker: MockerFixture, tmp_path: Any
    ) -> None:
        """HTML export: a shared file differing only in mtime is not unique."""
        mocker.patch(
            "recursivist.compare.compile_regex_patterns",
            side_effect=lambda patterns, use_regex: list(patterns),
        )
        local = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=1.6e9)]}
        remote = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=0.0)]}
        mocker.patch(
            "recursivist.compare.compare_directory_structures",
            return_value=(local, remote),
        )
        out = str(tmp_path / "cmp.html")
        export_comparison(
            "/local",
            _GITHUB_URL,
            "html",
            out,
            spec=DisplayOptions(metrics=(METRIC_LOC, METRIC_MTIME)),
        )
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert "a.py" in content
        assert 'class="file-unique-left"' not in content
        assert 'class="file-unique-right"' not in content

    def test_export_html_local_vs_local_splits_on_mtime(
        self, mocker: MockerFixture, tmp_path: Any
    ) -> None:
        """The same inputs between two local paths still split on mtime."""
        mocker.patch(
            "recursivist.compare.compile_regex_patterns",
            side_effect=lambda patterns, use_regex: list(patterns),
        )
        left = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=1.6e9)]}
        right = {"_files": [FileEntry(name="a.py", path="a.py", loc=5, mtime=0.0)]}
        mocker.patch(
            "recursivist.compare.compare_directory_structures",
            return_value=(left, right),
        )
        out = str(tmp_path / "cmp.html")
        export_comparison(
            "/local-a",
            "/local-b",
            "html",
            out,
            spec=DisplayOptions(metrics=(METRIC_LOC, METRIC_MTIME)),
        )
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert 'class="file-unique-left"' in content
        assert 'class="file-unique-right"' in content
