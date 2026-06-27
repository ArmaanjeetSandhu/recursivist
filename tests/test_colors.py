"""Tests for recursivist.colors.generate_color_for_extension."""

import re

import pytest

from recursivist.colors import generate_color_for_extension


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
