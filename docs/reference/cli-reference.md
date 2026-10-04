# CLI Reference

A complete reference for every Recursivist command and option.

## Commands

| Command     | Description                                   |
| ----------- | --------------------------------------------- |
| `visualize` | Display a directory structure in the terminal |
| `export`    | Export a directory structure to files         |
| `compare`   | Compare two directory structures side by side |
| `config`    | Manage persistent user preferences            |
| `version`   | Show the installed version                    |

## Shared Options

The following options are common to `visualize`, `export`, and `compare`. Repeatable options take one value per flag; repeat the flag to supply several values (e.g. `--exclude node_modules --exclude .git`). Because each value is used verbatim, values may contain spaces — quote them, e.g. `--exclude "Application Support"`.

| Option                 | Short | Description                                                                    |
| ---------------------- | ----- | ------------------------------------------------------------------------------ |
| `--exclude`            | `-e`  | Directory names to exclude                                                     |
| `--exclude-ext`        | `-x`  | File extensions to exclude (leading dot optional)                              |
| `--exclude-pattern`    | `-p`  | File-name patterns to exclude (glob by default, regex with `-r`)               |
| `--include-pattern`    | `-i`  | File-name patterns to include                                                  |
| `--regex`              | `-r`  | Treat patterns as regular expressions instead of globs                         |
| `--ignore-file`        | `-g`  | Gitignore-style ignore file to honor (e.g. `.gitignore`)                       |
| `--depth`              | `-d`  | Maximum depth to traverse (`0` for unlimited)                                  |
| `--full-path`          | `-l`  | Show full paths instead of bare filenames (GitHub blob URLs for GitHub inputs) |
| `--sort-by-similarity` | `-S`  | Group files with similar names together                                        |
| `--sort-by-loc`        | `-s`  | Sort files by lines of code and display LOC counts                             |
| `--sort-by-size`       | `-z`  | Sort files by size and display file sizes                                      |
| `--sort-by-mtime`      | `-m`  | Sort files by modification time and display timestamps                         |
| `--sort-by-git-status` |       | Sort files by Git status and display status markers                            |
| `--loc`                |       | Display lines of code without affecting sort order                             |
| `--size`               |       | Display file sizes without affecting sort order                                |
| `--mtime`              |       | Display modification times without affecting sort order                        |
| `--git-status`         | `-G`  | Display Git status markers without affecting sort order                        |
| `--icon-style`         |       | Icon style: `emoji` or `nerd`                                                  |
| `--verbose`            | `-v`  | Enable verbose (DEBUG) logging                                                 |

