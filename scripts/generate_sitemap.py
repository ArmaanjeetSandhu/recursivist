import json
import os
import re
from typing import Any

import yaml

MKDOCS_FILE = "mkdocs.yml"
SITEMAP_FILE = "docs/sitemap.md"
DOCS_DIR = "docs"


def parse_markdown_headers(filepath: str, path_prefix: str) -> list[dict[str, Any]]:
    """Parses markdown files to extract headers H1-H4 and builds a tree."""
    if not os.path.exists(filepath):
        return []

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    root_nodes = []
    stack: list[tuple[int, dict[str, Any]]] = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        match = re.match(r"^(#{1,4})\s+(.*)", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()

            title = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", title)

            slug = title.lower().replace(" ", "-").replace("`", "")

            if stack:
                parent_id = stack[-1][1]["id"]
                node_id = f"{parent_id}/{slug}"
            else:
                node_id = f"{path_prefix}/{slug}"

            node = {
                "id": node_id,
                "label": title,
                "children": [],
            }

            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                parent_id = stack[-1][1]["id"]
                node["id"] = f"{parent_id}/{slug}"
            else:
                node["id"] = f"{path_prefix}/{slug}"

            if not stack:
                root_nodes.append(node)
            else:
                stack[-1][1]["children"].append(node)

            stack.append((level, node))

    def clean_empty_children(nodes: list[dict[str, Any]]) -> None:
        for n in nodes:
            if not n["children"]:
                del n["children"]
            else:
                clean_empty_children(n["children"])

    clean_empty_children(root_nodes)
    return root_nodes


def process_nav(nav_item: object, parent_id: str = "root") -> dict[str, Any] | None:
    """Recursively processes the mkdocs nav structure."""
    if isinstance(nav_item, str):
        title = os.path.basename(nav_item).replace(".md", "").replace("-", " ").title()
        node_id = nav_item
        children = parse_markdown_headers(
            os.path.join(DOCS_DIR, nav_item), path_prefix=node_id
        )
        node: dict[str, Any] = {"id": node_id, "label": title}
        if children:
            node["children"] = children
        return node

    elif isinstance(nav_item, dict):
        for key, value in nav_item.items():
            slug = key.lower().replace(" ", "-")
            node_id = f"{parent_id}/{slug}"
            node = {"id": node_id, "label": key}
            if isinstance(value, str):
                children = parse_markdown_headers(
                    os.path.join(DOCS_DIR, value), path_prefix=node_id
                )
                if children:
                    node["children"] = children
            elif isinstance(value, list):
                node["children"] = [
                    process_nav(item, parent_id=node_id) for item in value
                ]
            return node

    return None


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

    tree = {
        "id": "root",
        "label": "Recursivist",
        "children": [process_nav(item, parent_id="root") for item in nav_list if item],
    }

    js_tree = "const TREE = " + json.dumps(tree, indent=2) + ";"

    with open(SITEMAP_FILE, encoding="utf-8") as f:
        content = f.read()

    updated_content = re.sub(
        r"const TREE = \{.*?\};", js_tree, content, flags=re.DOTALL
    )

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("Successfully updated sitemap.md!")


if __name__ == "__main__":
    main()
