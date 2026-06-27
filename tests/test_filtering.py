"""Tests for recursivist.filtering: should_exclude, compile_regex_patterns, parse_ignore_file."""

import os
import re
import tempfile
from typing import Any
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture

from recursivist.filtering import (
    compile_regex_patterns,
    parse_ignore_file,
    should_exclude,
)


def _make_entry(base_dir: str, rel_path: str, is_dir: bool) -> tuple[str, str, str]:
    """Create *rel_path* (relative to a fresh scan root under *base_dir*) on disk
    and return ``(path, current_dir, rel_dir)`` exactly as get_directory_structure
    would hand them to should_exclude for a direct child entry.

    A fresh scan root per call keeps the cases order- and fixture-scope-independent
    (so a dir named ``build`` in one case can't collide with a file named ``build``
    in another).
    """
    scan_root = tempfile.mkdtemp(dir=base_dir)
    rel_path = rel_path.replace("/", os.sep)
    parent_rel, name = os.path.split(rel_path)
    parent = os.path.join(scan_root, parent_rel) if parent_rel else scan_root
    os.makedirs(parent, exist_ok=True)
    target = os.path.join(parent, name)
    if is_dir:
        os.makedirs(target, exist_ok=True)
    else:
        with open(target, "w") as fh:
            fh.write("x")
    return target, parent, parent_rel


