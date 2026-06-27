"""Shared Hypothesis strategies for property-based tests."""

from typing import Any

from hypothesis import strategies as st

simple_filename = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-",
    ),
    min_size=1,
    max_size=20,
).flatmap(
    lambda s: st.sampled_from(
        [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
    ).map(lambda ext: s + ext)
)


file_item_tuple = st.tuples(
    simple_filename,
    st.text(min_size=1, max_size=100),
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=10 * 1024 * 1024),
    st.floats(min_value=0, max_value=1672531200),
)


file_list = st.lists(
    st.one_of(
        simple_filename,
        st.tuples(
            simple_filename,
            st.text(min_size=1, max_size=100),
        ),
        st.tuples(
            simple_filename,
            st.text(min_size=1, max_size=100),
            st.integers(min_value=0, max_value=1000),
        ),
        st.tuples(
            simple_filename,
            st.text(min_size=1, max_size=100),
            st.integers(min_value=0, max_value=1000),
            st.integers(min_value=0, max_value=10 * 1024 * 1024),
        ),
        file_item_tuple,
    ),
    min_size=0,
    max_size=20,
)


@st.composite
def simple_directory_structure(draw: st.DrawFn) -> dict[str, Any]:
    """Generate a simple directory structure."""
    structure: dict[str, Any] = {}
    structure["_files"] = draw(file_list)
    if draw(st.booleans()):
        structure["_loc"] = draw(st.integers(min_value=0, max_value=10000))
    if draw(st.booleans()):
        structure["_size"] = draw(st.integers(min_value=0, max_value=100 * 1024 * 1024))
    if draw(st.booleans()):
        structure["_mtime"] = draw(st.floats(min_value=0, max_value=1672531200))
    if draw(st.booleans()):
        subdir_name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=10,
            )
        )
        structure[subdir_name] = draw(simple_directory_structure())
    if draw(st.booleans()):
        structure["_max_depth_reached"] = True
    return structure
