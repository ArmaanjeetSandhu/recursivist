"""Tests for file-name similarity sorting.

Covers the :func:`recursivist.core.sort_files_by_similarity` helper, the
``sort_by_similarity`` branch of :func:`recursivist.core.sort_files_by_type`
(including its precedence relative to the numeric metric sorts), and that the
ordering is deterministic and independent of input order.
"""

import random
from typing import Any

import pytest

from recursivist._models import FileEntry
from recursivist.core import sort_files_by_similarity, sort_files_by_type


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
