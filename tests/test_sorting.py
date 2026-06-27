"""Tests for recursivist.sorting: sort_files_by_type and sort_files_by_similarity."""

import os
import random
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from recursivist._models import FileEntry
from recursivist.sorting import sort_files_by_similarity, sort_files_by_type
from tests.strategies import file_list


def _names(entries: list[Any]) -> list[str]:
    """Extract bare names from sorted output (always FileEntry here)."""
    out = []
    for item in entries:
        if isinstance(item, FileEntry):
            out.append(item.name)
        elif isinstance(item, tuple):
            out.append(item[0])
        else:
            out.append(item)
    return out


def _is_contiguous(order: list[str], group: list[str]) -> bool:
    """True if every member of *group* appears as one unbroken run in *order*."""
    positions = sorted(order.index(name) for name in group)
    return positions == list(range(positions[0], positions[0] + len(group)))


@pytest.mark.parametrize(
    "names,groups",
    [
        (
            [
                "auth_login.py",
                "user_model.py",
                "auth_logout.py",
                "user_view.py",
                "auth_token.py",
                "user_service.py",
            ],
            [
                ["auth_login.py", "auth_logout.py", "auth_token.py"],
                ["user_model.py", "user_view.py", "user_service.py"],
            ],
        ),
        (
            ["config.json", "main.py", "config.yaml", "main.js"],
            [["config.json", "config.yaml"], ["main.py", "main.js"]],
        ),
        (
            [
                "report_2021.pdf",
                "summary.txt",
                "report_2023.pdf",
                "report_2022.pdf",
            ],
            [["report_2021.pdf", "report_2022.pdf", "report_2023.pdf"]],
        ),
    ],
)
def test_similar_names_are_grouped(names: list[str], groups: list[list[str]]) -> None:
    """Each expected group of similar names ends up contiguous in the output."""
    order = _names(sort_files_by_similarity(names))
    assert sorted(order) == sorted(names), "no files added or dropped"
    for group in groups:
        assert _is_contiguous(order, group), f"{group} not contiguous in {order}"


def test_chain_starts_from_alphabetically_first_name() -> None:
    """The deterministic anchor is the case-insensitively first name."""
    names = ["zebra.py", "Apple.py", "mango.py"]
    order = _names(sort_files_by_similarity(names))
    assert order[0] == "Apple.py"


@pytest.mark.parametrize(
    "names",
    [
        [],
        ["only.py"],
        ["b.py", "a.py"],
    ],
)
def test_trivial_inputs(names: list[str]) -> None:
    """Empty/single/pair inputs are handled and yield alphabetical order."""
    order = _names(sort_files_by_similarity(names))
    assert order == sorted(names, key=str.lower)


def test_accepts_strings_tuples_and_fileentries() -> None:
    """Mixed raw input shapes are all normalised to FileEntry and ordered."""
    mixed: list[Any] = [
        "auth_a.py",
        ("auth_b.py", "/p/auth_b.py"),
        FileEntry(name="auth_c.py", path="auth_c.py"),
    ]
    result = sort_files_by_similarity(mixed)
    assert all(isinstance(e, FileEntry) for e in result)
    assert sorted(_names(result)) == ["auth_a.py", "auth_b.py", "auth_c.py"]


def test_case_insensitive_grouping() -> None:
    """Ratio is computed case-insensitively, so case variants still cluster."""
    names = ["README.md", "readme_old.md", "LICENSE", "license_notes.txt"]
    order = _names(sort_files_by_similarity(names))
    assert _is_contiguous(order, ["README.md", "readme_old.md"])
    assert _is_contiguous(order, ["LICENSE", "license_notes.txt"])


def test_ordering_is_deterministic_and_input_order_independent() -> None:
    """Shuffling the input never changes the resulting order."""
    base = [
        "user_controller.py",
        "report_2023.pdf",
        "auth_service.py",
        "user_model.py",
        "report_2021.pdf",
        "auth_middleware.py",
        "README.md",
        "report_2022.pdf",
        "user_view.py",
        "config.yaml",
        "config.json",
        "auth_utils.py",
    ]
    reference = _names(sort_files_by_similarity(base))
    for seed in range(100):
        shuffled = random.Random(seed).sample(base, len(base))
        assert _names(sort_files_by_similarity(shuffled)) == reference


def test_sort_files_by_type_similarity_matches_helper() -> None:
    """The sort_by_similarity flag routes through to the helper's ordering."""
    names = ["a_one.py", "b_two.py", "a_three.py", "b_four.py"]
    via_flag = _names(sort_files_by_type(names, sort_by_similarity=True))
    via_helper = _names(sort_files_by_similarity(names))
    assert via_flag == via_helper


