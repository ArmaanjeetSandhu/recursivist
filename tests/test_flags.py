"""Tests for recursivist.flags: order-sensitive sort/display flag resolution.

This module resolves sort/display flags into a single :class:`DisplayOptions`.
Flags fall into three families — sorting-only (``--sort-by-similarity``),
combined (``--sort-by-loc/-size/-mtime/-git-status``) and display-only
(``--loc``, ``--size``, ``--mtime``, ``--git-status``) — and are resolved
strictly by their left-to-right order on the command line.
"""

import dataclasses

import pytest

from recursivist.flags import (
    _SPEC_BY_ID,
    FLAG_SPECS,
    METRIC_GIT,
    METRIC_LOC,
    METRIC_MTIME,
    METRIC_SIMILARITY,
    METRIC_SIZE,
    MODE_COMBINED,
    MODE_DISPLAY_ONLY,
    MODE_SORT_ONLY,
    NUMERIC_METRICS,
    DisplayOptions,
    FlagSpec,
    _cli_order_key,
    resolve_display_options,
    resolve_flags,
)


def _spec(flag_id: str) -> FlagSpec:
    return _SPEC_BY_ID[flag_id]


class TestDisplayOptions:
    def test_defaults(self) -> None:
        opts = DisplayOptions()
        assert opts.sort_key is None
        assert opts.metrics == ()
        assert opts.show_git_status is False
        assert opts.show_loc is False
        assert opts.show_size is False
        assert opts.show_mtime is False
        assert opts.sorts_by_metric is False

    def test_show_properties_track_metrics(self) -> None:
        opts = DisplayOptions(metrics=(METRIC_SIZE, METRIC_LOC))
        assert opts.show_loc is True
        assert opts.show_size is True
        assert opts.show_mtime is False

    @pytest.mark.parametrize(
        "sort_key,expected",
        [
            (METRIC_LOC, True),
            (METRIC_SIZE, True),
            (METRIC_MTIME, True),
            (METRIC_GIT, False),
            (METRIC_SIMILARITY, False),
            (None, False),
        ],
    )
    def test_sorts_by_metric(self, sort_key: str | None, expected: bool) -> None:
        assert DisplayOptions(sort_key=sort_key).sorts_by_metric is expected

    def test_is_frozen(self) -> None:
        opts = DisplayOptions()
        with pytest.raises(dataclasses.FrozenInstanceError):
            opts.sort_key = METRIC_LOC  # type: ignore[misc]

    def test_equality(self) -> None:
        assert DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,)) == (
            DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,))
        )
        assert DisplayOptions(metrics=(METRIC_LOC,)) != DisplayOptions(
            metrics=(METRIC_SIZE,)
        )


class TestRegistry:
    def test_numeric_metrics(self) -> None:
        assert NUMERIC_METRICS == (METRIC_LOC, METRIC_SIZE, METRIC_MTIME)
        assert METRIC_GIT not in NUMERIC_METRICS
        assert METRIC_SIMILARITY not in NUMERIC_METRICS

    def test_all_specs_have_unique_ids(self) -> None:
        ids = [spec.id for spec in FLAG_SPECS]
        assert len(ids) == len(set(ids))

    def test_short_flags_are_unique_where_present(self) -> None:
        shorts = [spec.short for spec in FLAG_SPECS if spec.short is not None]
        assert len(shorts) == len(set(shorts))

    def test_long_flags_are_unique(self) -> None:
        longs = [spec.long for spec in FLAG_SPECS]
        assert len(longs) == len(set(longs))

    def test_modes_are_valid(self) -> None:
        valid = {MODE_SORT_ONLY, MODE_COMBINED, MODE_DISPLAY_ONLY}
        assert all(spec.mode in valid for spec in FLAG_SPECS)

    def test_only_similarity_is_sort_only(self) -> None:
        sort_only = [s for s in FLAG_SPECS if s.mode == MODE_SORT_ONLY]
        assert [s.metric for s in sort_only] == [METRIC_SIMILARITY]


