# Configuration

Options you would otherwise pass on every run can be saved once. Recursivist has five settings, and each can be set in three places: on the command line for a single run, in a project file for everyone who works on a project, and in your own user preferences.

## Settings

| Key           | Values                            | Default    | What it sets                                                                                      |
| ------------- | --------------------------------- | ---------- | ------------------------------------------------------------------------------------------------- |
| `icon-style`  | `emoji` or `nerd`                 | `emoji`    | The icons of `visualize`, and of `compare` in the terminal                                        |
| `date-format` | `relative` or `iso`               | `relative` | How `visualize`, and `compare` in the terminal, write modification times                          |
| `size-format` | `iec` or `si`                     | `iec`      | How `visualize`, `export`, and `compare` write file sizes                                         |
| `ignore-file` | A file name, such as `.gitignore` | Not set    | The ignore file honored by `visualize`, `export`, and `compare` when `--ignore-file` is not given |
| `exclude`     | One or more directory names       | Not set    | The directories excluded by `visualize`, `export`, and `compare` when `--exclude` is not given    |

**`icon-style`** chooses between the two [icon styles](visualization.md#icon-styles). Exported files, and a comparison saved as HTML, use the `emoji` style regardless of this setting, to render consistently on any machine; pass `--icon-style nerd` to override that for a run.

**`date-format`** chooses between the two [date formats](sorting-and-statistics.md#date-format) of a modification time: `relative` (`Today 14:30`) or `iso` (`2026-10-07T12:30:41Z`). Exported files, and a comparison saved as HTML, use the `iso` format regardless of this setting, because a relative time stops being true once the file is read on another day; pass `--date-format relative` to override that for a run.

**`size-format`** chooses between the two [size formats](sorting-and-statistics.md#size-format) of a file size: `iec` (`4.2 MiB`, powers of 1024) or `si` (`4.4 MB`, powers of 1000). Unlike the two settings above, it applies to exported files and to a comparison saved as HTML as well, because a size reads the same wherever and whenever the file is opened.

**`ignore-file`** names a gitignore-style [ignore file](pattern-filtering.md#ignore-files), exactly as `--ignore-file` does: the leading dot is optional, and the file is looked up in the directory being scanned and at every level below it. Any name that is not blank is accepted. A directory that has no file of that name is scanned without one, and no warning is shown, so the setting can be saved once and left on.

**`exclude`** names directories to leave out, exactly as `--exclude` does: a directory with one of the names is pruned wherever it appears in the tree. A list is always used whole, never merged with another: a project's list replaces the one in your user preferences, and `--exclude` replaces both for a run.

## Order of Precedence

Each setting is resolved in this order, the first one found winning:

1. The command-line flag (`--icon-style`, `--date-format`, `--size-format`, `--ignore-file`, or `--exclude`)
2. The [project configuration](#project-configuration)
3. Your [user preferences](#user-preferences) (`config set`)
4. The built-in default

To switch a saved setting off for one run, pass the flag with an empty value: `--ignore-file ""` honors no ignore file, and `--exclude ""` excludes no directory.

## User Preferences

Your own preferences are stored as JSON in your platform's application-data directory (for example, `~/.config/recursivist/config.json` on Linux) and managed with the `config` command:

```bash
# Save a value
recursivist config set icon-style nerd
recursivist config set date-format iso             # ISO 8601 modification times in the terminal
recursivist config set size-format si              # sizes in kB, MB, GB on every run
recursivist config set ignore-file .gitignore      # honor .gitignore on every run
recursivist config set exclude node_modules .git   # leave these directories out of every run

# Read a value back
recursivist config get icon-style

# Remove one saved value, or all of them
recursivist config unset icon-style
recursivist config reset

# Print where the file is
recursivist config path
```

`config set exclude` takes one name per argument (quote a name that contains spaces), and the names given replace the saved ones as a whole. `config get` prints the saved value, or the built-in default when none is saved. `config reset` asks for confirmation before deleting the file; add `--yes` to skip the question in a script.

The [CLI Reference](../reference/cli-reference.md#config) describes each subcommand's output and exit status precisely.

## Project Configuration

A project can carry its own settings in a TOML file, which override your user preferences for that project. Recursivist reads either of two files:

```toml
# .recursivist.toml
icon-style = "nerd"
date-format = "iso"
size-format = "si"
ignore-file = ".gitignore"
exclude = ["node_modules", ".git"]
```

```toml
# pyproject.toml
[tool.recursivist]
icon-style = "nerd"
date-format = "iso"
size-format = "si"
ignore-file = ".gitignore"
exclude = ["node_modules", ".git"]
```

The file is looked up in the directory being scanned, then in each parent directory; the nearest one is used and files further up are not merged in. When a directory holds both files, `.recursivist.toml` is used. A `pyproject.toml` without a `[tool.recursivist]` table is skipped.

Project files accept the same keys and values as `config set` (`exclude` is a list of one or more names, none of them blank), and are edited by hand: `config set` only writes your user preferences.

## Seeing What Is in Effect

`config list` resolves each setting the way a command run on a directory does, and prints the winning value with the layer and file it comes from:

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
date-format = relative            (default)
size-format = iec                 (default)
ignore-file = .gitignore          (user: /home/me/.config/recursivist/config.json)
exclude     = node_modules, .git  (user: /home/me/.config/recursivist/config.json)</pre>
    </div>
  </div>
</div>

The directory defaults to the current one. Add `--all` to see the value of every layer, or `--json` for machine-readable output; both are described in the [CLI Reference](../reference/cli-reference.md#config-list). A command-line flag still overrides the listed value for a run. Running any command with `--verbose` also reports which project file was used.

## Invalid Values

An unknown key or an invalid value is reported with a warning and ignored, and that setting falls through to the next layer. This applies to project files and to your user preferences file alike, so a mistake made while editing either by hand cannot change what is rendered. Remove a bad entry from your user preferences with `config unset` — it accepts any key, including one Recursivist does not recognize — or remove the whole file with `config reset`.

## How Commands Use Settings

- **`export`** applies `size-format`, `ignore-file`, and `exclude` as the other commands do, but always defaults to the `emoji` icon style and the `iso` date format.
- **`compare --save`** defaults to the `emoji` icon style and the `iso` date format in the same way; in the terminal, `compare` uses the `icon-style` and `date-format` settings. It uses the `size-format` setting either way.
- **`compare`** uses the project configuration of the first local directory given: it looks for the ignore file that configuration names in each local directory, and excludes the directories it names from both sides.
- **A GitHub repository input** has no project configuration. The `ignore-file` setting is not applied to it; the `size-format` and `exclude` settings of your user preferences are. See [GitHub Repositories](github-repositories.md#which-options-apply).
