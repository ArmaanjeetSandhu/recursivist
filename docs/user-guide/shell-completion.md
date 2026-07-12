# Shell Completion

Recursivist supports tab completion for Bash, Zsh, Fish, and PowerShell. Once enabled, pressing `Tab` completes commands, options, and path arguments.

## Recommended: Built-in Installer

Recursivist is built with Typer, which provides two top-level options for completion:

```bash
# Install completion for the shell you're currently using
recursivist --install-completion

# Print the completion script for your current shell (to inspect or redirect)
recursivist --show-completion
```

`--install-completion` detects your shell, writes the appropriate completion script, and wires it into your shell configuration. Restart your shell (or open a new terminal) afterwards for it to take effect. This is the simplest and most reliable way to enable completion.

## The `completion` Command

The `completion` command prints the completion **script** for a named shell to standard output, so you can save it wherever that shell loads completions from. Unlike `--show-completion`, it takes the shell name explicitly rather than detecting the current one, which is useful for generating a script for a shell other than the one you're in:

```bash
recursivist completion SHELL
```

where `SHELL` is `bash`, `zsh`, `fish`, or `powershell`. Only the script is written to stdout; a short usage hint is written to stderr, so redirecting stdout to a file captures the script by itself.

Save the printed script to the location your shell reads completions from, then restart your shell (or open a new terminal):

| Shell      | Install the printed script                                                  |
| ---------- | --------------------------------------------------------------------------- |
| Bash       | `recursivist completion bash >> ~/.bashrc`                                  |
| Zsh        | `recursivist completion zsh > ~/.zfunc/_recursivist` (see note below)       |
| Fish       | `recursivist completion fish > ~/.config/fish/completions/recursivist.fish` |
| PowerShell | `recursivist completion powershell >> $PROFILE`                             |

For Zsh, the target directory must be on your `fpath` and `compinit` must run. If you don't already have a completions directory set up, add this to `~/.zshrc` before any `compinit` call:

```zsh
fpath=(~/.zfunc $fpath)
autoload -U compinit; compinit
```

then create the directory and write the script:

```zsh
mkdir -p ~/.zfunc
recursivist completion zsh > ~/.zfunc/_recursivist
```

> **Tip:** If you only need completion for your current shell, `recursivist --install-completion` generates the script and places it correctly in one step.

## Using Completion

Once set up, completion works throughout the CLI:

```text
recursivist [Tab]              # lists visualize, export, compare, config, ...
recursivist visualize --[Tab]  # lists --exclude, --depth, --sort-by-loc, ...
recursivist visualize ~/pro[Tab]  # completes the path
```

## Troubleshooting

If completion doesn't activate:

1. Make sure you restarted the shell (or opened a new terminal) after installing.
2. Confirm your shell's completion system is enabled. For Zsh, that means `compinit` is loaded:

   ```zsh
   autoload -U compinit; compinit
   ```

3. Re-run `recursivist --install-completion` and check for any reported errors.
