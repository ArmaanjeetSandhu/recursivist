"""Deterministic color assignment for file extensions.

Generates a stable, visually distinct hex color per file extension using a
hash of the extension, with a collision-avoidance pass over already-assigned
colors. Pure standard library.
"""

import colorsys
import hashlib
import math
from typing import cast

_EXTENSION_COLORS: dict[str, str] = {}


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
        hex_color = "#{:02x}{:02x}{:02x}".format(*initial_color)
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
    hex_color = "#{:02x}{:02x}{:02x}".format(*best_color)
    _EXTENSION_COLORS[extension] = hex_color
    if extension != normalized_ext:
        _EXTENSION_COLORS[normalized_ext] = hex_color
    return hex_color
