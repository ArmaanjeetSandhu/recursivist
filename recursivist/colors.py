"""Deterministic color assignment for file extensions.

Generates a stable, visually distinct hex color per file extension using a
hash of the extension, with a collision-avoidance pass over already-assigned
colors. Also provides WCAG 2.1 contrast helpers used by renderers that draw
onto a known background (such as the HTML exporter) to guarantee legible
text. Pure standard library.
"""

import colorsys
import hashlib
import math
from functools import lru_cache
from typing import cast

_EXTENSION_COLORS: dict[str, str] = {}

_HEX_FORMAT = "#{:02x}{:02x}{:02x}"
"""Format string for a CSS hex color built from an ``(r, g, b)`` tuple."""

WCAG_AA_NORMAL_TEXT = 4.5
"""WCAG 2.1 level AA minimum contrast ratio for normal-sized body text."""

WCAG_AA_LARGE_TEXT = 3.0
"""WCAG 2.1 level AA minimum contrast ratio for large text (>=18pt, or >=14pt bold)."""

WCAG_AAA_NORMAL_TEXT = 7.0
"""WCAG 2.1 level AAA minimum contrast ratio for normal-sized body text."""

WCAG_AAA_LARGE_TEXT = 4.5
"""WCAG 2.1 level AAA minimum contrast ratio for large text (>=18pt, or >=14pt bold)."""