def test_sort_files_by_type_default_is_unaffected_when_flag_off() -> None:
    """With the flag off, the default extension+name ordering is preserved."""
    names = ["c.txt", "b.py", "a.txt", "d.py"]
    order = _names(sort_files_by_type(names, sort_by_similarity=False))
    assert order == ["b.py", "d.py", "a.txt", "c.txt"]


@pytest.mark.parametrize(
    "sort_kwargs,expected_order",
    [
        ({"sort_by_size": True}, ["big.py", "mid.py", "small.py"]),
        ({"sort_by_loc": True}, ["big.py", "mid.py", "small.py"]),
    ],
)
def test_numeric_sort_overrides_similarity(
    sort_kwargs: dict[str, bool], expected_order: list[str]
) -> None:
    """When combined with a numeric sort, similarity is ignored."""
    files = [
        ("small.py", "/p/small.py", 1, 10),
        ("big.py", "/p/big.py", 100, 1000),
        ("mid.py", "/p/mid.py", 50, 500),
    ]
    order = _names(sort_files_by_type(files, sort_by_similarity=True, **sort_kwargs))
    assert order == expected_order


def test_empty_through_sort_files_by_type() -> None:
    """sort_files_by_type returns [] for empty input regardless of the flag."""
    assert sort_files_by_type([], sort_by_similarity=True) == []


@pytest.mark.parametrize(
    "files,sort_key,expected_order",
    [
        (["c.txt", "b.py", "a.txt", "d.py"], None, ["b.py", "d.py", "a.txt", "c.txt"]),
        (
            [
                ("a.py", "/path/to/a.py", 5),
                ("b.py", "/path/to/b.py", 10),
                ("c.py", "/path/to/c.py", 3),
            ],
            "sort_by_loc",
            ["b.py", "a.py", "c.py"],
        ),
        (
            [
                ("a.py", "/path/to/a.py", 0, 1024),
                ("b.py", "/path/to/b.py", 0, 2048),
                ("c.py", "/path/to/c.py", 0, 512),
            ],
            "sort_by_size",
            ["b.py", "a.py", "c.py"],
        ),
    ],
)
def test_sort_files_by_type(
    files: list[Any], sort_key: str | None, expected_order: list[str]
) -> None:
    """Test sorting files by different criteria."""
    kwargs = {}
    if sort_key:
        kwargs[sort_key] = True
    sorted_files = sort_files_by_type(files, **kwargs)
    sorted_names = []
    for item in sorted_files:
        if isinstance(item, tuple):
            sorted_names.append(item[0])
        else:
            sorted_names.append(item)
    for i, expected_file in enumerate(expected_order):
        assert sorted_names[i] == expected_file, (
            f"Expected {expected_file} at position {i}, got {sorted_names[i]}"
        )


class TestSortFilesByTypeProperties:
    """Property-based tests for sort_files_by_type function."""

    @given(file_list)
    @settings(max_examples=100)
    def test_sorts_by_extension(self, files: list[Any]) -> None:
        """Test that files are sorted by extension and then by name."""
        sorted_files = sort_files_by_type(files)
        assert len(sorted_files) == len(files), (
            "Sorted list should have same length as original"
        )
        extensions = []
        for f in sorted_files:
            if isinstance(f, tuple):
                filename = f[0]
            else:
                filename = f
            ext = os.path.splitext(filename)[1].lower()
            extensions.append(ext)
        assert extensions == sorted(extensions), "Files should be sorted by extension"
        for ext in set(extensions):
            names_for_ext = []
            for f in sorted_files:
                if isinstance(f, tuple):
                    filename = f[0]
                else:
                    filename = f
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext == ext:
                    names_for_ext.append(filename.lower())
            assert names_for_ext == sorted(names_for_ext), (
                f"Files with extension {ext} should be sorted by name"
            )

    @given(file_list, st.booleans(), st.booleans(), st.booleans())
    @settings(max_examples=100)
    def test_sort_with_stats(
        self,
        files: list[Any],
        sort_by_loc: bool,
        sort_by_size: bool,
        sort_by_mtime: bool,
    ) -> None:
        """Test sort_files_by_type with various sorting options."""
        sorted_files = sort_files_by_type(
            files, sort_by_loc, sort_by_size, sort_by_mtime
        )
        assert len(sorted_files) == len(files), (
            "Sorted list should have same length as original"
        )
        original_contents = set()
        for f in files:
            if isinstance(f, tuple):
                original_contents.add(f[0])
            else:
                original_contents.add(f)
        sorted_contents = set()
        for f in sorted_files:
            if isinstance(f, tuple):
                sorted_contents.add(f[0])
            else:
                sorted_contents.add(f)
        assert sorted_contents == original_contents, (
            "Sorted list should contain the same items as original"
        )


