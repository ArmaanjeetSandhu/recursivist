# CLI Reference

A complete reference for every Recursivist command and option. For explanations and worked examples, follow the links into the [User Guide](../user-guide/basic-usage.md).

## Commands

| Command                   | Description                                   |
| ------------------------- | --------------------------------------------- |
| [`visualize`](#visualize) | Display a directory structure in the terminal |
| [`export`](#export)       | Export a directory structure to files         |
| [`compare`](#compare)     | Compare two directory structures side by side |
| [`config`](#config)       | Manage persistent user preferences            |
| [`version`](#version)     | Show the installed version                    |

Two top-level options manage [shell completion](../user-guide/shell-completion.md): `--install-completion` and `--show-completion`. `--help` is available at the top level and on every command.

## Shared Options

The following options are common to `visualize`, `export`, and `compare`.

| Option                 | Short | Value          | Description                                                                    |
| ---------------------- | ----- | -------------- | ------------------------------------------------------------------------------ |
| `--exclude`            | `-e`  | Name           | Directory name to exclude (repeatable)                                         |
| `--exclude-ext`        | `-x`  | Extension      | File extension to exclude, leading dot optional (repeatable)                   |
| `--exclude-pattern`    | `-p`  | Pattern        | File-name pattern to exclude; glob by default, regex with `-r` (repeatable)    |
| `--include-pattern`    | `-i`  | Pattern        | File-name pattern to include (repeatable)                                      |
| `--regex`              | `-r`  |                | Treat patterns as regular expressions instead of globs                         |
| `--ignore-file`        | `-g`  | File name      | Gitignore-style ignore file to honor (e.g. `.gitignore`)                       |
| `--depth`              | `-d`  | Integer        | Maximum depth to traverse (`0`, the default, for unlimited)                    |
| `--full-path`          | `-l`  |                | Show full paths instead of bare filenames (GitHub blob URLs for GitHub inputs) |
| `--sort-by-similarity` | `-S`  |                | Group files with similar names together                                        |
| `--sort-by-loc`        | `-s`  |                | Sort files by lines of code and display LOC counts                             |
| `--sort-by-size`       | `-z`  |                | Sort files by size and display file sizes                                      |
| `--sort-by-mtime`      | `-m`  |                | Sort files by modification time and display timestamps                         |
| `--sort-by-git-status` |       |                | Sort files by Git status and display status markers                            |
| `--loc`                |       |                | Display lines of code without affecting sort order                             |
| `--size`               |       |                | Display file sizes without affecting sort order                                |
| `--mtime`              |       |                | Display modification times without affecting sort order                        |
| `--git-status`         | `-G`  |                | Display Git status markers without affecting sort order                        |
| `--icon-style`         |       | `emoji`/`nerd` | Icon style                                                                     |
| `--verbose`            | `-v`  |                | Enable verbose (DEBUG) logging                                                 |

Notes:

- **Repeatable options** take one value per flag; repeat the flag to supply several values (e.g. `--exclude node_modules --exclude .git`). Because each value is used verbatim, values may contain spaces — quote them, e.g. `--exclude "Application Support"`.
- **Pattern scope.** `--exclude-pattern` and `--include-pattern` match against each file's **name**, not its path. For path-based filtering, use `--exclude` (directory names) or `--ignore-file` (gitignore-style). See [Pattern Matching](pattern-matching.md) for the syntax and [Pattern Filtering](../user-guide/pattern-filtering.md#order-of-precedence) for the order in which filters are applied.
- **`--ignore-file`** matches the name with or without a leading dot, so `--ignore-file gitignore` and `--ignore-file .gitignore` behave the same when a `.gitignore` is present. Without the option, the ignore file named by the `ignore-file` [setting](../user-guide/configuration.md#settings) is used, if one is set; `--ignore-file ""` honors no ignore file for that run.
- **`--exclude`**, when omitted, falls back to the directories named by the `exclude` [setting](../user-guide/configuration.md#settings), if it is set. Directories given with `--exclude` are used in place of the configured ones for that run, not on top of them, and `--exclude ""` excludes no directory.
- **`--icon-style`**, when omitted, falls back to the `icon-style` setting in `visualize` and in `compare` in the terminal; `export` and `compare --save` default to `emoji`.

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

### Sort order

| Sort                   | Order                                                                      |
| ---------------------- | -------------------------------------------------------------------------- |
| Default                | By extension, then by name (case-insensitive)                              |
| `--sort-by-loc`        | Most lines first                                                           |
| `--sort-by-size`       | Largest first                                                              |
| `--sort-by-mtime`      | Newest first                                                               |
| `--sort-by-git-status` | Modified, added, deleted, untracked, then clean; by name within each group |
| `--sort-by-similarity` | Files with similar names adjacent                                          |

Files are always listed before subdirectories. See [Sorting and Statistics](../user-guide/sorting-and-statistics.md) for examples of each.

## GitHub Repositories

Wherever `visualize`, `export`, and `compare` take a directory, they also take a GitHub repository URL, optionally with a `/tree/<ref>` or `/blob/<ref>/<subpath>` selector. `--ignore-file`, `--git-status`, `--sort-by-git-status`, `--mtime`, and `--sort-by-mtime` are skipped for a GitHub input. A token in `GITHUB_TOKEN` (or `GH_TOKEN`) is used when set.

The accepted URL forms and the behavior of every option are documented in [GitHub Repositories](../user-guide/github-repositories.md).

## `visualize`

Display a directory structure as a tree in the terminal.

```bash
recursivist visualize [OPTIONS] [DIRECTORY]
```

| Argument    | Description                                                                         |
| ----------- | ----------------------------------------------------------------------------------- |
| `DIRECTORY` | Directory or GitHub repository URL to visualize (defaults to the current directory) |

`visualize` takes the [shared options](#shared-options) and no others.

```bash
recursivist visualize
recursivist visualize /path/to/project --depth 3
recursivist visualize --exclude node_modules --exclude .git --exclude-ext .pyc
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
recursivist visualize --sort-by-loc --size       # sort by LOC, show LOC and size
recursivist visualize --mtime --git-status       # annotate only: mtime, then Git status
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

In addition to the [shared options](#shared-options), `export` supports:

| Option         | Short | Description                                                                                   |
| -------------- | ----- | --------------------------------------------------------------------------------------------- |
| `--format`     | `-f`  | [Export formats](export-formats.md): `txt`, `json`, `html`, `md`, `svg`, `rst` (default `md`) |
| `--output-dir` | `-o`  | Output directory (created if missing; defaults to current directory)                          |
| `--prefix`     | `-n`  | Filename prefix for exports (default `structure`)                                             |

`--format` accepts several formats, either space-separated in one value (`--format "txt json"`) or by repeating the flag. One file is written per format, named `<prefix>.<format>`.

```bash
recursivist export
recursivist export --format "json html md"
recursivist export --format txt --output-dir ./exports --prefix my-project
recursivist export --format html --sort-by-loc --size   # sort by LOC, show LOC and size
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

In addition to the [shared options](#shared-options), `compare` supports:

| Option         | Short | Description                                                        |
| -------------- | ----- | ------------------------------------------------------------------ |
| `--save`       | `-f`  | Save the comparison as an HTML file instead of printing it         |
| `--output-dir` | `-o`  | Output directory for the HTML file (defaults to current directory) |
| `--prefix`     | `-n`  | Filename prefix for the HTML file (default `comparison`)           |

Notes:

- In `compare`, `-f` is shorthand for `--save`, not `--format`.
- In each panel, items found only on that side are highlighted in green and items found only on the other side in red.
- Git status is read independently for each directory, so each side is annotated against its own repository.
- Settings come from the [project configuration](../user-guide/configuration.md#how-commands-use-settings) of the first local directory given.

```bash
recursivist compare dir1 dir2
recursivist compare dir1 dir2 --exclude node_modules --exclude .git --depth 2
recursivist compare dir1 dir2 --save --output-dir ./reports
recursivist compare dir1 dir2 --sort-by-loc --size   # sort by LOC, show LOC and size
recursivist compare ./local-fork https://github.com/owner/repo          # local vs. GitHub
```

## `config`

Manage persistent user preferences, stored as JSON in your platform's application-data directory (for example, `~/.config/recursivist/config.json` on Linux). [Configuration](../user-guide/configuration.md) explains the settings, project configuration files, and the order of precedence.

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

The subcommands write only your user preferences file. A project configuration file is never created, changed, or removed; `config list` is the only subcommand that reads one.

### `config set`

Saves a value for one of the settings. `exclude` takes one name per argument, and the names given replace the saved ones as a whole; every other key takes exactly one value. Only the key given is changed; the rest of the file is left untouched.

### `config unset`

Removes a saved value, so the setting falls back to its default. `unset` accepts any key, including one Recursivist does not recognize, which makes it the way to clear an entry that is reported with a warning. Only the key given is changed.

### `config reset`

| Option  | Short | Description                            |
| ------- | ----- | -------------------------------------- |
| `--yes` | `-y`  | Remove without asking for confirmation |

Removes every saved value at once by deleting the file, so each setting falls back to its default. The whole file is removed, including entries Recursivist does not recognize and a file it cannot read, which makes it the way to clear a file that is reported with a warning.

It asks for confirmation first, in a question that names the entries about to be removed, and removes nothing unless the answer is yes: declining, or having no answer to read, as in a script, exits with status 1. `--yes` removes without asking. The removed entries are printed with their values, so a value can be saved again with `config set`. When there is no file, nothing is asked or done and the command still succeeds.

### `config get`

Prints the value of a setting: the one saved in the file, or the built-in default when none is saved or the saved one is invalid. For `ignore-file`, whose default is to honor no ignore file, that is an empty line. The directory names of `exclude` are printed one per line, and nothing is printed when no directory is excluded.

The value is the only thing written to standard output, so it can be captured in a script; warnings about the file, and the error for a key Recursivist does not recognize, go to standard error. It reads only your user preferences, so a project configuration or a command-line flag can still override the printed value for a run; `config list` shows the value in effect for a directory. Nothing is created or changed.

### `config list`

| Option   | Short | Description                                        |
| -------- | ----- | -------------------------------------------------- |
| `--all`  | `-a`  | Show the value of every layer, not only the winner |
| `--json` |       | Print the listing as JSON                          |

Resolves each setting the way a command run on `DIRECTORY` does, through the project configuration, your user configuration, and the built-in default, and prints the winning value with the layer and file it comes from:

```bash
recursivist config list ./my-project
```

<div class="terminal-demo compact">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>icon-style  = nerd                (project: /home/me/my-project/.recursivist.toml)
ignore-file = .gitignore          (user: /home/me/.config/recursivist/config.json)
exclude     = node_modules, .git  (user: /home/me/.config/recursivist/config.json)</pre>
    </div>
  </div>
</div>

The origin is `project` or `user` followed by the file that sets the value, or `default` when no file sets it. `ignore-file` and `exclude` have no built-in value, so when no file sets one of them, it is listed as `(not set)` with the origin `default`. The directory names of `exclude` are listed on one line, separated by commas.

`--all` lists the value of every layer under the setting, from the highest precedence to the lowest. The winning layer is marked with `*`, and a layer that does not set the value shows `(not set)`. A layer's file is named whenever it exists, even when it does not set the value, so the listing shows every file that is consulted:

```bash
recursivist config list ./my-project --all
```

<div class="terminal-demo compact">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>icon-style = nerd
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
    default  (not set)</pre>
    </div>
  </div>
</div>

`--json` prints the listing as a JSON object keyed by setting. Each entry holds the winning `value`, the `layer` it comes from (`project`, `user`, or `default`), and its `source` file, which is `null` for a built-in default. The `value` is `null` for a setting that no layer sets, and an array of directory names for `exclude`:

```bash
recursivist config list ./my-project --json
```

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>{
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
    "value": [
      "node_modules",
      ".git"
    ],
    "layer": "user",
    "source": "/home/me/.config/recursivist/config.json"
  }
}</pre>
    </div>
  </div>
</div>

With `--all` as well, each entry also has a `layers` array holding the same three fields for every layer, in the same order as the text listing. There, `value` is `null` for a layer that does not set it, and `source` is `null` for a layer that has no file.

The listing is the only thing written to standard output, so it can be piped to another program; warnings about a configuration file, and the error for a `DIRECTORY` that is not a directory, go to standard error. An invalid value is reported with a warning and counts as not set, as it does for a run. Nothing is created or changed.

A command-line flag such as `--icon-style`, `--ignore-file`, or `--exclude` still overrides the listed value for a run, and exports use the `emoji` icon style unless `--icon-style` is given.

### `config path`

Prints where the user preferences file is on your system. The path is the only output, so it can be passed straight to another command. It takes no arguments and never reads or creates the file: the path is printed whether or not the file exists, and the file is absent until `config set` saves a value. A project configuration file is not reported.

### Examples

```bash
recursivist config set icon-style nerd
recursivist config set ignore-file .gitignore   # honor .gitignore on every run
recursivist config set exclude node_modules .git   # leave these directories out of every run
recursivist config unset icon-style
recursivist config reset --yes               # remove every saved preference without being asked
recursivist config get exclude               # one directory name per line
recursivist config list ./my-project --all   # every layer's value for a project
recursivist config list --json
recursivist config path
```

## `version`

Print the installed version.

```bash
recursivist version
```

## Exit Codes

| Code | Meaning                                                                                                                                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`  | Success                                                                                                                                                 |
| `1`  | An error occurred: an invalid directory, an unsupported export format, a failure during scanning or writing, or a `config reset` that was not confirmed |
| `2`  | The command line could not be parsed: an unknown option or a missing argument                                                                           |