The `--ignore-file` name is matched with or without a leading dot, so `--ignore-file gitignore` and `--ignore-file .gitignore` behave the same when a `.gitignore` is present. Without the option, the ignore file named by the `ignore-file` [setting](#settings) is used, if one is set; `--ignore-file ""` honors no ignore file for that run.

Without `--exclude`, the directories named by the `exclude` [setting](#settings) are excluded, if it is set. Directories given with `--exclude` are used in place of the configured ones for that run, not on top of them, and `--exclude ""` excludes no directory.

The sorting and annotation flags (`--sort-by-*`, `--loc`, `--size`, `--mtime`, `--git-status`) follow a specific resolution model when several are combined; that model is described in the [Sorting and Display Flags](#sorting-and-display-flags) section below.

!!! note "Pattern scope"

    `--exclude-pattern` and `--include-pattern` match against each file's **name**, not its path. For path-based filtering, use `--exclude` (directory names) or `--ignore-file` (gitignore-style). See [Pattern Matching](pattern-matching.md).

## Sorting and Display Flags

Recursivist keeps two concerns separate: **how files are ordered** and **what each file is annotated with**. The flags fall into three families.

| Family           | Flags                                                                                             | Effect                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Sorting-only** | `--sort-by-similarity` (`-S`)                                                                     | Reorders files; adds no annotation of its own                   |
| **Combined**     | `--sort-by-loc` (`-s`), `--sort-by-size` (`-z`), `--sort-by-mtime` (`-m`), `--sort-by-git-status` | Reorders files by a metric **and** annotates every file with it |
| **Display-only** | `--loc`, `--size`, `--mtime`, `--git-status` (`-G`)                                               | Annotates files with a metric **without** changing the order    |

The combined numeric flags (`--sort-by-loc`, `--sort-by-size`, `--sort-by-mtime`) are shorthand for "sort by this metric and display it too" — equivalent to pairing a sort with the matching display-only flag.

### Resolution by command-line order

When several of these flags are combined, they are resolved strictly by their **left-to-right order on the command line**, not by any fixed precedence:

- **Only the first sorting flag takes effect.** Every later sorting flag — whether sorting-only or combined — is discarded completely, contributing neither ordering nor annotation. So `--sort-by-loc --sort-by-size` sorts by lines of code and shows **only** the LOC annotation; the `--sort-by-size` is dropped.
- **Display-only flags always annotate,** in the exact order they are given.
- **A winning combined numeric metric annotates first,** ahead of any display-only annotations.
- **A Git-status marker always trails last,** after every numeric annotation.

To sort by one metric while displaying others, pair a single sorting flag with display-only flags. For example, `--sort-by-loc --size --mtime` orders files by lines of code and annotates each with its LOC, size, and modification time, in that order.

All three commands (`visualize`, `export`, and `compare`) support every sorting and display flag. In `compare`, Git status is read independently for each directory, so each side is annotated against its own repository.

## GitHub Repositories

`visualize`, `export`, and `compare` accept a GitHub repository URL anywhere they accept a local directory path. The repository's source archive is downloaded into a temporary directory, scanned exactly like a local directory, and removed once the command finishes.

### Accepted URL forms

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

When no ref is pinned, the repository's default branch is used. A `/tree/` or `/blob/` selector pins a branch, tag, or commit, and any path after the ref scopes the scan to that subtree, so the tree is rooted at the subtree rather than the repository root. When that path names a file rather than a folder — as in the URL of a file's page on GitHub — the folder containing the file is scanned instead (the repository root, for a top-level file), and a message says so. The segment immediately after `/tree/` or `/blob/` is read as the ref, so a ref whose own name contains a slash (such as `feature/login`) cannot be combined with a subpath in a single URL; pass the repository without a selector, or pin a ref whose name has no slash. The SSH form addresses the whole repository only and carries no ref or subpath.

The scheme and host are case-insensitive (`https://GitHub.com/owner/repo` works); the owner, repository, ref, and subpath are used exactly as written. Because the scheme-less form is also a valid relative path, an argument such as `github.com/golang/go` is treated as a local directory when that path exists (for example, a GOPATH-style checkout); add `https://` to force the GitHub repository.

### Authentication

A token in the `GITHUB_TOKEN` environment variable — or `GH_TOKEN` when `GITHUB_TOKEN` is unset — is sent with each request, which raises GitHub's rate limits and grants access to private repositories.

```bash
export GITHUB_TOKEN=ghp_your_token_here
recursivist visualize https://github.com/owner/private-repo
```

### Options for a GitHub input

A hosted repository already reflects its own ignore rules, and every file in a checkout shares a single Git status and modification time (the tip commit's). The options that depend on those are skipped for a GitHub input, with an informational message naming the ones that were skipped:

| Option                                 | Behavior for a GitHub input                                                                                                  |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `--ignore-file`                        | Skipped                                                                                                                      |
| `--git-status`, `--sort-by-git-status` | Skipped                                                                                                                      |
| `--mtime`, `--sort-by-mtime`           | Skipped                                                                                                                      |
| `--loc`, `--sort-by-loc`               | Applied, since lines of code come from the file contents                                                                     |
| `--size`, `--sort-by-size`             | Applied, since sizes come from the file contents                                                                             |
| `--full-path`                          | Applied; shows each file's GitHub blob URL (`https://github.com/owner/repo/blob/<ref>/<path>`) in place of a filesystem path |

The `ignore-file` [setting](#settings) is not applied to a GitHub input either, and no message is shown for it. The `exclude` setting of your user preferences is applied to a GitHub input, as `--exclude` is.

In `compare`, `--ignore-file`, `--git-status`, and `--mtime` are skipped for a given side only when that side is a GitHub repository. When both inputs are GitHub repositories they are skipped entirely; in a mixed comparison — one local directory and one GitHub repository — they still apply to the local side. The sorting flags `--sort-by-git-status` and `--sort-by-mtime` are skipped whenever either input is a GitHub repository, because both sides share one ordering.

## `visualize`

Display a directory structure as a tree in the terminal.

```bash
recursivist visualize [OPTIONS] [DIRECTORY]
```

| Argument    | Description                                                                         |
| ----------- | ----------------------------------------------------------------------------------- |
| `DIRECTORY` | Directory or GitHub repository URL to visualize (defaults to the current directory) |

`visualize` supports the [shared options](#shared-options) and the full set of [sorting and display flags](#sorting-and-display-flags). When `DIRECTORY` is a [GitHub repository URL](#github-repositories), the repository is downloaded and scanned in place of a local directory.

### Examples

```bash
recursivist visualize
recursivist visualize /path/to/project
recursivist visualize --exclude node_modules --exclude .git
recursivist visualize --exclude-ext .pyc --exclude-ext .log
recursivist visualize --exclude-pattern "*.test.js" --exclude-pattern "*.spec.js"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
recursivist visualize --include-pattern "*.md" --include-pattern "*.py"
recursivist visualize --ignore-file .gitignore
recursivist visualize --depth 3
recursivist visualize --full-path
recursivist visualize --sort-by-loc              # sort by and show lines of code
recursivist visualize --sort-by-loc --size       # sort by LOC, show LOC and size
recursivist visualize --mtime --git-status       # annotate only: mtime, then Git status
recursivist visualize --git-status               # Git status markers
recursivist visualize --sort-by-git-status       # sort by and show Git status
recursivist visualize --icon-style nerd
recursivist visualize https://github.com/owner/repo                     # a GitHub repository
recursivist visualize https://github.com/owner/repo/tree/main/src -l    # a subtree, showing blob URLs
```

## `export`

Export a directory structure to one or more files.

```bash
recursivist export [OPTIONS] [DIRECTORY]
```

| Argument    | Description                                                                      |
| ----------- | -------------------------------------------------------------------------------- |
| `DIRECTORY` | Directory or GitHub repository URL to export (defaults to the current directory) |

In addition to the [shared options](#shared-options) and the [sorting and display flags](#sorting-and-display-flags), `export` supports:

| Option         | Short | Description                                                              |
| -------------- | ----- | ------------------------------------------------------------------------ |
| `--format`     | `-f`  | Export formats: `txt`, `json`, `html`, `md`, `svg`, `rst` (default `md`) |
| `--output-dir` | `-o`  | Output directory (created if missing; defaults to current directory)     |
| `--prefix`     | `-n`  | Filename prefix for exports (default `structure`)                        |

Exports default to the `emoji` icon style for cross-platform consistency, regardless of saved or project configuration; the `ignore-file` and `exclude` [settings](#settings) apply to exports as they do to the other commands. `DIRECTORY` may also be a [GitHub repository URL](#github-repositories), in which case the repository is downloaded and scanned in place of a local directory.

### Examples

```bash
recursivist export
recursivist export --format html
recursivist export --format "json html md"
recursivist export --format txt --output-dir ./exports
recursivist export --format json --prefix my-project
recursivist export --exclude node_modules --exclude-ext .pyc
recursivist export --format html --sort-by-loc --size   # sort by LOC, show LOC and size
recursivist export --format md --git-status             # Git status markers
recursivist export --format md --icon-style nerd
recursivist export https://github.com/owner/repo --format md          # a GitHub repository
recursivist export https://github.com/owner/repo --format md -l       # blob URLs as full paths
```

## `compare`

Compare two directory structures side by side.

```bash
recursivist compare [OPTIONS] DIR1 DIR2
```

| Argument | Description                                          |
| -------- | ---------------------------------------------------- |
| `DIR1`   | First directory or GitHub repository URL to compare  |
| `DIR2`   | Second directory or GitHub repository URL to compare |

In addition to the [shared options](#shared-options) and the [sorting and display flags](#sorting-and-display-flags), `compare` supports:

| Option         | Short | Description                                                        |
| -------------- | ----- | ------------------------------------------------------------------ |
| `--save`       | `-f`  | Save the comparison as an HTML file instead of printing it         |
| `--output-dir` | `-o`  | Output directory for the HTML file (defaults to current directory) |
| `--prefix`     | `-n`  | Filename prefix for the HTML file (default `comparison`)           |

!!! note

    In `compare`, `-f` is shorthand for `--save`, not `--format`. Items unique to `DIR1` are highlighted in green, items unique to `DIR2` in red. When Git status is enabled, it is read independently for each directory, so each side is annotated against its own repository. Either input may be a [GitHub repository URL](#github-repositories); a local directory can be compared against a GitHub repository, or two GitHub repositories against each other.

### Examples

```bash
recursivist compare dir1 dir2
recursivist compare dir1 dir2 --exclude node_modules --exclude .git
recursivist compare dir1 dir2 --depth 2
recursivist compare dir1 dir2 --save --output-dir ./reports
recursivist compare dir1 dir2 --sort-by-loc --size   # sort by LOC, show LOC and size
recursivist compare dir1 dir2 --git-status           # annotate each side with Git status
recursivist compare dir1 dir2 --sort-by-git-status   # sort each side by Git status
recursivist compare ./local-fork https://github.com/owner/repo          # local vs. GitHub
recursivist compare https://github.com/owner/repo-a https://github.com/owner/repo-b   # GitHub vs. GitHub
```

## `config`

Manage persistent user preferences, stored as JSON in your platform's application-data directory (for example, `~/.config/recursivist/config.json` on Linux).

```bash
recursivist config set KEY VALUE...
recursivist config unset KEY
recursivist config reset [OPTIONS]
recursivist config get KEY
recursivist config list [OPTIONS] [DIRECTORY]
recursivist config path
```

| Argument    | Description                                                                                                                                     |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `KEY`       | Configuration key: `icon-style`, `ignore-file`, or `exclude`                                                                                    |
| `VALUE`     | Value to set: `emoji` or `nerd` for `icon-style`, a file name such as `.gitignore` for `ignore-file`, one or more directory names for `exclude` |
| `DIRECTORY` | Directory whose project configuration applies, for `config list` (defaults to the current directory)                                            |

`config list` supports:

| Option   | Short | Description                                        |
| -------- | ----- | -------------------------------------------------- |
| `--all`  | `-a`  | Show the value of every layer, not only the winner |
| `--json` |       | Print the listing as JSON                          |

`config reset` supports:

| Option  | Short | Description                            |
| ------- | ----- | -------------------------------------- |
| `--yes` | `-y`  | Remove without asking for confirmation |

`config set` saves a value for one of the [settings](#settings). `config unset` removes a saved value, so the setting falls back to its default. `unset` accepts any key, including one Recursivist does not recognize, which makes it the way to clear an entry that is reported with a warning. Both commands change only the key they are given and leave the rest of the file untouched.

`config reset` removes every saved value at once by deleting the file, so each setting falls back to its default. The whole file is removed, including entries Recursivist does not recognize and a file it cannot read, which makes it the way to clear a file that is reported with a warning. It asks for confirmation first, in a question that names the entries about to be removed, and removes nothing unless the answer is yes: declining, or having no answer to read, as in a script, exits with status 1. `--yes` removes without asking. The removed entries are printed with their values, so a value can be saved again with `config set`. When there is no file, nothing is asked or done and the command still succeeds. A [project configuration](#project-configuration) file is left as it is.

`config get` prints the value of a setting: the one saved in the file, or the built-in default when none is saved or the saved one is invalid. For `ignore-file`, whose default is to honor no ignore file, that is an empty line. The directory names of `exclude` are printed one per line, and nothing is printed when no directory is excluded. The value is the only thing written to standard output, so it can be captured in a script; warnings about the file, and the error for a key Recursivist does not recognize, go to standard error. It reads only your user preferences, so a [project configuration](#project-configuration) or a command-line flag can still override the printed value for a run; `config list` shows the value in effect for a directory. Nothing is created or changed.

`config list` prints every setting with the value in effect for a directory and the layer and file that value comes from, taking the [project configuration](#project-configuration) into account. `--all` adds the value of every layer, and `--json` prints the listing as JSON. See [Listing Settings](#listing-settings) for the output. Nothing is created or changed.

`config path` prints where the file is on your system. The path is the only output, so it can be passed straight to another command. It takes no arguments and never reads or creates the file: the path is printed whether or not the file exists, and the file is absent until `config set` saves a value. A [project configuration](#project-configuration) file is not reported.

### Examples

```bash
recursivist config set icon-style nerd
recursivist config set icon-style emoji
recursivist config set ignore-file .gitignore   # honor .gitignore on every run
recursivist config set exclude node_modules .git   # leave these directories out of every run
recursivist config unset icon-style
recursivist config reset                     # remove every saved preference, after confirming
recursivist config reset --yes               # the same without being asked, for scripts
recursivist config get icon-style
recursivist config get ignore-file
recursivist config get exclude               # one directory name per line
recursivist export --icon-style "$(recursivist config get icon-style)"   # export with your saved style
recursivist config list                      # settings in effect for the current directory
recursivist config list ./my-project --all   # every layer's value for a project
recursivist config list --json
recursivist config path
cat "$(recursivist config path)"   # show your saved preferences
```

### Settings

| Key           | Values                            | Default | What it sets                                                                                      |
| ------------- | --------------------------------- | ------- | ------------------------------------------------------------------------------------------------- |
| `icon-style`  | `emoji` or `nerd`                 | `emoji` | The icons of `visualize`, and of `compare` in the terminal                                        |
| `ignore-file` | A file name, such as `.gitignore` | Not set | The ignore file honored by `visualize`, `export`, and `compare` when `--ignore-file` is not given |
| `exclude`     | One or more directory names       | Not set | The directories excluded by `visualize`, `export`, and `compare` when `--exclude` is not given    |

`ignore-file` names a gitignore-style [ignore file](../user-guide/pattern-filtering.md#ignore-files), exactly as `--ignore-file` does: the leading dot is optional, and the file is looked up in the directory being scanned and at every level below it. Any name that is not blank is accepted. A directory that has no file of that name is scanned without one, and no warning is shown, so the setting can be saved once and left on. It is not applied to a [GitHub repository](#github-repositories) input. `--ignore-file NAME` overrides the setting for a run, and `--ignore-file ""` turns it off for a run.

`exclude` names directories to leave out, exactly as `--exclude` does: a directory with one of the names is pruned wherever it appears in the tree. `config set exclude` takes one name per argument, so a name that contains spaces is quoted, and the names given replace the saved ones as a whole. In a configuration file the value is a list of one or more names, none of them blank. The setting is applied to a [GitHub repository](#github-repositories) input as well, from your user preferences. A list is always used whole: a project's list replaces the one in your user preferences without being merged with it, `--exclude NAME` replaces the setting for a run, and `--exclude ""` turns it off for a run.

### Project Configuration

A project can carry its own settings in a TOML file, which override your user preferences for that project. Recursivist reads either of two files:

```toml
# .recursivist.toml
icon-style = "nerd"
ignore-file = ".gitignore"
exclude = ["node_modules", ".git"]
```

```toml
# pyproject.toml
[tool.recursivist]
icon-style = "nerd"
ignore-file = ".gitignore"
exclude = ["node_modules", ".git"]
```

The file is looked up in the directory being scanned, then in each parent directory; the nearest one is used and files further up are not merged in. When a directory holds both files, `.recursivist.toml` is used. A `pyproject.toml` without a `[tool.recursivist]` table is skipped. Project files accept the same keys and values as `config set`, and are edited by hand: `config set` only writes your user preferences.

Each setting is resolved in this order, the first one found winning:

1. The command-line flag (for example `--icon-style`)
2. The project configuration
3. Your user configuration (`config set`)
4. The built-in default

An unknown key or an invalid value is reported with a warning and ignored, so that setting falls through to the next layer. This applies to project files and to your user configuration file alike, so a mistake made while editing either by hand cannot change what is rendered. Remove an entry from your user configuration file with `config unset`, or the whole file with `config reset`. Run `config list` to see which layer and file each setting comes from, or a command with `--verbose` to see which project file was used.

`compare` uses the project configuration of the first local directory given: it looks for the ignore file that configuration names in each local directory, and excludes the directories it names from both sides. A [GitHub repository](#github-repositories) input has no project configuration.

### Listing Settings

`config list` resolves each setting the way a command run on `DIRECTORY` does, through the [project configuration](#project-configuration), your user configuration, and the built-in default, and prints the winning value with the layer and file it comes from:

```text
$ recursivist config list ./my-project
icon-style  = nerd                (project: /home/me/my-project/.recursivist.toml)
ignore-file = .gitignore          (user: /home/me/.config/recursivist/config.json)
exclude     = node_modules, .git  (user: /home/me/.config/recursivist/config.json)
```

The origin is `project` or `user` followed by the file that sets the value, or `default` when no file sets it. `ignore-file` and `exclude` have no built-in value, so when no file sets one of them, it is listed as `(not set)` with the origin `default`. The directory names of `exclude` are listed on one line, separated by commas.

`--all` lists the value of every layer under the setting, from the highest precedence to the lowest. The winning layer is marked with `*`, and a layer that does not set the value shows `(not set)`. A layer's file is named whenever it exists, even when it does not set the value, so the listing shows every file that is consulted:

```text
$ recursivist config list ./my-project --all
icon-style = nerd
  * project  nerd                /home/me/my-project/.recursivist.toml
    user     emoji               /home/me/.config/recursivist/config.json
    default  emoji
ignore-file = .gitignore
    project  (not set)           /home/me/my-project/.recursivist.toml
  * user     .gitignore          /home/me/.config/recursivist/config.json
    default  (not set)
exclude = node_modules, .git
    project  (not set)           /home/me/my-project/.recursivist.toml
  * user     node_modules, .git  /home/me/.config/recursivist/config.json
    default  (not set)
```

`--json` prints the listing as a JSON object keyed by setting. Each entry holds the winning `value`, the `layer` it comes from (`project`, `user`, or `default`), and its `source` file, which is `null` for a built-in default. The `value` is `null` for a setting that no layer sets, and an array of directory names for `exclude`:

```json
{
    "icon-style": {
        "value": "nerd",
        "layer": "project",
        "source": "/home/me/my-project/.recursivist.toml"
    },
    "ignore-file": {
        "value": ".gitignore",
        "layer": "user",
        "source": "/home/me/.config/recursivist/config.json"
    },
    "exclude": {
        "value": ["node_modules", ".git"],
        "layer": "user",
        "source": "/home/me/.config/recursivist/config.json"
    }
}
```

With `--all` as well, each entry also has a `layers` array holding the same three fields for every layer, in the same order as the text listing. There, `value` is `null` for a layer that does not set it, and `source` is `null` for a layer that has no file.

The listing is the only thing written to standard output, so it can be piped to another program; warnings about a configuration file, and the error for a `DIRECTORY` that is not a directory, go to standard error. An invalid value is reported with a warning and counts as not set, as it does for a run.

A command-line flag such as `--icon-style`, `--ignore-file`, or `--exclude` still overrides the listed value for a run, and exports use the `emoji` icon style unless `--icon-style` is given.

## `version`

Print the installed version.

```bash
recursivist version
```
