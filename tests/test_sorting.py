"""Tests for recursivist.sorting: sort_files_by_type and sort_files_by_similarity.

``sort_files_by_type`` takes a single ``sort_key`` (plus an optional
``git_markers`` mapping used only for Git-status ordering) and applies exactly
one ordering per call. Combining several metrics is handled upstream in
:mod:`recursivist.flags`, which resolves flags into that single key.
"""

import os
import random
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from recursivist._models import FileEntry
from recursivist.flags import (
    METRIC_GIT,
    METRIC_LOC,
    METRIC_MTIME,
    METRIC_SIMILARITY,
    METRIC_SIZE,
)
from recursivist.sorting import sort_files_by_similarity, sort_files_by_type
from tests.strategies import file_list

ALL_SORT_KEYS = [
    None,
    METRIC_LOC,
    METRIC_SIZE,
    METRIC_MTIME,
    METRIC_GIT,
    METRIC_SIMILARITY,
]


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


def test_similarity_key_matches_helper() -> None:
    """sort_key='similarity' routes through to the similarity helper's ordering."""
    names = ["a_one.py", "b_two.py", "a_three.py", "b_four.py"]
    via_key = _names(sort_files_by_type(names, METRIC_SIMILARITY))
    via_helper = _names(sort_files_by_similarity(names))
    assert via_key == via_helper


def test_default_key_is_extension_then_name() -> None:
    """With no sort key, the default extension+name ordering is used."""
    names = ["c.txt", "b.py", "a.txt", "d.py"]
    order = _names(sort_files_by_type(names, None))
    assert order == ["b.py", "d.py", "a.txt", "c.txt"]


def test_default_key_when_omitted_entirely() -> None:
    """Omitting the sort key argument is equivalent to passing None."""
    names = ["c.txt", "b.py", "a.txt", "d.py"]
    assert _names(sort_files_by_type(names)) == _names(sort_files_by_type(names, None))


@pytest.mark.parametrize(
    "sort_key,expected_order",
    [
        (METRIC_SIZE, ["big.py", "mid.py", "small.py"]),
        (METRIC_LOC, ["big.py", "mid.py", "small.py"]),
    ],
)
def test_numeric_sort_key_orders_descending(
    sort_key: str, expected_order: list[str]
) -> None:
    """A numeric key orders files by that metric, largest first."""
    files = [
        ("small.py", "/p/small.py", 1, 10),
        ("big.py", "/p/big.py", 100, 1000),
        ("mid.py", "/p/mid.py", 50, 500),
    ]
    order = _names(sort_files_by_type(files, sort_key))
    assert order == expected_order


@pytest.mark.parametrize("sort_key", ALL_SORT_KEYS)
def test_empty_input_returns_empty(sort_key: str | None) -> None:
    """sort_files_by_type returns [] for empty input regardless of the key."""
    assert sort_files_by_type([], sort_key) == []


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
            METRIC_LOC,
            ["b.py", "a.py", "c.py"],
        ),
        (
            [
                ("a.py", "/path/to/a.py", 0, 1024),
                ("b.py", "/path/to/b.py", 0, 2048),
                ("c.py", "/path/to/c.py", 0, 512),
            ],
            METRIC_SIZE,
            ["b.py", "a.py", "c.py"],
        ),
    ],
)
def test_sort_files_by_type(
    files: list[Any], sort_key: str | None, expected_order: list[str]
) -> None:
    """Test sorting files by different criteria."""
    sorted_files = sort_files_by_type(files, sort_key)
    sorted_names = _names(sorted_files)
    for i, expected_file in enumerate(expected_order):
        assert sorted_names[i] == expected_file, (
            f"Expected {expected_file} at position {i}, got {sorted_names[i]}"
        )


def test_string_literal_keys_work() -> None:
    """The public contract accepts the bare metric strings, not just constants."""
    files = [
        ("a.py", "/p/a.py", 5),
        ("b.py", "/p/b.py", 10),
        ("c.py", "/p/c.py", 3),
    ]
    assert _names(sort_files_by_type(files, "loc")) == ["b.py", "a.py", "c.py"]


def test_unknown_sort_key_falls_back_to_default() -> None:
    """An unrecognised key is treated as the default extension/name ordering."""
    names = ["c.txt", "b.py", "a.txt", "d.py"]
    order = _names(sort_files_by_type(names, "not-a-real-key"))
    assert order == ["b.py", "d.py", "a.txt", "c.txt"]


def test_sort_by_git_status_groups_and_orders() -> None:
    """Git status orders files M, A, D, U, then clean; alphabetical within a group."""
    files = [
        "e_clean.py",
        "b_mod.py",
        "a_add.py",
        "c_del.py",
        "d_untr.py",
        "a_mod.py",
    ]
    markers = {
        "b_mod.py": "M",
        "a_mod.py": "M",
        "a_add.py": "A",
        "c_del.py": "D",
        "d_untr.py": "U",
    }
    order = _names(sort_files_by_type(files, METRIC_GIT, markers))
    assert order == [
        "a_mod.py",
        "b_mod.py",
        "a_add.py",
        "c_del.py",
        "d_untr.py",
        "e_clean.py",
    ]


