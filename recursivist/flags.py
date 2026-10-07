"""Command-line flag resolution for file sorting and annotation.

Recursivist exposes three families of file-annotation flags:

* **Sorting-only** — ``--sort-by-similarity`` groups similarly named files together but
  adds no annotation of its own.
* **Combined** — ``--sort-by-loc``, ``--sort-by-size``, ``--sort-by-mtime`` and
  ``--sort-by-git-status`` each sort files by a metric *and* annotate every file with
  that metric.
* **Display-only** — ``--loc``, ``--size``, ``--mtime`` and ``--git-status`` annotate
  files with a metric without influencing the ordering.

When several of these flags are combined, they are resolved strictly by their
left-to-right order on the command line rather than by any fixed internal precedence.
The rules, implemented by [`resolve_flags`][recursivist.flags.resolve_flags], are:

* Only the *first* sorting flag (sorting-only or combined) is honored; every later
  sorting flag is discarded completely — it contributes neither ordering nor annotation.
* Display-only flags always annotate. Their annotations appear in the exact order the
  flags were given.
* When the winning sort is a *combined* numeric metric (LOC, size or mtime), that
  metric's annotation is shown first, ahead of any display-only ones.
* When the winning sort is a *combined* Git-status flag, its badge trails at the very
  end, after every display-only annotation.

The resolution is expressed as a [`DisplayOptions`][recursivist.flags.DisplayOptions],
the single value the renderers and exporters consult to decide how to sort and what to
annotate.
"""

from collections.abc import Sequence
from dataclasses import dataclass

MODE_SORT_ONLY = "sort_only"
MODE_COMBINED = "combined"
MODE_DISPLAY_ONLY = "display_only"

METRIC_LOC = "loc"
METRIC_SIZE = "size"
METRIC_MTIME = "mtime"
METRIC_GIT = "git_status"
METRIC_SIMILARITY = "similarity"

NUMERIC_METRICS: tuple[str, ...] = (METRIC_LOC, METRIC_SIZE, METRIC_MTIME)


@dataclass(frozen=True)
class FlagSpec:
    """Static description of a single order-sensitive flag.

    Attributes:
        id: Stable identifier used as a dictionary key by the CLI layer.
        mode: One of `MODE_SORT_ONLY`, `MODE_COMBINED`, or `MODE_DISPLAY_ONLY`.
        metric: The metric the flag relates to (e.g. `METRIC_LOC`).
    """

    id: str
    mode: str
    metric: str


FLAG_SPECS: tuple[FlagSpec, ...] = (
    FlagSpec("sort_similarity", MODE_SORT_ONLY, METRIC_SIMILARITY),
    FlagSpec("sort_loc", MODE_COMBINED, METRIC_LOC),
    FlagSpec("sort_size", MODE_COMBINED, METRIC_SIZE),
    FlagSpec("sort_mtime", MODE_COMBINED, METRIC_MTIME),
    FlagSpec("sort_git", MODE_COMBINED, METRIC_GIT),
    FlagSpec("disp_loc", MODE_DISPLAY_ONLY, METRIC_LOC),
    FlagSpec("disp_size", MODE_DISPLAY_ONLY, METRIC_SIZE),
    FlagSpec("disp_mtime", MODE_DISPLAY_ONLY, METRIC_MTIME),
    FlagSpec("disp_git", MODE_DISPLAY_ONLY, METRIC_GIT),
)


@dataclass(frozen=True)
class DisplayOptions:
    """Resolved sorting and annotation directives for a single run.

    This is the value produced by [`resolve_flags`][recursivist.flags.resolve_flags] and
    threaded through the renderers and exporters. It keeps two concerns separate: *how
    files are ordered* (`sort_key`) and *what is annotated, and in what order*
    (`metrics` plus `show_git_status`), along with how a modification time is written
    (`date_format`).

    Attributes:
        sort_key: The single metric files are ordered by — one of `METRIC_LOC`,
            `METRIC_SIZE`, `METRIC_MTIME`, `METRIC_GIT`, `METRIC_SIMILARITY`, or
            ``None`` to keep the default extension/name ordering.
        metrics: The numeric metrics (subset of `NUMERIC_METRICS`) to annotate files
            with, in the exact order they should be displayed.
        show_git_status: Whether to append the Git-status badge to each file. The badge
            always trails the numeric-metric parenthetical.
        date_format: How the modification-time annotation is written: ``"relative"``
            for the recency-aware form (``Today 14:30``) or ``"iso"`` for ISO 8601 in
            UTC (``2026-10-07T12:30:41Z``). See
            [`format_timestamp`][recursivist.metrics.format_timestamp].
    """

    sort_key: str | None = None
    metrics: tuple[str, ...] = ()
    show_git_status: bool = False
    date_format: str = "relative"

    @property
    def show_loc(self) -> bool:
        """Whether the lines-of-code annotation is shown."""
        return METRIC_LOC in self.metrics

    @property
    def show_size(self) -> bool:
        """Whether the file-size annotation is shown."""
        return METRIC_SIZE in self.metrics

    @property
    def show_mtime(self) -> bool:
        """Whether the modification-time annotation is shown."""
        return METRIC_MTIME in self.metrics

    def without_remote_unsupported(self) -> "DisplayOptions":
        """Return a copy with annotations that don't apply to a hosted repo.

        A GitHub checkout has no meaningful per-file Git status or modification time,
        because every file effectively shares the tip commit's status and timestamp. The
        Git-status badge and the modification-time metric are dropped, and a sort keyed
        on either falls back to the default ordering. The lines-of-code and size metrics
        are retained, since those are computed from the file contents themselves. The
        date format is kept as it is.

        Returns:
            A [`DisplayOptions`][recursivist.flags.DisplayOptions] with Git status and
            modification time removed from both the sort key and the annotation set.
        """
        sort_key = self.sort_key
        if sort_key in (METRIC_GIT, METRIC_MTIME):
            sort_key = None
        metrics = tuple(metric for metric in self.metrics if metric != METRIC_MTIME)
        return DisplayOptions(
            sort_key=sort_key,
            metrics=metrics,
            show_git_status=False,
            date_format=self.date_format,
        )


