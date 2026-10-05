# Basic Usage

Recursivist is built around three commands — `visualize`, `export`, and `compare` — that share one set of filtering, sorting, and display options. This page covers what they have in common; each of the other guides goes deeper into one topic.

## Command Structure

```bash
recursivist [COMMAND] [OPTIONS] [ARGUMENTS]
```

The available commands are:

| Command     | Purpose                                       | Guide                             |
| ----------- | --------------------------------------------- | --------------------------------- |
| `visualize` | Display a directory structure in the terminal | [Visualization](visualization.md) |
| `export`    | Export a directory structure to files         | [Export](export.md)               |
| `compare`   | Compare two directory structures side by side | [Compare](compare.md)             |
| `config`    | Manage persistent user preferences            | [Configuration](configuration.md) |
| `version`   | Show the installed version                    |                                   |

## Getting Help

Every command has built-in help:

```bash
recursivist --help            # list all commands
recursivist visualize --help  # options for a specific command
```

## Default Behavior

By default, `visualize` and `export`:

- Include every file and directory in the target location. Nothing is left out unless you ask: a `.git` directory is listed like any other, and a `.gitignore` is not read until you [name it](pattern-filtering.md#ignore-files).
- Apply no depth limit.
- Show bare filenames rather than full paths.
- Color files by extension (colors are derived deterministically from the extensions present, so the same set of file types always gets the same colors).
- List files before subdirectories, ordering files by extension and then name.
- Label entries with generic emoji icons (📄 for files, 📂 for directories that have contents, and 📁 for empty ones).

## Shared Options

`visualize`, `export`, and `compare` accept the same options for choosing what is shown and how:

| To...                                          | Use                                                                                                        | Guide                                                          |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Leave out directories, file types, or files    | `--exclude`, `--exclude-ext`, `--exclude-pattern`, `--include-pattern`, `--regex`, `--ignore-file`         | [Pattern Filtering](pattern-filtering.md)                      |
| Limit how deep the tree goes                   | `--depth`                                                                                                  | [Visualization](visualization.md#directory-depth-control)      |
| Show full paths instead of bare filenames      | `--full-path`                                                                                              | [Visualization](visualization.md#full-path-display)            |
| Sort files, or annotate them with a metric     | `--sort-by-loc`, `--sort-by-size`, `--sort-by-mtime`, `--sort-by-similarity`, `--loc`, `--size`, `--mtime` | [Sorting and Statistics](sorting-and-statistics.md)            |
| Show or sort by Git status                     | `--git-status`, `--sort-by-git-status`                                                                     | [Sorting and Statistics](sorting-and-statistics.md#git-status) |
| Choose between emoji and Nerd Font icons       | `--icon-style`                                                                                             | [Visualization](visualization.md#icon-styles)                  |
| See how filters and settings are being applied | `--verbose`                                                                                                | [Below](#verbose-output)                                       |

Two more things apply to all three commands:

- Wherever a command takes a directory, it also takes a GitHub repository URL. See [GitHub Repositories](github-repositories.md).
- Options you would otherwise repeat on every run — the icon style, an ignore file, directories to exclude — can be saved for yourself or for a project. See [Configuration](configuration.md).

The [CLI Reference](../reference/cli-reference.md) lists every option with its short form.

## Verbose Output

```bash
recursivist visualize --verbose
```

Verbose mode lowers the log level to `DEBUG`, printing details about how patterns and filters are applied and which project configuration file was used — useful when a filter isn't behaving as expected.

## Exit Codes

| Code | Meaning                                                                                                                      |
| ---- | ---------------------------------------------------------------------------------------------------------------------------- |
| `0`  | Success                                                                                                                      |
| `1`  | An error occurred (for example, an invalid directory, an unsupported export format, or a failure during scanning or writing) |
| `2`  | The command line could not be parsed (for example, an unknown option or a missing argument)                                  |

These make Recursivist easy to use in scripts and automation; see [Scripting and Python](../recipes/scripting.md).

## Next Steps

- [Visualization](visualization.md) — terminal output options in depth
- [Sorting and Statistics](sorting-and-statistics.md) — ordering files and annotating them with metrics
- [Pattern Filtering](pattern-filtering.md) — precise include/exclude control
- [Export](export.md) — saving structures to files
- [Compare](compare.md) — diffing two directories
