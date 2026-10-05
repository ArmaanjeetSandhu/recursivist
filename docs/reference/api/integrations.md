# Git, GitHub, and Configuration

The modules that reach outside the directory being scanned: the local Git repository, GitHub, and the user and project configuration files.

## Git Status

::: recursivist.git_status

## GitHub

A GitHub repository URL passed to `visualize`, `export`, or `compare` is resolved here. `parse_github_url` turns a URL into a `GitHubTarget`, and `checkout_repository` downloads the repository's source archive into a temporary directory and yields a `RepoCheckout` whose `local_root` is scanned like any other directory. `apply_github_urls` rewrites file paths to GitHub blob URLs for `--full-path` output.

::: recursivist.github

## Configuration

::: recursivist.config
