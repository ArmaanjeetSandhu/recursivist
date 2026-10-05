# GitHub Repositories

`visualize`, `export`, and `compare` accept a GitHub repository URL anywhere they accept a local directory. The repository's source archive is downloaded into a temporary directory, scanned exactly like a local directory, and removed once the command finishes — no manual clone required.

```bash
recursivist visualize https://github.com/owner/repo
recursivist export https://github.com/owner/repo --format md
recursivist compare ./my-fork https://github.com/owner/repo
```

## Choosing a Branch, Tag, or Subtree

When no ref is pinned, the repository's default branch is used. Add a `/tree/<ref>` or `/blob/<ref>/<subpath>` selector to pin a branch, tag, or commit, and, optionally, to scan only part of the repository:

```bash
recursivist visualize https://github.com/owner/repo/tree/develop     # a branch
recursivist visualize https://github.com/owner/repo/tree/main/src    # a subtree of a branch
```

Any path after the ref scopes the scan to that subtree, so the tree is rooted at the subtree rather than the repository root. When that path names a file rather than a folder — as in the URL of a file's page on GitHub — the folder containing the file is scanned instead (the repository root, for a top-level file), and a message says so.

## Accepted URL Forms

| Form                       | Example                                              |
| -------------------------- | ---------------------------------------------------- |
| HTTPS URL                  | `https://github.com/owner/repo`                      |
| Without scheme             | `github.com/owner/repo`                              |
| With `.git` suffix         | `https://github.com/owner/repo.git`                  |
| SSH form                   | `git@github.com:owner/repo.git`                      |
| Pinned branch or tag       | `https://github.com/owner/repo/tree/<ref>`           |
| Pinned ref and subtree     | `https://github.com/owner/repo/tree/<ref>/<subpath>` |
| Blob URL (ref and subtree) | `https://github.com/owner/repo/blob/<ref>/<subpath>` |
| File URL (its folder)      | `https://github.com/owner/repo/blob/<ref>/<file>`    |

A few details are worth knowing:

- **Refs that contain a slash.** The segment immediately after `/tree/` or `/blob/` is read as the ref, so a ref whose own name contains a slash (such as `feature/login`) cannot be combined with a subpath in a single URL; pass the repository without a selector, or pin a ref whose name has no slash.
- **The SSH form** addresses the whole repository only and carries no ref or subpath.
- **Case.** The scheme and host are case-insensitive (`https://GitHub.com/owner/repo` works); the owner, repository, ref, and subpath are used exactly as written.
- **Scheme-less URLs that are also local paths.** Because the scheme-less form is also a valid relative path, an argument such as `github.com/golang/go` is treated as a local directory when that path exists (for example, a GOPATH-style checkout); add `https://` to force the GitHub repository.

## Authentication

A token in the `GITHUB_TOKEN` environment variable — or `GH_TOKEN` when `GITHUB_TOKEN` is unset — is sent with each request, which raises GitHub's rate limits and grants access to private repositories.

```bash
export GITHUB_TOKEN=ghp_your_token_here
recursivist visualize https://github.com/owner/private-repo
```

## Which Options Apply

A hosted repository already reflects its own ignore rules, and every file in a checkout shares a single Git status and modification time (the tip commit's). The options that depend on those are skipped for a GitHub input, with an informational message naming the ones that were skipped:

| Option                                 | Behavior for a GitHub input                                                                                                  |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `--ignore-file`                        | Skipped                                                                                                                      |
| `--git-status`, `--sort-by-git-status` | Skipped                                                                                                                      |
| `--mtime`, `--sort-by-mtime`           | Skipped                                                                                                                      |
| `--loc`, `--sort-by-loc`               | Applied, since lines of code come from the file contents                                                                     |
| `--size`, `--sort-by-size`             | Applied, since sizes come from the file contents                                                                             |
| `--full-path`                          | Applied; shows each file's GitHub blob URL (`https://github.com/owner/repo/blob/<ref>/<path>`) in place of a filesystem path |

The blob URLs make `--full-path` convenient for a Markdown or JSON export that links back to the source:

```bash
recursivist export https://github.com/owner/repo --format md --full-path
```

[Saved and project settings](configuration.md) follow the same logic. The `ignore-file` setting is not applied to a GitHub input, and no message is shown for it. The `exclude` setting of your user preferences is applied, as `--exclude` is. A GitHub input has no project configuration of its own.

## Symbolic Links

A symbolic link whose target lies inside the repository is [listed like any other link](visualization.md#symbolic-links). One whose target lies outside it — an absolute path such as `/etc/hosts`, or a relative path that climbs out of the repository — is left out of the tree, and a warning names the link. Its target is not part of the repository, so following it would read a file from your own machine.

## Comparing with a GitHub Repository

Either input to `compare` may be a GitHub repository URL, so a local directory can be compared against a GitHub repository, or two GitHub repositories (or two refs of one repository) against each other:

```bash
# Local directory against a GitHub repository
recursivist compare ./my-fork https://github.com/owner/repo

# Two GitHub repositories
recursivist compare https://github.com/owner/repo-a https://github.com/owner/repo-b

# Two refs of the same repository
recursivist compare https://github.com/owner/repo/tree/main https://github.com/owner/repo/tree/develop
```

The options that are skipped for a GitHub input are skipped per side:

- When **both** inputs are GitHub repositories, `--ignore-file`, `--git-status`, `--mtime`, and their sorting forms are skipped entirely.
- In a **mixed** comparison — one local directory and one GitHub repository — `--ignore-file`, `--git-status`, and `--mtime` still apply to the local side, so a local directory can be annotated with Git status while the GitHub side is not.
- The sorting flags `--sort-by-git-status` and `--sort-by-mtime` are skipped whenever either input is a GitHub repository, because both sides share one ordering.

An ignore file named by the `ignore-file` setting is likewise applied to local sides only, while the directories named by the `exclude` setting are left out of both sides, as those given with `--exclude` are.