def resolve_flags(events: Sequence[tuple[str, str]]) -> DisplayOptions:
    """Resolve an ordered sequence of flag events into
    [`DisplayOptions`][recursivist.flags.DisplayOptions].

    Each event is a ``(mode, metric)`` pair drawn from the registry, in the
    left-to-right order the flags appeared on the command line. The resolution rules are
    described in the module docstring.

    Args:
        events: The flag events, ordered by command-line position.

    Returns:
        The resolved [`DisplayOptions`][recursivist.flags.DisplayOptions].
    """
    sort_key: str | None = None
    sort_locked = False
    combined_winner: str | None = None
    display_only_metrics: list[str] = []
    display_only_git = False

    for mode, metric in events:
        if mode in (MODE_SORT_ONLY, MODE_COMBINED):
            if not sort_locked:
                sort_locked = True
                sort_key = metric
                if mode == MODE_COMBINED:
                    combined_winner = metric
        elif metric == METRIC_GIT:
            display_only_git = True
        elif metric not in display_only_metrics:
            display_only_metrics.append(metric)

    metrics: list[str] = []
    if combined_winner in NUMERIC_METRICS:
        metrics.append(combined_winner)
    for metric in display_only_metrics:
        if metric not in metrics:
            metrics.append(metric)

    show_git = display_only_git or combined_winner == METRIC_GIT
    return DisplayOptions(
        sort_key=sort_key,
        metrics=tuple(metrics),
        show_git_status=show_git,
    )


def resolve_display_options(
    *,
    sort_loc: bool = False,
    sort_size: bool = False,
    sort_mtime: bool = False,
    sort_similarity: bool = False,
    sort_git: bool = False,
    disp_loc: bool = False,
    disp_size: bool = False,
    disp_mtime: bool = False,
    disp_git: bool = False,
    order: Sequence[str] = (),
    date_format: str = "relative",
) -> DisplayOptions:
    """Resolve the raw per-flag booleans into
    [`DisplayOptions`][recursivist.flags.DisplayOptions].

    The boolean arguments say *which* flags are active and *order* says in what order
    they were given; the CLI parser supplies both. *order* only arranges the active set
    — a flag listed in it but not active is ignored, and an active flag missing from it
    is placed after the listed ones, in registry order, which keeps resolution
    deterministic.

    Args:
        sort_loc: Whether ``--sort-by-loc`` was given.
        sort_size: Whether ``--sort-by-size`` was given.
        sort_mtime: Whether ``--sort-by-mtime`` was given.
        sort_similarity: Whether ``--sort-by-similarity`` was given.
        sort_git: Whether ``--sort-by-git-status`` was given.
        disp_loc: Whether ``--loc`` was given.
        disp_size: Whether ``--size`` was given.
        disp_mtime: Whether ``--mtime`` was given.
        disp_git: Whether ``--git-status`` was given.
        order: The ids of the flags (see `FLAG_SPECS`) in the order the parser
            encountered them on the command line. A repeated id counts at its first
            position. When omitted, every active flag falls back to its registry
            position.
        date_format: How modification times are written, either ``"relative"`` or
            ``"iso"``. Unlike the flags above, its position on the command line does
            not matter.

    Returns:
        The resolved [`DisplayOptions`][recursivist.flags.DisplayOptions].

    Raises:
        ValueError: If *order* contains an id that is not in the registry.
    """
    active = {
        "sort_similarity": sort_similarity,
        "sort_loc": sort_loc,
        "sort_size": sort_size,
        "sort_mtime": sort_mtime,
        "sort_git": sort_git,
        "disp_loc": disp_loc,
        "disp_size": disp_size,
        "disp_mtime": disp_mtime,
        "disp_git": disp_git,
    }
    position: dict[str, int] = {}
    for index, flag_id in enumerate(order):
        if flag_id not in active:
            raise ValueError(f"Unknown flag id in order: {flag_id!r}")
        position.setdefault(flag_id, index)

    active_specs = [spec for spec in FLAG_SPECS if active[spec.id]]
    ordered = sorted(active_specs, key=lambda spec: position.get(spec.id, len(order)))
    events = [(spec.mode, spec.metric) for spec in ordered]
    resolved = resolve_flags(events)
    return DisplayOptions(
        sort_key=resolved.sort_key,
        metrics=resolved.metrics,
        show_git_status=resolved.show_git_status,
        date_format=date_format,
    )
