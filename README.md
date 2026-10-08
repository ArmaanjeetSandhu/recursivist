<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ArmaanjeetSandhu/recursivist/main/docs/assets/images/logo-white.svg">
  <img src="https://raw.githubusercontent.com/ArmaanjeetSandhu/recursivist/main/docs/assets/images/logo-black.svg" alt="Recursivist logo" width="88">
</picture>

# Recursivist

**See the shape of any codebase in one command**

[![PyPI](https://img.shields.io/pypi/v/recursivist?color=blue&style=for-the-badge)](https://pypi.org/project/recursivist/)
[![Python](https://img.shields.io/pypi/pyversions/recursivist?style=for-the-badge)](https://pypi.org/project/recursivist/)
[![Tests](https://img.shields.io/github/actions/workflow/status/ArmaanjeetSandhu/recursivist/test.yml?branch=main&label=tests&style=for-the-badge)](https://github.com/ArmaanjeetSandhu/recursivist/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/sonar/coverage/ArmaanjeetSandhu_recursivist?server=https%3A%2F%2Fsonarcloud.io&style=for-the-badge)](https://sonarcloud.io/summary/new_code?id=ArmaanjeetSandhu_recursivist)
[![Quality Gate Status](https://img.shields.io/sonar/quality_gate/ArmaanjeetSandhu_recursivist?server=https%3A%2F%2Fsonarcloud.io&style=for-the-badge)](https://sonarcloud.io/summary/new_code?id=ArmaanjeetSandhu_recursivist)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](https://github.com/ArmaanjeetSandhu/recursivist/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-online-8A2BE2?style=for-the-badge)](https://armaanjeetsandhu.github.io/recursivist/)

</div>

Recursivist draws any directory as a color-coded tree and annotates it with lines of code, file sizes, modification times, and Git status. It can filter that tree, compare it with another, and export it in six formats, for a local folder or for a GitHub repository you haven't cloned.

<p align="center">
  <img src="https://raw.githubusercontent.com/ArmaanjeetSandhu/recursivist/main/docs/assets/images/terminal-demo.svg" alt="Terminal output of recursivist visualize --sort-by-loc --size --git-status --exclude .git: the tree of my-project, where every file and folder shows its lines of code and size, and two files carry Git status markers" width="720">
</p>

Each file type gets its own color. Folder figures are totals for the files beneath them, and `[M]` and `[U]` mark modified and untracked files.

## Installation

```bash
pip install recursivist
```

Prefer an isolated install? `pipx install recursivist` and `uv tool install recursivist` both work. Each installs the `recursivist` command and its shorter alias, `rcv`.

## Features

- **[File statistics][stats]**: lines of code, size, and modification time for every file, rolled up per folder. Sort by any of them, or just display them.
- **[Git status][git]**: modified, added, deleted, and untracked files are marked in the tree and can be sorted first.
- **[Filtering][filtering]**: exclude directories and extensions, match file names by glob or regex, and apply `.gitignore`-style files at every level of the tree.
- **[GitHub repositories][github]**: pass a URL wherever a path is accepted, pinned to a branch, tag, or subfolder if you like. Private repositories work with `GITHUB_TOKEN` set.
- **[Comparison][compare]**: two trees side by side with their differences highlighted, in the terminal or as a self-contained HTML page. Either side can be local or on GitHub.
- **[Export][export]**: Markdown, JSON, HTML, SVG, plain text, and reStructuredText, with a [pre-commit hook][hook] that regenerates them on every commit.
- **[Configuration][config]**: save your defaults once, or commit a project's to `.recursivist.toml` or `pyproject.toml`.
- **And more**: [Nerd Font icons][icons], [shell completion][completion] for Bash, Zsh, Fish, and PowerShell, and a typed [Python API][api].

## Quick Start

```bash
# The current directory, or any path, as a tree
recursivist visualize
recursivist visualize path/to/project --depth 2

# Most lines of code first, with size and modification time alongside
recursivist visualize --sort-by-loc --size --mtime

# Changed files first, leaving out whatever .gitignore ignores
recursivist visualize --sort-by-git-status --ignore-file .gitignore

# Python files only, without the tests
recursivist visualize --include-pattern "*.py" --exclude-pattern "test_*"

# A GitHub repository, or one folder of one branch
recursivist visualize https://github.com/owner/repo
recursivist visualize https://github.com/owner/repo/tree/develop/src

# A fork against its upstream, saved as an HTML report
recursivist compare ./my-fork https://github.com/owner/repo --save

# Markdown for the docs, JSON for scripts, SVG for a README
recursivist export --format "md json svg" --output-dir docs

# Defaults for every run
recursivist config set exclude node_modules .git
recursivist config set ignore-file .gitignore
```

## Documentation

The [documentation][docs] covers every command and option. Begin with the [quick start][quickstart], borrow from the [recipes][recipes] for CI pipelines, self-updating structure docs, and `jq` analysis, or look things up in the [CLI reference][cli].

[docs]: https://armaanjeetsandhu.github.io/recursivist/
[quickstart]: https://armaanjeetsandhu.github.io/recursivist/getting-started/quick-start/
[recipes]: https://armaanjeetsandhu.github.io/recursivist/recipes/
[cli]: https://armaanjeetsandhu.github.io/recursivist/reference/cli-reference/
[stats]: https://armaanjeetsandhu.github.io/recursivist/user-guide/sorting-and-statistics/
[git]: https://armaanjeetsandhu.github.io/recursivist/user-guide/sorting-and-statistics/#git-status
[filtering]: https://armaanjeetsandhu.github.io/recursivist/user-guide/pattern-filtering/
[github]: https://armaanjeetsandhu.github.io/recursivist/user-guide/github-repositories/
[compare]: https://armaanjeetsandhu.github.io/recursivist/user-guide/compare/
[export]: https://armaanjeetsandhu.github.io/recursivist/reference/export-formats/
[hook]: https://armaanjeetsandhu.github.io/recursivist/recipes/documentation/#pre-commit-framework
[config]: https://armaanjeetsandhu.github.io/recursivist/user-guide/configuration/
[icons]: https://armaanjeetsandhu.github.io/recursivist/user-guide/visualization/#icon-styles
[completion]: https://armaanjeetsandhu.github.io/recursivist/user-guide/shell-completion/
[api]: https://armaanjeetsandhu.github.io/recursivist/reference/api-reference/