def test_sort_by_git_status_without_markers_is_all_clean() -> None:
    """With no markers every file ranks as clean, so ordering is by name."""
    files = ["c.py", "a.py", "b.py"]
    assert _names(sort_files_by_type(files, METRIC_GIT)) == ["a.py", "b.py", "c.py"]
    assert _names(sort_files_by_type(files, METRIC_GIT, {})) == ["a.py", "b.py", "c.py"]


def test_sort_by_git_status_unknown_marker_ranks_as_clean() -> None:
    """An unrecognised status char sorts alongside clean files, after known ones."""
    files = ["tracked.py", "weird.py"]
    markers = {"tracked.py": "M", "weird.py": "Z"}
    assert _names(sort_files_by_type(files, METRIC_GIT, markers)) == [
        "tracked.py",
        "weird.py",
    ]


def test_git_markers_ignored_for_non_git_keys() -> None:
    """git_markers has no effect unless the sort key is git_status."""
    files = [
        ("a.py", "/p/a.py", 5),
        ("b.py", "/p/b.py", 10),
    ]
    markers = {"a.py": "M", "b.py": "U"}
    assert _names(sort_files_by_type(files, METRIC_LOC, markers)) == ["b.py", "a.py"]


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
            filename = f[0] if isinstance(f, tuple) else f
            ext = os.path.splitext(filename)[1].lower()
            extensions.append(ext)
        assert extensions == sorted(extensions), "Files should be sorted by extension"
        for ext in set(extensions):
            names_for_ext = []
            for f in sorted_files:
                filename = f[0] if isinstance(f, tuple) else f
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext == ext:
                    names_for_ext.append(filename.lower())
            assert names_for_ext == sorted(names_for_ext), (
                f"Files with extension {ext} should be sorted by name"
            )

    @given(file_list, st.sampled_from(ALL_SORT_KEYS))
    @settings(max_examples=100)
    def test_sort_preserves_items(
        self,
        files: list[Any],
        sort_key: str | None,
    ) -> None:
        """Any sort key preserves the exact multiset of file names."""
        sorted_files = sort_files_by_type(files, sort_key)
        assert len(sorted_files) == len(files), (
            "Sorted list should have same length as original"
        )
        original_contents = sorted(f[0] if isinstance(f, tuple) else f for f in files)
        sorted_contents = sorted(_names(sorted_files))
        assert sorted_contents == original_contents, (
            "Sorted list should contain the same items as original"
        )

    @given(file_list)
    @settings(max_examples=50)
    def test_output_is_always_fileentries(self, files: list[Any]) -> None:
        """Every returned item is a normalised FileEntry."""
        for key in ALL_SORT_KEYS:
            result = sort_files_by_type(files, key)
            assert all(isinstance(e, FileEntry) for e in result)


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
        sorted_names = _names(sorted_files)
        if len(expected_order) > 0:
            expected_names = [f if isinstance(f, str) else f[0] for f in expected_order]
            assert sorted_names == expected_names, (
                f"Expected {expected_names}, got {sorted_names}"
            )

    @pytest.mark.parametrize(
        "sort_key,files,expected_order",
        [
            (
                METRIC_LOC,
                [
                    ("a.py", "/path/to/a.py", 100),
                    ("b.py", "/path/to/b.py", 50),
                    ("c.py", "/path/to/c.py", 200),
                ],
                ["c.py", "a.py", "b.py"],
            ),
            (
                METRIC_SIZE,
                [
                    ("a.txt", "/path/to/a.txt", 0, 1024),
                    ("b.txt", "/path/to/b.txt", 0, 2048),
                    ("c.txt", "/path/to/c.txt", 0, 512),
                ],
                ["b.txt", "a.txt", "c.txt"],
            ),
            (
                METRIC_MTIME,
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
        sort_key: str,
        files: list[tuple[Any, ...]],
        expected_order: list[str],
    ) -> None:
        sorted_files = sort_files_by_type(files, sort_key)
        sorted_names = _names(sorted_files)
        assert sorted_names == expected_order, (
            f"Expected {expected_order}, got {sorted_names}"
        )

    def test_single_key_is_a_stable_sort(self) -> None:
        """Only the single key drives ordering; equal values keep input order.

        A single key is applied, and Python's stable sort preserves the original
        order among files that tie on that key.
        """
        files = [
            ("a.py", "/path/to/a.py", 100, 1024, 1609459200),
            ("b.py", "/path/to/b.py", 100, 2048, 1609459200),
            ("c.py", "/path/to/c.py", 200, 512, 1609459200),
            ("d.py", "/path/to/d.py", 100, 1024, 1612137600),
        ]
        sorted_names = _names(sort_files_by_type(files, METRIC_LOC))
        assert sorted_names == ["c.py", "a.py", "b.py", "d.py"]
        sorted_names = _names(sort_files_by_type(files, METRIC_SIZE))
        assert sorted_names == ["b.py", "a.py", "d.py", "c.py"]