def color_distance(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Calculate the perceptual distance between two RGB colors.

    Uses a weighted Euclidean distance formula that approximates human color
    perception by emphasising the green channel over red and blue.

    Args:
        color1: First color as an ``(r, g, b)`` tuple with component values
            in the range ``0``–``255``.
        color2: Second color as an ``(r, g, b)`` tuple with component values
            in the range ``0``–``255``.

    Returns:
        A non-negative float representing the perceptual distance; ``0.0``
        means the colors are identical and larger values indicate greater
        visual difference.
    """
    r1, g1, b1 = [x / 255 for x in color1]
    r2, g2, b2 = [x / 255 for x in color2]
    r_weight, g_weight, b_weight = 0.3, 0.59, 0.11
    dist = math.sqrt(
        r_weight * (r1 - r2) ** 2
        + g_weight * (g1 - g2) ** 2
        + b_weight * (b1 - b2) ** 2
    )
    return dist


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a CSS hex color string to an ``(r, g, b)`` tuple.

    Args:
        hex_color: Six-digit hex color string, optionally prefixed with
            ``'#'`` (e.g., ``"#FF5733"`` or ``"FF5733"``).

    Returns:
        A three-tuple of integers ``(red, green, blue)`` in the range
        ``0``–``255``.
    """
    hex_color = hex_color.lstrip("#")
    return cast(
        tuple[int, int, int], tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    )


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    """Convert an ``(r, g, b)`` tuple to a CSS hex color string.

    Args:
        color: Three-tuple of integers ``(red, green, blue)`` in the range
            ``0``–``255``.

    Returns:
        A lowercase six-digit hex color string prefixed with ``'#'``.
    """
    return _HEX_FORMAT.format(*color)


def relative_luminance(color: tuple[int, int, int]) -> float:
    """Calculate the WCAG relative luminance of an sRGB color.

    Implements the definition given in WCAG 2.1: each channel is normalised
    to ``0``–``1``, linearised to remove the sRGB transfer function, and then
    combined with the standard luminance coefficients.

    Args:
        color: Color as an ``(r, g, b)`` tuple with component values in the
            range ``0``–``255``.

    Returns:
        The relative luminance, from ``0.0`` (black) to ``1.0`` (white).
    """
    linear = []
    for component in color:
        channel = component / 255
        if channel <= 0.03928:
            linear.append(channel / 12.92)
        else:
            linear.append(((channel + 0.055) / 1.055) ** 2.4)
    red, green, blue = linear
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Calculate the WCAG contrast ratio between two colors.

    Args:
        color1: First color as an ``(r, g, b)`` tuple with component values
            in the range ``0``–``255``.
        color2: Second color as an ``(r, g, b)`` tuple with component values
            in the range ``0``–``255``.

    Returns:
        The contrast ratio, from ``1.0`` (identical luminance) to ``21.0``
        (black against white). WCAG 2.1 requires at least ``4.5`` for normal
        body text at level AA and ``3.0`` for large text.
    """
    luminance1 = relative_luminance(color1)
    luminance2 = relative_luminance(color2)
    lighter = max(luminance1, luminance2)
    darker = min(luminance1, luminance2)
    return (lighter + 0.05) / (darker + 0.05)


def _hsv_to_rgb255(hue: float, saturation: float, value: float) -> tuple[int, int, int]:
    """Convert HSV components to a rounded ``(r, g, b)`` tuple."""
    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
    return (round(red * 255), round(green * 255), round(blue * 255))


@lru_cache(maxsize=512)
def ensure_contrast(
    hex_color: str,
    background: str = "#ffffff",
    min_ratio: float = WCAG_AA_NORMAL_TEXT,
) -> str:
    """Adjust a color until it meets a WCAG contrast ratio against *background*.

    The hue is preserved so extensions stay recognisable and mutually
    distinguishable; only brightness (and, if brightness alone is not enough,
    saturation) is changed. Colors that already meet *min_ratio* are returned
    unchanged, so this is a no-op for compliant input.

    Colors are darkened against light backgrounds and lightened against dark
    ones, whichever direction can reach the required ratio.

    Args:
        hex_color: Foreground color as a hex string, with or without a
            leading ``'#'``.
        background: Background color the text is drawn on, as a hex string.
        min_ratio: Minimum acceptable contrast ratio. Defaults to ``4.5``,
            the WCAG 2.1 level AA threshold for normal-sized text.

    Returns:
        A CSS hex color string that meets *min_ratio* against *background*,
        or (if no adjustment of this hue can reach the ratio) the closest
        achievable color.
    """
    foreground = hex_to_rgb(hex_color)
    background_rgb = hex_to_rgb(background)
    if contrast_ratio(foreground, background_rgb) >= min_ratio:
        return hex_color
    hue, saturation, value = colorsys.rgb_to_hsv(*[c / 255 for c in foreground])
    darken = contrast_ratio((0, 0, 0), background_rgb) >= contrast_ratio(
        (255, 255, 255), background_rgb
    )
    steps = 128
    best_color = foreground
    best_ratio = contrast_ratio(foreground, background_rgb)
    candidates = []
    for step in range(1, steps + 1):
        fraction = step / steps
        if darken:
            candidates.append((hue, saturation, value * (1.0 - fraction)))
        else:
            candidates.append((hue, saturation, value + (1.0 - value) * fraction))
    if not darken:
        for step in range(1, steps + 1):
            fraction = step / steps
            candidates.append((hue, saturation * (1.0 - fraction), 1.0))
    for candidate_hsv in candidates:
        candidate = _hsv_to_rgb255(*candidate_hsv)
        ratio = contrast_ratio(candidate, background_rgb)
        if ratio >= min_ratio:
            return rgb_to_hex(candidate)
        if ratio > best_ratio:
            best_ratio = ratio
            best_color = candidate
    return rgb_to_hex(best_color)


def generate_color_for_extension(extension: str) -> str:
    """Generate a stable, visually distinct color for a file extension.

    The color is derived deterministically from a hash of the extension, so a
    given extension always maps to the same color within a session. Candidate
    colors are nudged through hue/saturation/value variations until they are
    far enough from every previously assigned color, keeping distinct
    extensions visually separable. The leading dot is optional and ignored, so
    ``"py"`` and ``".py"`` share a color. An empty extension maps to white.

    Args:
        extension: File extension, with or without a leading dot.

    Returns:
        A CSS hex color string (e.g., ``"#FF5733"``).
    """
    if not extension:
        return "#FFFFFF"
    normalized_ext = extension
    if not extension.startswith("."):
        normalized_ext = "." + extension
    if extension in _EXTENSION_COLORS:
        return _EXTENSION_COLORS[extension]
    if extension != normalized_ext and normalized_ext in _EXTENSION_COLORS:
        color = _EXTENSION_COLORS[normalized_ext]
        _EXTENSION_COLORS[extension] = color
        return color
    hash_bytes = hashlib.md5(normalized_ext.encode(), usedforsecurity=False).digest()
    hue_int = int.from_bytes(hash_bytes[0:4], byteorder="big")
    hue = (hue_int % 360) / 360.0
    sat_int = hash_bytes[4]
    saturation = 0.65 + (sat_int % 26) / 100.0
    val_int = hash_bytes[5]
    value = 0.85 + (val_int % 16) / 100.0
    min_acceptable_distance = 0.15
    max_attempts = 15
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    initial_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
    if not _EXTENSION_COLORS:
        hex_color = rgb_to_hex(initial_color)
        _EXTENSION_COLORS[extension] = hex_color
        if extension != normalized_ext:
            _EXTENSION_COLORS[normalized_ext] = hex_color
        return hex_color
    best_color = initial_color
    best_min_distance = 0.0
    for attempt in range(max_attempts):
        test_hue = (hue + (attempt * 0.1)) % 1.0
        test_sat = min(1.0, saturation + (attempt * 0.02))
        test_val = max(0.8, value - (attempt * 0.01))
        rgb = colorsys.hsv_to_rgb(test_hue, test_sat, test_val)
        test_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        min_distance = float("inf")
        for existing_color in _EXTENSION_COLORS.values():
            existing_rgb = hex_to_rgb(existing_color)
            distance = color_distance(test_color, existing_rgb)
            min_distance = min(min_distance, distance)
        if min_distance > best_min_distance:
            best_min_distance = min_distance
            best_color = test_color
        if min_distance >= min_acceptable_distance:
            break
    hex_color = rgb_to_hex(best_color)
    _EXTENSION_COLORS[extension] = hex_color
    if extension != normalized_ext:
        _EXTENSION_COLORS[normalized_ext] = hex_color
    return hex_color
