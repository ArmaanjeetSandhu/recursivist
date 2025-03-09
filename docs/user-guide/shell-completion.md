# Shell Completion

Recursivist supports shell completion for easier command entry. This guide explains how to set up and use shell completion for different shells.

## What is Shell Completion?

Shell completion allows you to press the `Tab` key while typing a command to:

- Complete command names, options, and arguments
- See available options and subcommands
- Auto-complete file and directory paths

This makes Recursivist faster and easier to use from the command line.

## Generating Completion Scripts

Recursivist can generate shell completion scripts for different shells:

- Bash
- Zsh
- Fish
- PowerShell

Use the `completion` command to generate the appropriate script:

```bash
recursivist completion SHELL
```

Replace `SHELL` with one of: `bash`, `zsh`, `fish`, or `powershell`.

## Setting Up Completion for Different Shells

### Bash

```bash
# Create the completions directory if it doesn't exist
mkdir -p ~/.bash_completion.d

# Generate and save the completion script
recursivist completion bash > ~/.bash_completion.d/recursivist

# Add to .bashrc to load on startup
echo 'source ~/.bash_completion.d/recursivist' >> ~/.bashrc

# Load the completion in the current session
source ~/.bash_completion.d/recursivist
```

### Zsh

```zsh
# Create the completions directory if it doesn't exist
mkdir -p ~/.zsh/completion

# Generate and save the completion script
recursivist completion zsh > ~/.zsh/completion/_recursivist

# Add to .zshrc to load on startup (if not already configured)
echo 'fpath=(~/.zsh/completion $fpath)' >> ~/.zshrc
echo 'autoload -U compinit; compinit' >> ~/.zshrc

# Load the completion in the current session
fpath=(~/.zsh/completion $fpath)
autoload -U compinit; compinit
```

### Fish

```fish
# Create the completions directory if it doesn't exist
mkdir -p ~/.config/fish/completions

# Generate and save the completion script
recursivist completion fish > ~/.config/fish/completions/recursivist.fish

# Completions will be loaded automatically the next time you start fish
# To load them immediately:
source ~/.config/fish/completions/recursivist.fish
```

### PowerShell

```powershell
# Generate the completion script
recursivist completion powershell > recursivist.ps1

# Create a profile if it doesn't exist (check first)
if (!(Test-Path -Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}

# Add the completion script to your profile
Add-Content -Path $PROFILE -Value ". $(pwd)\recursivist.ps1"

# Load the completion in the current session
. .\recursivist.ps1
```

## Using Shell Completion

Once set up, you can use tab completion with Recursivist commands:

1. Type a partial command and press `Tab` to complete it:

   ```
   recursis[Tab]  # completes to "recursivist"
   ```

2. Type a command and press `Tab` to see available subcommands:

   ```
   recursivist [Tab]  # shows visualize, export, compare, etc.
   ```

3. Type a subcommand and press `Tab` to see available options:

   ```
   recursivist visualize --[Tab]  # shows --exclude, --depth, etc.
   ```

4. Type a path argument and press `Tab` to complete the path:
   ```
   recursivist visualize ~/pro[Tab]  # completes to "~/projects/"
   ```

## Completion Features

Recursivist's completion system provides:

- Command and subcommand completion
- Option name completion (both long and short forms)
- Option value completion for some options
- File and directory path completion
- Contextual help for available options

## Troubleshooting

If shell completion isn't working:

1. Make sure you've sourced the completion script correctly
2. Verify that your shell's completion system is enabled
3. Try restarting your shell session
4. Check for error messages when loading the completion script

### Common Issues

#### Permission Denied

If you get a "permission denied" error when generating the completion script:

```bash
# Make sure you have write permission to the target directory
chmod +w ~/.bash_completion.d

# Or use sudo to generate the script (system-wide)
sudo recursivist completion bash > /etc/bash_completion.d/recursivist
```

#### Completion Not Working

If completion doesn't work even after setting up:

```bash
# Make sure the script is executable
chmod +x ~/.bash_completion.d/recursivist

# Try sourcing it explicitly
source ~/.bash_completion.d/recursivist

# Check for errors in the script
cat ~/.bash_completion.d/recursivist
```

#### Zsh Insecure Directories Warning

If you see a warning about insecure directories in Zsh:

```zsh
# Fix directory permissions
chmod 755 ~/.zsh
chmod 755 ~/.zsh/completion
```

## System-Wide Installation

For system-wide installation (requires admin privileges):

### Bash (Ubuntu/Debian)

```bash
sudo recursivist completion bash > /etc/bash_completion.d/recursivist
```

### Bash (RHEL/CentOS/Fedora)

```bash
sudo recursivist completion bash > /etc/bash_completion.d/recursivist
```

### Zsh

```bash
sudo recursivist completion zsh > /usr/local/share/zsh/site-functions/_recursivist
```

### Fish

```bash
sudo recursivist completion fish > /usr/share/fish/vendor_completions.d/recursivist.fish
```

## Command Completion Options

The tab completion for Recursivist is particularly helpful for:

### Complex Options

```bash
# Tab completion suggests available options
recursivist visualize --sort-by-[Tab]
# Shows: --sort-by-loc --sort-by-size --sort-by-mtime
```

### Format Selection

```bash
# Tab completion suggests available formats
recursivist export --format [Tab]
# Shows: txt json html md jsx
```

### Shell Selection

```bash
# Tab completion suggests available shells
recursivist completion [Tab]
# Shows: bash zsh fish powershell
```

This makes it much easier to use Recursivist's more advanced features without needing to remember all the available options.