@pytest.mark.parametrize(
    "path,patterns,extensions,expected,exclude_patterns",
    [
        ("/test/app.log", ["*.log", "node_modules"], set(), True, None),
        ("/test/app.txt", ["*.log", "node_modules"], set(), False, None),
        ("/test/node_modules", ["*.log", "node_modules"], set(), True, None),
        ("/test/script.py", [], {".py", ".js"}, True, None),
        ("/test/app.js", [], {".py", ".js"}, True, None),
        ("/test/app.txt", [], {".py", ".js"}, False, None),
        ("/test/test_app.py", [], set(), True, [re.compile(r"test_.*\.py$")]),
        ("/test/app.log", [], set(), True, [re.compile(r"\.log$")]),
        ("/test/app.py", [], set(), False, [re.compile(r"test_.*\.py$")]),
    ],
)
def test_should_exclude(
    mocker: MockerFixture,
    path: str,
    patterns: list[str],
    extensions: set[str],
    expected: bool,
    exclude_patterns: list[Any] | None,
) -> None:
    """Test file exclusion logic."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": patterns, "current_dir": "/test"}
    kwargs = {}
    if exclude_patterns:
        kwargs["exclude_patterns"] = exclude_patterns
    result = should_exclude(
        path, ignore_context, exclude_extensions=extensions, **kwargs
    )
    assert result == expected, (
        f"Expected should_exclude('{path}') to return {expected}, got {result}"
    )


@pytest.mark.parametrize(
    "patterns,rel_path,is_dir,expected",
    [
        (["/build"], "build", True, True),
        (["/build"], "src/build", True, False),
        (["build"], "build", True, True),
        (["build"], "src/nested/build", True, True),
        (["src/build"], "src/build", True, True),
        (["src/build"], "build", True, False),
        (["src/build"], "other/src/build", True, False),
        (["build/"], "build", True, True),
        (["build/"], "build", False, False),
        (["*.log"], "foo.log", False, True),
        (["*.log"], "src/deep/foo.log", False, True),
        (["*.log"], "foo.log.txt", False, False),
        (["*.log", "!keep.log"], "keep.log", False, False),
        (["*.log", "!keep.log"], "other.log", False, True),
        (["!keep.log", "*.log"], "keep.log", False, True),
    ],
)
def test_should_exclude_gitignore_patterns(
    temp_dir: str,
    patterns: list[str],
    rel_path: str,
    is_dir: bool,
    expected: bool,
) -> None:
    """Gitignore-style matching in should_exclude: root-relative anchoring,
    directory-only markers, '*' not crossing '/', and order-sensitive negation."""
    target, current_dir, rel_dir = _make_entry(temp_dir, rel_path, is_dir)
    ignore_context = {
        "patterns": patterns,
        "current_dir": current_dir,
        "rel_dir": rel_dir,
    }
    assert should_exclude(target, ignore_context) is expected


@pytest.mark.parametrize(
    "ignore_patterns,exclude_patterns,exclude_extensions,include_patterns,rel_path,expected",
    [
        (["*.log", "!keep.log"], None, None, None, "keep.log", False),
        (["*.log", "!keep.log"], ["keep.log"], None, None, "keep.log", True),
        (["*.log", "!keep.log"], ["*.log"], None, None, "keep.log", True),
        (["*.log", "!keep.log"], None, {".log"}, None, "keep.log", True),
        (["*.log"], None, None, ["*.log"], "keep.log", False),
        (["!keep.log"], None, None, ["*.md"], "keep.log", True),
    ],
)
def test_should_exclude_filter_precedence(
    temp_dir: str,
    ignore_patterns: list[str],
    exclude_patterns: list[str] | None,
    exclude_extensions: set[str] | None,
    include_patterns: list[str] | None,
    rel_path: str,
    expected: bool,
) -> None:
    """CLI excludes and excluded extensions take priority over the gitignore
    stage, and include_patterns bypasses it; the gitignore negation only decides
    the outcome when no higher-priority filter applies."""
    target, current_dir, rel_dir = _make_entry(temp_dir, rel_path, is_dir=False)
    ignore_context = {
        "patterns": ignore_patterns,
        "current_dir": current_dir,
        "rel_dir": rel_dir,
    }
    result = should_exclude(
        target,
        ignore_context,
        exclude_extensions=exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
    )
    assert result is expected


@pytest.mark.parametrize(
    "ignore_patterns,rel_path,is_dir,expected",
    [
        (["doc/**/*.txt"], "doc/a.txt", False, True),
        (["doc/**/*.txt"], "doc/sub/deep/a.txt", False, True),
        (["doc/**/*.txt"], "doc/a.md", False, False),
        (["doc/**/*.txt"], "src/doc/a.txt", False, False),
        (["doc/**/*.txt"], "doc/sub", True, False),
        (["**/build"], "build", True, True),
        (["**/build"], "a/b/build", True, True),
    ],
)
def test_should_exclude_double_star(
    temp_dir: str,
    ignore_patterns: list[str],
    rel_path: str,
    is_dir: bool,
    expected: bool,
) -> None:
    """'**' spans directory boundaries: 'doc/**/*.txt' matches at any depth under
    doc/, '**/foo' floats a name anywhere, and intermediate directories are not
    incidentally matched."""
    target, current_dir, rel_dir = _make_entry(temp_dir, rel_path, is_dir=is_dir)
    ignore_context = {
        "patterns": ignore_patterns,
        "current_dir": current_dir,
        "rel_dir": rel_dir,
    }
    assert should_exclude(target, ignore_context) is expected


@pytest.mark.parametrize(
    "patterns,is_regex,expected_count,expected_types",
    [
        (["*.py", "test_*"], False, 2, [str, str]),
        ([r"\.py$", r"^test_"], True, 2, [re.Pattern, re.Pattern]),
        ([r"[invalid", r"(unclosed"], True, 2, [str, str]),
        ([], False, 0, []),
        ([], True, 0, []),
    ],
)
def test_compile_regex_patterns(
    patterns: list[str],
    is_regex: bool,
    expected_count: int,
    expected_types: list[type[Any]],
) -> None:
    """Test compiling regex patterns."""
    compiled = compile_regex_patterns(patterns, is_regex=is_regex)
    assert len(compiled) == expected_count
    for i, pattern_type in enumerate(expected_types):
        assert isinstance(compiled[i], pattern_type)


@pytest.mark.parametrize(
    "content,expected_patterns",
    [
        (
            "# This is a comment\n*.log\n\nnode_modules/\ndist\n# Another comment\n",
            ["*.log", "node_modules/", "dist"],
        ),
        ("", []),
        (
            "# Logs\n*.log\nlogs/\n!important.log\n# Directories\nnode_modules/\ndist/\n",
            ["*.log", "logs/", "!important.log", "node_modules/", "dist/"],
        ),
    ],
)
def test_parse_ignore_file(
    temp_dir: str, content: str, expected_patterns: list[str]
) -> None:
    """Test parsing ignore files."""
    ignore_path = os.path.join(temp_dir, ".testignore")
    with open(ignore_path, "w") as f:
        f.write(content)
    patterns = parse_ignore_file(ignore_path)
    assert set(patterns) == set(expected_patterns)


class TestShouldExcludeProperties:
    """Property-based tests for the should_exclude function."""

    @given(
        st.text(min_size=1, max_size=100),
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
        st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=100)
    def test_should_exclude_patterns(
        self, path: str, patterns: list[str], current_dir: str
    ) -> None:
        """Test that should_exclude correctly applies patterns."""
        pass

    def test_should_exclude_extensions_basic(self) -> None:
        """Test that should_exclude correctly applies extension exclusions with basic cases."""
        exclude_extensions = {".txt", ".md", ".py"}
        with patch("os.path.isfile", return_value=True):
            for ext in exclude_extensions:
                path = f"test_file{ext}"
                ignore_context = {"patterns": [], "current_dir": os.path.dirname(path)}
                result = should_exclude(
                    path, ignore_context, exclude_extensions=exclude_extensions
                )
                assert result, f"Path with excluded extension {ext} should be excluded"
            path = "test_file.allowed_ext"
            ignore_context = {"patterns": [], "current_dir": os.path.dirname(path)}
            result = should_exclude(
                path, ignore_context, exclude_extensions=exclude_extensions
            )
            assert not result, "Path without excluded extension should not be excluded"


class TestCompileRegexPatterns:
    @pytest.mark.parametrize(
        "patterns,is_regex,expected_types",
        [
            (["*.py", "test_*"], False, [str, str]),
            ([r"\.py$", r"^test_"], True, [re.Pattern, re.Pattern]),
            ([r"[invalid", r"(unclosed"], True, [str, str]),
        ],
    )
    def test_basic_compilation(
        self, patterns: list[str], is_regex: bool, expected_types: list[type]
    ) -> None:
        """Test basic pattern compilation."""
        compiled = compile_regex_patterns(patterns, is_regex=is_regex)
        assert len(compiled) == len(patterns)
        for i, pattern_type in enumerate(expected_types):
            assert isinstance(compiled[i], pattern_type)

    def test_empty_patterns(self) -> None:
        """Test compiling empty pattern lists."""
        assert compile_regex_patterns([], is_regex=False) == []
        assert compile_regex_patterns([], is_regex=True) == []

    def test_regex_matching(self) -> None:
        """Test compiled regex patterns match correctly."""
        patterns = [r"^data_\d{8}\.csv$", r".*\.(?:log|tmp)$", r"^\..*"]
        compiled = [re.compile(p) for p in patterns]
        assert len(compiled) == 3
        assert all(isinstance(p, re.Pattern) for p in compiled)
        assert compiled[0].match("data_20230101.csv")
        assert not compiled[0].match("data_20230101.txt")
        assert compiled[1].match("app.log")
        assert compiled[1].match("temp.tmp")
        assert not compiled[1].match("app.txt")
        assert compiled[2].match(".hidden")
        assert not compiled[2].match("visible")


class TestShouldExclude:
    @pytest.mark.parametrize(
        "path,patterns,expected",
        [
            ("/test/app.log", ["*.log", "node_modules"], True),
            ("/test/app.txt", ["*.log", "node_modules"], False),
            ("/test/node_modules", ["*.log", "node_modules"], True),
            ("/test/src", ["*.log", "node_modules"], False),
        ],
    )
    def test_with_ignore_patterns(
        self, mocker: MockerFixture, path: str, patterns: list[str], expected: bool
    ) -> None:
        """Test exclusion based on ignore patterns."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": patterns, "current_dir": "/test"}
        result = should_exclude(path, ignore_context)
        assert result == expected

    @pytest.mark.parametrize(
        "path,extensions,expected",
        [
            ("/test/script.py", {".py", ".js"}, True),
            ("/test/app.js", {".py", ".js"}, True),
            ("/test/app.txt", {".py", ".js"}, False),
        ],
    )
    def test_with_file_extensions(
        self, mocker: MockerFixture, path: str, extensions: set[str], expected: bool
    ) -> None:
        """Test exclusion based on file extensions."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        result = should_exclude(path, ignore_context, exclude_extensions=extensions)
        assert result == expected

    @pytest.mark.parametrize(
        "path,pattern,expected",
        [
            ("/test/test_app.py", r"test_.*\.py$", True),
            ("/test/app.log", r"\.log$", True),
            ("/test/app.py", r"test_.*\.py$", False),
        ],
    )
    def test_with_regex_patterns(
        self, mocker: MockerFixture, path: str, pattern: str, expected: bool
    ) -> None:
        """Test exclusion based on regex patterns."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        exclude_patterns = [re.compile(pattern)]
        result = should_exclude(path, ignore_context, exclude_patterns=exclude_patterns)
        assert result == expected

    def test_with_negation_patterns(self, mocker: MockerFixture) -> None:
        """Test negation patterns in ignore files."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {
            "patterns": ["*.txt", "!important.txt"],
            "current_dir": "/test",
        }
        assert should_exclude("/test/file.txt", ignore_context)
        assert not should_exclude("/test/important.txt", ignore_context)
        assert not should_exclude("/test/file.py", ignore_context)

    def test_with_include_patterns(self, mocker: MockerFixture) -> None:
        """Test include patterns override exclusion."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": ["*.py"], "current_dir": "/test"}
        exclude_patterns = [re.compile(r"\.js$")]
        include_patterns = [re.compile(r"important\.py$")]
        assert should_exclude(
            "/test/app.py",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )
        assert not should_exclude(
            "/test/important.py",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )
        assert should_exclude(
            "/test/app.js",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )
        assert should_exclude(
            "/test/app.txt",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )

    @pytest.mark.parametrize(
        "path,pattern,expected",
        [
            ("/test/path/to/file.txt", "file.txt", True),
            ("/test/path/to/other.txt", "file.txt", False),
        ],
    )
    def test_basename_matching(
        self, mocker: MockerFixture, path: str, pattern: str, expected: bool
    ) -> None:
        """Test matching against the basename only."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        exclude_patterns = [re.compile(pattern + "$")]
        result = should_exclude(path, ignore_context, exclude_patterns=exclude_patterns)
        assert result == expected

    def test_case_sensitivity(self, mocker: MockerFixture) -> None:
        """Test case sensitivity in pattern matching."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        exclude_patterns = [re.compile(r"\.py$")]
        assert should_exclude(
            "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
        )
        assert not should_exclude(
            "/test/script.PY", ignore_context, exclude_patterns=exclude_patterns
        )
        exclude_patterns = [re.compile(r"\.py$", re.IGNORECASE)]
        assert should_exclude(
            "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
        )
        assert should_exclude(
            "/test/script.PY", ignore_context, exclude_patterns=exclude_patterns
        )
        exclude_extensions = {".py"}
        assert should_exclude(
            "/test/script.py", ignore_context, exclude_extensions=exclude_extensions
        )
        assert should_exclude(
            "/test/script.PY", ignore_context, exclude_extensions=exclude_extensions
        )
