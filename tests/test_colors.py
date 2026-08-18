"""Tests for recursivist.colors.generate_color_for_extension."""

import colorsys
import re
import string

import pytest

from recursivist.colors import (
    WCAG_AA_NORMAL_TEXT,
    WCAG_AAA_NORMAL_TEXT,
    contrast_ratio,
    ensure_contrast,
    generate_color_for_extension,
    hex_to_rgb,
    relative_luminance,
)


class TestGenerateColorForExtension:
    def test_color_format(self) -> None:
        color = generate_color_for_extension(".py")
        assert re.match(r"^#[0-9A-Fa-f]{6}$", color)

    def test_consistency(self) -> None:
        """Test that the same extension always gets the same color."""
        color1 = generate_color_for_extension(".py")
        color2 = generate_color_for_extension(".py")
        color3 = generate_color_for_extension(".py")
        assert color1 == color2 == color3

    def test_different_extensions(self) -> None:
        """Test that different extensions get different colors."""
        extensions = [".py", ".js", ".txt", ".md", ".html", ".css", ".json", ".xml"]
        colors = [generate_color_for_extension(ext) for ext in extensions]
        assert len(set(colors)) == len(extensions)

    @pytest.mark.parametrize(
        "test_case,extension1,extension2",
        [
            ("case_sensitivity", ".py", ".PY"),
            ("with_without_dot", ".py", "py"),
        ],
    )
    def test_extension_variants(
        self, test_case: str, extension1: str, extension2: str
    ) -> None:
        """Test behavior with different variants of extensions."""
        color1 = generate_color_for_extension(extension1)
        color2 = generate_color_for_extension(extension2)
        assert isinstance(color1, str)
        assert isinstance(color2, str)
        assert color1.startswith("#")
        assert color2.startswith("#")
        if test_case == "case_sensitivity":
            assert color1 != color2
        else:
            assert color1 == color2

    def test_empty_extension(self) -> None:
        color = generate_color_for_extension("")
        assert color == "#FFFFFF"


class TestRelativeLuminance:
    @pytest.mark.parametrize(
        "color,expected",
        [
            ((0, 0, 0), 0.0),
            ((255, 255, 255), 1.0),
        ],
    )
    def test_known_endpoints(
        self, color: tuple[int, int, int], expected: float
    ) -> None:
        assert relative_luminance(color) == pytest.approx(expected, abs=1e-9)

    def test_monotonic_in_brightness(self) -> None:
        greys = [relative_luminance((v, v, v)) for v in range(0, 256, 15)]
        assert greys == sorted(greys)


class TestContrastRatio:
    def test_black_on_white_is_maximum(self) -> None:
        assert contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)

    def test_identical_colors_have_no_contrast(self) -> None:
        assert contrast_ratio((18, 52, 86), (18, 52, 86)) == pytest.approx(1.0)

    def test_symmetric(self) -> None:
        a, b = (200, 30, 90), (12, 240, 77)
        assert contrast_ratio(a, b) == pytest.approx(contrast_ratio(b, a))


class TestEnsureContrast:
    """The HTML export draws on white, so colors must be legible against it."""

    def test_compliant_color_is_unchanged(self) -> None:
        assert ensure_contrast("#2c3e50", "#ffffff") == "#2c3e50"

    @pytest.mark.parametrize(
        "hex_color",
        ["#FFFFFF", "#daff38", "#00e016", "#2bcdd8", "#ccc622", "#f7383f", "#e08e41"],
    )
    def test_low_contrast_colors_are_fixed(self, hex_color: str) -> None:
        adjusted = ensure_contrast(hex_color, "#ffffff")
        assert contrast_ratio(hex_to_rgb(adjusted), hex_to_rgb("#ffffff")) >= 4.5

    @pytest.mark.parametrize("ratio", [WCAG_AA_NORMAL_TEXT, WCAG_AAA_NORMAL_TEXT])
    def test_meets_requested_conformance_level(self, ratio: float) -> None:
        for hex_color in ["#FFFFFF", "#daff38", "#2bcdd8", "#f7383f", "#e08e41"]:
            adjusted = ensure_contrast(hex_color, "#ffffff", ratio)
            assert contrast_ratio(hex_to_rgb(adjusted), hex_to_rgb("#ffffff")) >= ratio

    def test_white_on_white_becomes_visible(self) -> None:
        """An empty extension maps to white, which would otherwise be invisible."""
        assert ensure_contrast("#FFFFFF", "#ffffff") != "#FFFFFF"

    def test_hue_is_preserved(self) -> None:
        """Adjusting brightness must not turn one extension's color into another's."""
        for hex_color in ["#daff38", "#2bcdd8", "#f7383f", "#7320d8"]:
            original = colorsys.rgb_to_hsv(*[c / 255 for c in hex_to_rgb(hex_color)])
            adjusted = colorsys.rgb_to_hsv(
                *[c / 255 for c in hex_to_rgb(ensure_contrast(hex_color, "#ffffff"))]
            )
            assert adjusted[0] == pytest.approx(original[0], abs=0.01)

    def test_lightens_against_a_dark_background(self) -> None:
        adjusted = ensure_contrast("#3600cc", "#000000")
        assert contrast_ratio(hex_to_rgb(adjusted), hex_to_rgb("#000000")) >= 4.5
        assert relative_luminance(hex_to_rgb(adjusted)) > relative_luminance(
            hex_to_rgb("#3600cc")
        )

    def test_darkens_against_a_light_background(self) -> None:
        adjusted = ensure_contrast("#daff38", "#ffffff")
        assert relative_luminance(hex_to_rgb(adjusted)) < relative_luminance(
            hex_to_rgb("#daff38")
        )

    def test_idempotent(self) -> None:
        once = ensure_contrast("#daff38", "#ffffff")
        assert ensure_contrast(once, "#ffffff") == once

    def test_respects_a_custom_ratio(self) -> None:
        adjusted = ensure_contrast("#e08e41", "#ffffff", 7.0)
        assert contrast_ratio(hex_to_rgb(adjusted), hex_to_rgb("#ffffff")) >= 7.0

    def test_every_generated_extension_color_can_be_fixed(self) -> None:
        extensions = [
            f".{a}{b}" for a in string.ascii_lowercase for b in string.ascii_lowercase
        ]
        for ext in extensions:
            adjusted = ensure_contrast(
                generate_color_for_extension(ext), "#ffffff", WCAG_AAA_NORMAL_TEXT
            )
            assert (
                contrast_ratio(hex_to_rgb(adjusted), hex_to_rgb("#ffffff"))
                >= WCAG_AAA_NORMAL_TEXT
            )
