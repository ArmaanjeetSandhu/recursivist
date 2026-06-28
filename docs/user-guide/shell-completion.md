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

The `completion` command prints a short activation snippet for a named shell that you can add to your shell startup file:

```bash
recursivist completion SHELL
```

where `SHELL` is `bash`, `zsh`, `fish`, or `powershell`. For example, `recursivist completion bash` prints a line of the form:

```bash
eval "$(recursivist --completion-script bash)"
```

Add the printed line to the relevant startup file so completion loads in every new session:

| Shell      | Startup file                 |
| ---------- | ---------------------------- |
| Bash       | `~/.bashrc`                  |
| Zsh        | `~/.zshrc`                   |
| Fish       | `~/.config/fish/config.fish` |
| PowerShell | the file at `$PROFILE`       |

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