class TestResolveFlags:
    def test_empty_is_default(self) -> None:
        assert resolve_flags([]) == DisplayOptions()

    def test_single_combined_numeric(self) -> None:
        opts = resolve_flags([(MODE_COMBINED, METRIC_LOC)])
        assert opts == DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,))

    def test_single_sort_only(self) -> None:
        opts = resolve_flags([(MODE_SORT_ONLY, METRIC_SIMILARITY)])
        assert opts.sort_key == METRIC_SIMILARITY
        assert opts.metrics == ()
        assert opts.show_git_status is False

    def test_single_display_only_numeric(self) -> None:
        opts = resolve_flags([(MODE_DISPLAY_ONLY, METRIC_LOC)])
        assert opts.sort_key is None
        assert opts.metrics == (METRIC_LOC,)

    def test_single_display_only_git(self) -> None:
        opts = resolve_flags([(MODE_DISPLAY_ONLY, METRIC_GIT)])
        assert opts.sort_key is None
        assert opts.metrics == ()
        assert opts.show_git_status is True

    def test_single_combined_git(self) -> None:
        opts = resolve_flags([(MODE_COMBINED, METRIC_GIT)])
        assert opts.sort_key == METRIC_GIT
        assert opts.metrics == ()
        assert opts.show_git_status is True

    def test_first_sorting_flag_wins(self) -> None:
        """Only the first sorting flag takes effect; the later one is discarded."""
        opts = resolve_flags(
            [(MODE_COMBINED, METRIC_LOC), (MODE_COMBINED, METRIC_SIZE)]
        )
        assert opts.sort_key == METRIC_LOC
        assert opts.metrics == (METRIC_LOC,)

    def test_sort_only_winner_suppresses_later_combined(self) -> None:
        """A winning sort-only flag suppresses a later combined flag entirely."""
        opts = resolve_flags(
            [(MODE_SORT_ONLY, METRIC_SIMILARITY), (MODE_COMBINED, METRIC_LOC)]
        )
        assert opts.sort_key == METRIC_SIMILARITY
        assert opts.metrics == ()

    def test_combined_numeric_annotates_before_display_only(self) -> None:
        opts = resolve_flags(
            [(MODE_COMBINED, METRIC_LOC), (MODE_DISPLAY_ONLY, METRIC_SIZE)]
        )
        assert opts.sort_key == METRIC_LOC
        assert opts.metrics == (METRIC_LOC, METRIC_SIZE)

    def test_combined_winner_first_regardless_of_event_order(self) -> None:
        """The combined numeric winner annotates first even if given last."""
        opts = resolve_flags(
            [(MODE_DISPLAY_ONLY, METRIC_SIZE), (MODE_COMBINED, METRIC_LOC)]
        )
        assert opts.metrics == (METRIC_LOC, METRIC_SIZE)

    def test_display_only_order_preserved(self) -> None:
        opts = resolve_flags(
            [
                (MODE_DISPLAY_ONLY, METRIC_MTIME),
                (MODE_DISPLAY_ONLY, METRIC_LOC),
                (MODE_DISPLAY_ONLY, METRIC_SIZE),
            ]
        )
        assert opts.metrics == (METRIC_MTIME, METRIC_LOC, METRIC_SIZE)
        assert opts.show_loc and opts.show_size and opts.show_mtime

    def test_duplicate_display_only_deduplicated(self) -> None:
        opts = resolve_flags(
            [(MODE_DISPLAY_ONLY, METRIC_LOC), (MODE_DISPLAY_ONLY, METRIC_LOC)]
        )
        assert opts.metrics == (METRIC_LOC,)

    def test_combined_git_with_display_numeric(self) -> None:
        """A git-status combined winner adds no numeric metric but sets the badge."""
        opts = resolve_flags(
            [(MODE_COMBINED, METRIC_GIT), (MODE_DISPLAY_ONLY, METRIC_LOC)]
        )
        assert opts.sort_key == METRIC_GIT
        assert opts.metrics == (METRIC_LOC,)
        assert opts.show_git_status is True

    def test_combined_numeric_with_display_git(self) -> None:
        opts = resolve_flags(
            [(MODE_COMBINED, METRIC_LOC), (MODE_DISPLAY_ONLY, METRIC_GIT)]
        )
        assert opts.sort_key == METRIC_LOC
        assert opts.metrics == (METRIC_LOC,)
        assert opts.show_git_status is True

    def test_discarded_combined_numeric_does_not_annotate(self) -> None:
        """Only the winning combined numeric annotates; the discarded one does not."""
        opts = resolve_flags(
            [
                (MODE_COMBINED, METRIC_SIZE),
                (MODE_COMBINED, METRIC_LOC),
                (MODE_DISPLAY_ONLY, METRIC_MTIME),
            ]
        )
        assert opts.sort_key == METRIC_SIZE
        assert opts.metrics == (METRIC_SIZE, METRIC_MTIME)

    def test_git_badge_from_either_source(self) -> None:
        assert resolve_flags([(MODE_DISPLAY_ONLY, METRIC_GIT)]).show_git_status
        assert resolve_flags([(MODE_COMBINED, METRIC_GIT)]).show_git_status
        opts = resolve_flags(
            [(MODE_COMBINED, METRIC_GIT), (MODE_DISPLAY_ONLY, METRIC_GIT)]
        )
        assert opts.show_git_status is True


