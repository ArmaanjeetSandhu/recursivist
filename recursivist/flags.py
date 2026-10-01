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

from collections.abc import Collection, Sequence
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
        long: The long option string, including the leading dashes.
        short: The single-letter short option (without the dash), or ``None`` when the
            flag has no short form.
    """

    id: str
    mode: str
    metric: str
    long: str
    short: str | None = None


FLAG_SPECS: tuple[FlagSpec, ...] = (
    FlagSpec(
        "sort_similarity",
        MODE_SORT_ONLY,
        METRIC_SIMILARITY,
        "--sort-by-similarity",
        "S",
    ),
    FlagSpec("sort_loc", MODE_COMBINED, METRIC_LOC, "--sort-by-loc", "s"),
    FlagSpec("sort_size", MODE_COMBINED, METRIC_SIZE, "--sort-by-size", "z"),
    FlagSpec("sort_mtime", MODE_COMBINED, METRIC_MTIME, "--sort-by-mtime", "m"),
    FlagSpec("sort_git", MODE_COMBINED, METRIC_GIT, "--sort-by-git-status", None),
    FlagSpec("disp_loc", MODE_DISPLAY_ONLY, METRIC_LOC, "--loc", None),
    FlagSpec("disp_size", MODE_DISPLAY_ONLY, METRIC_SIZE, "--size", None),
    FlagSpec("disp_mtime", MODE_DISPLAY_ONLY, METRIC_MTIME, "--mtime", None),
    FlagSpec("disp_git", MODE_DISPLAY_ONLY, METRIC_GIT, "--git-status", "G"),
)
_SPEC_BY_ID: dict[str, FlagSpec] = {spec.id: spec for spec in FLAG_SPECS}
_REGISTRY_INDEX: dict[str, int] = {spec.id: i for i, spec in enumerate(FLAG_SPECS)}


@dataclass(frozen=True)
class DisplayOptions:
    """Resolved sorting and annotation directives for a single run.

    This is the value produced by [`resolve_flags`][recursivist.flags.resolve_flags] and
    threaded through the renderers and exporters. It keeps two concerns separate: *how
    files are ordered* (`sort_key`) and *what is annotated, and in what order*
    (`metrics` plus `show_git_status`).

    Attributes:
        sort_key: The single metric files are ordered by — one of `METRIC_LOC`,
            `METRIC_SIZE`, `METRIC_MTIME`, `METRIC_GIT`, `METRIC_SIMILARITY`, or
            ``None`` to keep the default extension/name ordering.
        metrics: The numeric metrics (subset of `NUMERIC_METRICS`) to annotate files
            with, in the exact order they should be displayed.
        show_git_status: Whether to append the Git-status badge to each file. The badge
            always trails the numeric-metric parenthetical.
    """

    sort_key: str | None = None
    metrics: tuple[str, ...] = ()
    show_git_status: bool = False

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

    @property
    def sorts_by_metric(self) -> bool:
        """Whether ordering is driven by a numeric metric (LOC, size, mtime)."""
        return self.sort_key in NUMERIC_METRICS

    def without_remote_unsupported(self) -> "DisplayOptions":
        """Return a copy with annotations that don't apply to a hosted repo.

        A GitHub checkout has no meaningful per-file Git status or modification time —
        every file effectively shares the tip commit's status and timestamp — so the
        Git-status badge and the modification-time metric are dropped, and a sort keyed
        on either falls back to the default ordering. The lines-of-code and size metrics
        are retained, since those are computed from the file contents themselves.

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


def _cli_order_key(
    spec: FlagSpec,
    tokens: Sequence[str],
    value_options: Collection[str] = (),
) -> tuple[int, int] | None:
    """Return the earliest ``(token_index, char_index)`` position of *spec*.

    Long options match a whole token (ignoring any ``=value`` suffix). Short options are
    searched for within short-option bundles such as ``-sz``, so the character position
    inside the bundle preserves the user's ordering. Returns ``None`` when the flag does
    not appear in *tokens*.

    Option values are never mistaken for flags. Every option string in *value_options*
    (e.g. ``"-x"`` or ``"--exclude-ext"``) consumes a value: inside a short bundle the
    rest of the bundle is that value (``-xmd`` is ``-x md``, not ``-x -m -d``), and when
    nothing follows the option in its own token the next token is the value, even if it
    starts with a dash.

    Args:
        spec: The flag to locate.
        tokens: The raw command-line tokens to search.
        value_options: Option strings, with their dashes, that take a value.

    Returns:
        The earliest position as a sortable tuple, or ``None`` if not found.
    """
    skip_next = False
    for index, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if token == "--":
            break
        if token.startswith("--"):
            name = token.split("=", 1)[0]
            if name == spec.long:
                return (index, 0)
            if name in value_options and "=" not in token:
                skip_next = True
        elif len(token) >= 2 and token[0] == "-":
            body = token[1:]
            for char_index, char in enumerate(body):
                if char == spec.short:
                    return (index, char_index)
                if f"-{char}" in value_options:
                    skip_next = char_index == len(body) - 1
                    break
    return None


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
    tokens: Sequence[str] | None = None,
    value_options: Collection[str] = (),
) -> DisplayOptions:
    """Resolve the raw per-flag booleans into
    [`DisplayOptions`][recursivist.flags.DisplayOptions].

    The set of active flags comes from the boolean arguments (which the CLI parser has
    already validated), while their relative order is recovered from *tokens* — the raw
    command-line arguments. This split keeps resolution robust: the parser is the source
    of truth for *which* flags are present, and the token scan only orders that known
    set. A flag that cannot be located in *tokens* falls back to its registry position
    so ordering stays deterministic.

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
        tokens: The raw command-line tokens used to order the active flags. The caller
            must supply the arguments of the invocation being resolved; ``sys.argv`` is
            deliberately never consulted, because it belongs to the host process and is
            unrelated to the arguments when the CLI is invoked from code. When omitted,
            every active flag falls back to its registry position.
        value_options: Option strings, with their dashes (e.g. ``"-x"``,
            ``"--exclude-ext"``), that take a value on the command being resolved, so
            their values are skipped rather than scanned for flags.

    Returns:
        The resolved [`DisplayOptions`][recursivist.flags.DisplayOptions].
    """
    if tokens is None:
        tokens = ()

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
    active_specs = [_SPEC_BY_ID[flag_id] for flag_id, on in active.items() if on]

    def sort_key(spec: FlagSpec) -> tuple[int, int]:
        position = _cli_order_key(spec, tokens, value_options)
        if position is None:
            return (len(tokens) + 1, _REGISTRY_INDEX[spec.id])
        return position

    ordered = sorted(active_specs, key=sort_key)
    events = [(spec.mode, spec.metric) for spec in ordered]
    return resolve_flags(events)
