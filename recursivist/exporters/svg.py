"""SVG tree exporter.

Renders the scanned structure with the terminal tree builder into a recording ``rich``
console and saves the captured output as an ``.svg`` file.
"""

import copy
import io
import re

from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.terminal_theme import SVG_EXPORT_THEME
from rich.text import Text
from rich.tree import Tree

from recursivist.colors import build_color_map
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics
from recursivist.scanner import collect_extensions, has_contents
from recursivist.tree import build_tree

from .base import BaseExporter, write_text

TERMINAL_BACKGROUND = "#0d1117"
TERMINAL_HEADER_BACKGROUND = "#161b22"
TERMINAL_EDGE_OPACITY = "0.06"
TERMINAL_BUTTONS = ("#ff5f57", "#febc2e", "#28c840")

RICH_HEADER_HEIGHT = 40
HEADER_HEIGHT = 52

RICH_LINE_OFFSET = 1.5
RICH_BOTTOM_PADDING = 8
BODY_PADDING = 8

SVG_THEME = copy.copy(SVG_EXPORT_THEME)
SVG_THEME.background_color = ColorTriplet(13, 17, 23)

_FRAME_PATTERN = re.compile(
    r'<rect fill="[^"]*" stroke="[^"]*" stroke-width="1" '
    r'x="(?P<x>[\d.]+)" y="(?P<y>[\d.]+)" '
    r'width="(?P<width>[\d.]+)" height="(?P<height>[\d.]+)" rx="\d+"/>'
)
_BUTTONS_PATTERN = re.compile(r'<g transform="translate\(26,22\)">.*?</g>', re.DOTALL)
_VIEWBOX_PATTERN = re.compile(r'viewBox="0 0 [\d.]+ (?P<height>[\d.]+)"')
_TITLE_PATTERN = re.compile(r'<text class="[^"]*-title"[^>]*? y="(?P<y>[\d.]+)"')
_BODY_PATTERN = re.compile(
    r'<g transform="translate\([\d.]+, (?P<y>[\d.]+)\)" '
    r'clip-path="url\(#[^)]*-clip-terminal\)"'
)


def _shift(svg: str, match: re.Match[str], group: str, offset: float) -> str:
    """Return *svg* with the number captured by *group* in *match* moved by *offset*."""
    start, end = match.span(group)
    return f"{svg[:start]}{float(match[group]) + offset:g}{svg[end:]}"


def _style_terminal_chrome(svg: str) -> str:
    """Draw the terminal window around an SVG exported by Rich.

    The window has rounded corners, a header bar with a divider and three buttons, and
    equal padding above the first line and below the last line of the terminal body.
    The header title text and its styling come from Rich unchanged. If Rich's markup
    is not recognised, the SVG is returned unchanged.

    Args:
        svg: SVG markup produced by ``Console.export_svg``.

    Returns:
        The SVG markup with the terminal window drawn.
    """
    frame = _FRAME_PATTERN.search(svg)
    buttons = _BUTTONS_PATTERN.search(svg)
    viewbox = _VIEWBOX_PATTERN.search(svg)
    body = _BODY_PATTERN.search(svg)
    if frame is None or buttons is None or viewbox is None or body is None:
        return svg

    x = float(frame["x"])
    y = float(frame["y"])
    width = float(frame["width"])
    rich_height = float(frame["height"])
    lines_height = rich_height - RICH_HEADER_HEIGHT - RICH_BOTTOM_PADDING
    height = HEADER_HEIGHT + BODY_PADDING + lines_height + BODY_PADDING
    header_extra = HEADER_HEIGHT - RICH_HEADER_HEIGHT
    body_shift = header_extra + BODY_PADDING - RICH_LINE_OFFSET
    radius = 12
    header_bottom = y + HEADER_HEIGHT - 1
    right = x + width

    frame_box = (
        f'x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="{radius}"'
    )
    window = (
        f'<rect fill="{TERMINAL_BACKGROUND}" {frame_box}/>'
        f'<path fill="{TERMINAL_HEADER_BACKGROUND}" d="M{x:g} {header_bottom:g}'
        f"V{y + radius:g}A{radius} {radius} 0 0 1 {x + radius:g} {y:g}"
        f"H{right - radius:g}A{radius} {radius} 0 0 1 {right:g} {y + radius:g}"
        f'V{header_bottom:g}Z"/>'
        f'<rect fill="#ffffff" fill-opacity="{TERMINAL_EDGE_OPACITY}" '
        f'x="{x:g}" y="{header_bottom:g}" width="{width:g}" height="1"/>'
        f'<rect fill="none" stroke="#ffffff" stroke-opacity="{TERMINAL_EDGE_OPACITY}" '
        f'stroke-width="1" {frame_box}/>'
    )
    button_y = y + (HEADER_HEIGHT - 1) / 2
    traffic_lights = "".join(
        f'<circle cx="{x + 26 + index * 18:g}" cy="{button_y:g}" r="6" fill="{color}"/>'
        for index, color in enumerate(TERMINAL_BUTTONS)
    )

    svg = _shift(svg, body, "y", body_shift)
    svg = (
        svg[: frame.start()]
        + window
        + svg[frame.end() : buttons.start()]
        + traffic_lights
        + svg[buttons.end() :]
    )
    title = _TITLE_PATTERN.search(svg)
    if title is not None:
        svg = _shift(svg, title, "y", header_extra / 2)
    return _shift(svg, viewbox, "height", height - rich_height)


class SvgExporter(BaseExporter):
    """Exporter that captures the rendered tree as an SVG image."""

    extension = "svg"

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as an SVG image.

        Builds the same colored tree used for terminal output via
        [`recursivist.tree.build_tree`][recursivist.tree.build_tree], renders it to a
        recording ``rich`` console, and saves that console's output as SVG.

        Args:
            output_path: Path the ``.svg`` file is written to.
        """
        color_map = build_color_map(collect_extensions(self.structure))

        root_icon = get_icon(
            self.root_name,
            is_dir=True,
            style=self.icon_style,
            is_empty=not has_contents(self.structure),
        )
        root_label = f"{root_icon} {self.root_name}" + format_dir_metrics(
            self.structure, self.metrics, self.date_format, self.size_format
        )

        tree = Tree(Text(root_label))

        build_tree(
            structure=self.structure,
            tree=tree,
            color_map=color_map,
            spec=self.spec,
            icon_style=self.icon_style,
        )

        dummy_file = io.StringIO()
        console = Console(record=True, width=120, file=dummy_file, force_terminal=True)
        console.print(tree)

        svg = console.export_svg(
            title=f"Directory Structure - {self.root_name}", theme=SVG_THEME
        )
        write_text(output_path, _style_terminal_chrome(svg))
