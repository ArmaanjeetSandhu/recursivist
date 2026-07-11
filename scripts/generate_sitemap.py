"""Generate ``docs/sitemap.md`` from the MkDocs navigation.

The sitemap mirrors the documentation website's structure: it walks the ``nav``
defined in ``mkdocs.yml`` and, for every page, extracts the ``H1``-``H4``
headers to recover each page's sections and subsections. The result is written
as a Markdown in which every page, section, and subsection is hyperlinked to its
exact location on the documentation website.

Anchors are computed with the very same slugifier MkDocs uses (the ``toc``
extension of Python-Markdown), including its duplicate-heading disambiguation,
so the generated links resolve correctly.
"""

import os
import re
import unicodedata
from typing import Any

import yaml

MKDOCS_FILE = "mkdocs.yml"
SITEMAP_FILE = "docs/sitemap.md"
DOCS_DIR = "docs"

SITEMAP_REL = os.path.relpath(SITEMAP_FILE, DOCS_DIR).replace(os.sep, "/")

_MD_LINK_RE = re.compile(r"\[(.*?)\]\(.*?\)")
_HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)")
_IDCOUNT_RE = re.compile(r"^(.*)_(\d+)$")


def _slugify(value: str) -> str:
    """Slugify a header exactly as MkDocs' ``toc`` extension does by default.

    Mirrors ``markdown.extensions.toc.slugify`` (separator ``-``) so the
    generated anchors match the ids MkDocs renders. Reproduced here rather than
    imported to keep the script's only third-party dependency ``PyYAML``.
    """
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def _anchor(title: str, used_ids: set[str]) -> str:
    """Return the unique MkDocs anchor slug for a header on a single page.

    Mirrors ``markdown.extensions.toc.unique`` so repeated headers on one page
    are disambiguated the same way MkDocs does (``slug``, ``slug_1``, ...).
    """
    slug = _slugify(title)
    while slug in used_ids or not slug:
        m = _IDCOUNT_RE.match(slug)
        slug = f"{m.group(1)}_{int(m.group(2)) + 1}" if m else f"{slug}_1"
    used_ids.add(slug)
    return slug


def parse_markdown_headers(filepath: str, page_url: str) -> list[dict[str, Any]]:
    """Parse a page and return its ``H1``-``H4`` headers as a nested tree.

    Each node carries the link ``url`` (the page URL plus the header's anchor)
    so the sitemap can hyperlink straight to that section.
    """
    if not os.path.exists(filepath):
        return []

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    root_nodes: list[dict[str, Any]] = []
    stack: list[tuple[int, dict[str, Any]]] = []
    used_ids: set[str] = set()
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        match = _HEADER_RE.match(line)
        if not match:
            continue

        level = len(match.group(1))
        title = _MD_LINK_RE.sub(r"\1", match.group(2).strip())
        anchor = _anchor(title, used_ids)

        node: dict[str, Any] = {
            "label": title,
            "url": f"{page_url}#{anchor}",
            "children": [],
        }

        while stack and stack[-1][0] >= level:
            stack.pop()

        if stack:
            stack[-1][1]["children"].append(node)
        else:
            root_nodes.append(node)

        stack.append((level, node))

    return root_nodes


def _page_sections(filepath: str, page_url: str) -> list[dict[str, Any]]:
    """Return the sections to list under a page.

    A page conventionally has a single ``H1`` that repeats its title; when that
    is the case the redundant ``H1`` is unwrapped so its subsections attach
    directly to the page entry.
    """
    headers = parse_markdown_headers(filepath, page_url)
    if len(headers) == 1:
        children: list[dict[str, Any]] = headers[0]["children"]
        return children
    return headers


def process_nav(nav_item: object) -> dict[str, Any] | None:
    """Turn one ``mkdocs.yml`` ``nav`` entry into a sitemap node.

    A node has a ``label``, an optional ``url`` (``None`` for grouping entries
    that are not pages themselves), and ``children`` (subsections for pages,
    or nested pages for groups).
    """
    if isinstance(nav_item, str):
        label = os.path.basename(nav_item).replace(".md", "").replace("-", " ").title()
        return _page_node(label, nav_item)

    if isinstance(nav_item, dict):
        for key, value in nav_item.items():
            if isinstance(value, str):
                return _page_node(key, value)
            if isinstance(value, list):
                children = [process_nav(item) for item in value]
                return {
                    "label": key,
                    "url": None,
                    "children": [c for c in children if c],
                }
    return None


def _page_node(label: str, rel_path: str) -> dict[str, Any] | None:
    """Build a page node, hyperlinked to the page and carrying its sections.

    The sitemap page itself is omitted: it should not list itself, and skipping
    it keeps regeneration idempotent.
    """
    rel_path = rel_path.replace(os.sep, "/")
    if rel_path == SITEMAP_REL:
        return None
    sections = _page_sections(os.path.join(DOCS_DIR, rel_path), rel_path)
    return {"label": label, "url": rel_path, "children": sections}


def _render_bullets(nodes: list[dict[str, Any]], indent: int, out: list[str]) -> None:
    """Render nodes as a nested Markdown bullet list (4 spaces per level)."""
    pad = "    " * indent
    for node in nodes:
        label, url = node["label"], node.get("url")
        out.append(f"{pad}- [{label}]({url})" if url else f"{pad}- {label}")
        if node.get("children"):
            _render_bullets(node["children"], indent + 1, out)


def render_sitemap(tree: list[dict[str, Any]]) -> str:
    """Render the full sitemap Markdown document."""
    out: list[str] = ["# Sitemap", ""]

    for node in tree:
        label, url = node["label"], node.get("url")
        heading = f"[{label}]({url})" if url else label
        out.append(f"## {heading}")
        out.append("")
        if node.get("children"):
            _render_bullets(node["children"], 0, out)
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def _ignore_python_tags(
    _loader: yaml.SafeLoader, _suffix: str, _node: yaml.Node
) -> None:
    return None


def main() -> None:
    yaml.add_multi_constructor(
        "tag:yaml.org,2002:python/name:",
        _ignore_python_tags,
        Loader=yaml.SafeLoader,
    )

    with open(MKDOCS_FILE, encoding="utf-8") as f:
        mkdocs_config = yaml.safe_load(f)

    nav_list = mkdocs_config.get("nav", [])
    tree = [node for item in nav_list if item and (node := process_nav(item))]

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(render_sitemap(tree))

    print("Successfully updated sitemap.md!")


if __name__ == "__main__":
    main()