class TestCliOrderKey:
    def test_long_option_match(self) -> None:
        assert _cli_order_key(_spec("sort_loc"), ["--sort-by-loc"]) == (0, 0)

    def test_long_option_with_value_suffix(self) -> None:
        assert _cli_order_key(_spec("sort_loc"), ["--sort-by-loc=x"]) == (0, 0)

    def test_long_option_absent(self) -> None:
        assert _cli_order_key(_spec("sort_loc"), ["--size", "foo"]) is None

    def test_short_flag_standalone(self) -> None:
        assert _cli_order_key(_spec("sort_loc"), ["-s"]) == (0, 0)

    def test_short_flag_in_bundle_preserves_char_index(self) -> None:
        assert _cli_order_key(_spec("sort_size"), ["-zs"]) == (0, 0)
        assert _cli_order_key(_spec("sort_loc"), ["-zs"]) == (0, 1)

    def test_earliest_position_wins_across_tokens(self) -> None:
        tokens = ["-z", "-s", "-s"]
        assert _cli_order_key(_spec("sort_loc"), tokens) == (1, 0)

    def test_double_dash_terminates_scan(self) -> None:
        assert _cli_order_key(_spec("sort_size"), ["--", "-z"]) is None

    def test_flag_without_short_never_matches_bundle(self) -> None:
        assert _cli_order_key(_spec("disp_size"), ["-sz"]) is None
        assert _cli_order_key(_spec("disp_size"), ["--size"]) == (0, 0)


class TestResolveDisplayOptions:
    def test_no_flags(self) -> None:
        assert resolve_display_options(tokens=[]) == DisplayOptions()

    def test_combined_plus_display(self) -> None:
        opts = resolve_display_options(
            sort_loc=True, disp_size=True, tokens=["--sort-by-loc", "--size"]
        )
        assert opts.sort_key == METRIC_LOC
        assert opts.metrics == (METRIC_LOC, METRIC_SIZE)

    def test_display_only_order_follows_tokens(self) -> None:
        forward = resolve_display_options(
            disp_loc=True, disp_size=True, tokens=["--loc", "--size"]
        )
        assert forward.metrics == (METRIC_LOC, METRIC_SIZE)
        reverse = resolve_display_options(
            disp_loc=True, disp_size=True, tokens=["--size", "--loc"]
        )
        assert reverse.metrics == (METRIC_SIZE, METRIC_LOC)

    def test_first_sorting_flag_by_token_order(self) -> None:
        loc_first = resolve_display_options(
            sort_loc=True,
            sort_size=True,
            tokens=["--sort-by-loc", "--sort-by-size"],
        )
        assert loc_first.sort_key == METRIC_LOC
        assert loc_first.metrics == (METRIC_LOC,)
        size_first = resolve_display_options(
            sort_loc=True,
            sort_size=True,
            tokens=["--sort-by-size", "--sort-by-loc"],
        )
        assert size_first.sort_key == METRIC_SIZE
        assert size_first.metrics == (METRIC_SIZE,)

    def test_short_flag_bundle_ordering(self) -> None:
        sz = resolve_display_options(sort_loc=True, sort_size=True, tokens=["-sz"])
        assert sz.sort_key == METRIC_LOC
        zs = resolve_display_options(sort_loc=True, sort_size=True, tokens=["-zs"])
        assert zs.sort_key == METRIC_SIZE

    def test_missing_tokens_fall_back_to_registry_order(self) -> None:
        """Active flags absent from the tokens use their registry order."""
        opts = resolve_display_options(disp_size=True, disp_loc=True, tokens=[])
        assert opts.metrics == (METRIC_LOC, METRIC_SIZE)

    def test_double_dash_pushes_later_flag_last(self) -> None:
        opts = resolve_display_options(
            disp_loc=True,
            disp_size=True,
            tokens=["--size", "--", "--loc"],
        )
        assert opts.metrics == (METRIC_SIZE, METRIC_LOC)

    def test_defaults_to_sys_argv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["recursivist", "--size", "--loc"])
        opts = resolve_display_options(disp_loc=True, disp_size=True)
        assert opts.metrics == (METRIC_SIZE, METRIC_LOC)

    def test_full_mix_resolves_by_order(self) -> None:
        """A realistic mix: git sort wins, display-only trio annotates in order."""
        opts = resolve_display_options(
            sort_git=True,
            sort_loc=True,
            disp_mtime=True,
            disp_size=True,
            tokens=[
                "--sort-by-git-status",
                "--sort-by-loc",
                "--mtime",
                "--size",
            ],
        )
        assert opts.sort_key == METRIC_GIT
        assert opts.metrics == (METRIC_MTIME, METRIC_SIZE)
        assert opts.show_git_status is True

    def test_git_display_and_numeric_sort(self) -> None:
        opts = resolve_display_options(
            sort_size=True,
            disp_git=True,
            tokens=["--sort-by-size", "--git-status"],
        )
        assert opts.sort_key == METRIC_SIZE
        assert opts.metrics == (METRIC_SIZE,)
        assert opts.show_git_status is True