class TestSortFilesByType:
    @pytest.mark.parametrize(
        "input_files,expected_order",
        [
            (["c.txt", "b.py", "a.txt", "d.py"], ["b.py", "d.py", "a.txt", "c.txt"]),
            (
                [
                    ("c.txt", "/path/to/c.txt"),
                    ("b.py", "/path/to/b.py"),
                    ("a.txt", "/path/to/a.txt"),
                    ("d.py", "/path/to/d.py"),
                ],
                [
                    ("b.py", "/path/to/b.py"),
                    ("d.py", "/path/to/d.py"),
                    ("a.txt", "/path/to/a.txt"),
                    ("c.txt", "/path/to/c.txt"),
                ],
            ),
            (
                [
                    "c.txt",
                    ("b.py", "/path/to/b.py"),
                    ("a.txt", "/path/to/a.txt"),
                    "d.py",
                ],
                [
                    ("b.py", "/path/to/b.py"),
                    "d.py",
                    ("a.txt", "/path/to/a.txt"),
                    "c.txt",
                ],
            ),
            (
                [
                    "readme",
                    ".gitignore",
                    "file.txt.bak",
                    ".env.local",
                ],
                [
                    ".gitignore",
                    "readme",
                    "file.txt.bak",
                    ".env.local",
                ],
            ),
            ([], []),
            (
                [
                    "file.tar.gz",
                    "file.min.js",
                    "file.spec.ts",
                    "file.d.ts",
                ],
                [
                    "file.tar.gz",
                    "file.min.js",
                    "file.d.ts",
                    "file.spec.ts",
                ],
            ),
        ],
    )
    def test_sort_by_extension(
        self,
        input_files: list[str | tuple[str, str]],
        expected_order: list[str | tuple[str, str]],
    ) -> None:
        sorted_files = sort_files_by_type(input_files)
        sorted_names = [f if isinstance(f, str) else f[0] for f in sorted_files]
        if len(expected_order) > 0:
            expected_names = [f if isinstance(f, str) else f[0] for f in expected_order]
            assert sorted_names == expected_names, (
                f"Expected {expected_names}, got {sorted_names}"
            )

    @pytest.mark.parametrize(
        "sort_option,files,expected_order",
        [
            (
                "sort_by_loc",
                [
                    ("a.py", "/path/to/a.py", 100),
                    ("b.py", "/path/to/b.py", 50),
                    ("c.py", "/path/to/c.py", 200),
                ],
                ["c.py", "a.py", "b.py"],
            ),
            (
                "sort_by_size",
                [
                    ("a.txt", "/path/to/a.txt", 0, 1024),
                    ("b.txt", "/path/to/b.txt", 0, 2048),
                    ("c.txt", "/path/to/c.txt", 0, 512),
                ],
                ["b.txt", "a.txt", "c.txt"],
            ),
            (
                "sort_by_mtime",
                [
                    ("a.txt", "/path/to/a.txt", 0, 0, 1609459200),
                    ("b.txt", "/path/to/b.txt", 0, 0, 1612137600),
                    ("c.txt", "/path/to/c.txt", 0, 0, 1606780800),
                ],
                ["b.txt", "a.txt", "c.txt"],
            ),
        ],
    )
    def test_sort_by_statistics(
        self,
        sort_option: str,
        files: list[tuple[Any, ...]],
        expected_order: list[str],
    ) -> None:
        kwargs = {sort_option: True}
        sorted_files = sort_files_by_type(files, **kwargs)
        sorted_names = [item[0] for item in sorted_files]
        assert sorted_names == expected_order, (
            f"Expected {expected_order}, got {sorted_names}"
        )

    def test_sort_with_multiple_criteria(self) -> None:
        files = [
            ("a.py", "/path/to/a.py", 100, 1024, 1609459200),
            ("b.py", "/path/to/b.py", 100, 2048, 1609459200),
            ("c.py", "/path/to/c.py", 200, 512, 1609459200),
            ("d.py", "/path/to/d.py", 100, 1024, 1612137600),
        ]
        sorted_files = sort_files_by_type(
            files, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
        )
        sorted_names = [item[0] for item in sorted_files]
        expected_order = ["c.py", "b.py", "d.py", "a.py"]
        assert sorted_names == expected_order, (
            f"Expected {expected_order}, got {sorted_names}"
        )
