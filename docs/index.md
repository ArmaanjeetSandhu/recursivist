# Recursivist

<div class="hero-section">
  <p class="hero-subtitle">A powerful command-line tool for visualizing directory structures with rich formatting, color-coding, and comprehensive analysis options.</p>
  
  <div class="hero-buttons">
    <a href="getting-started/installation/" class="md-button md-button--primary">Get Started</a>
    <a href="examples/basic/" class="md-button md-button--secondary">View Examples</a>
  </div>
</div>

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
    <div class="terminal-line">
      <span class="terminal-prompt">$</span>
      <span class="terminal-command">recursivist visualize --sort-by-loc</span>
    </div>
    <div style="height: 6px;"></div>
    <div class="terminal-output">
      <pre>📂 my-project (1262 lines)
├── 📁 src (1055 lines)
│   ├── 📄 <span style="color: #83e43d;">main.py</span> (245 lines)
│   ├── 📄 <span style="color: #83e43d;">utils.py</span> (157 lines)
│   └── 📁 tests (653 lines)
│       ├── 📄 <span style="color: #83e43d;">test_main.py</span> (412 lines)
│       └── 📄 <span style="color: #83e43d;">test_utils.py</span> (241 lines)
├── 📄 <span style="color: #f1fa8c;">README.md</span> (124 lines)
├── 📄 <span style="color: #bd93f9;">requirements.txt</span> (18 lines)
└── 📄 <span style="color: #83e43d;">setup.py</span> (65 lines)</pre>
    </div>
  </div>
</div>

## ✨ Key Features

<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">🎨</div>
    <div class="feature-title">Colorful Visualization</div>
    <div class="feature-description">Each file type is assigned a unique color for easy identification, created deterministically from file extensions for consistent visual mapping.</div>
    <a href="user-guide/visualization/" class="feature-link">See visualization <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📊</div>
    <div class="feature-title">File Statistics</div>
    <div class="feature-description">Display and sort by lines of code, file sizes, or modification times with formatting appropriate to each metric for better project understanding.</div>
    <a href="user-guide/visualization/#file-statistics" class="feature-link">File statistics <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📁</div>
    <div class="feature-title">Smart Filtering</div>
    <div class="feature-description">Powerful filtering options combining directory exclusions, extension filtering, glob patterns, regex matching, and gitignore integration for surgical precision.</div>
    <a href="user-guide/pattern-filtering/" class="feature-link">Filtering options <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🧩</div>
    <div class="feature-title">Gitignore Support</div>
    <div class="feature-description">Automatically respects your `.gitignore` patterns and similar ignore files to exclude files and directories you don't want to include in the visualization.</div>
    <a href="examples/advanced/#using-with-git-repositories" class="feature-link">Using with Git <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔍</div>
    <div class="feature-title">Pattern Matching</div>
    <div class="feature-description">Use glob patterns for simplicity or regular expressions for complex matching needs, with options for both inclusion and exclusion patterns.</div>
    <a href="reference/pattern-matching/" class="feature-link">Pattern matching <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔄</div>
    <div class="feature-title">Directory Comparison</div>
    <div class="feature-description">Compare two directory structures side by side with color-coded highlighting of differences for effective visual differentiation and change analysis.</div>
    <a href="user-guide/compare/" class="feature-link">Compare command <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📤</div>
    <div class="feature-title">Multiple Export Formats</div>
    <div class="feature-description">Export to TXT, JSON, HTML, Markdown, and React components with consistent styling across formats for documentation and integration needs.</div>
    <a href="reference/export-formats/" class="feature-link">Export formats <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔎</div>
    <div class="feature-title">Depth Control</div>
    <div class="feature-description">Limit directory traversal depth to focus on higher-level structure or specific layers of your project hierarchy for better visualization management.</div>
    <a href="examples/advanced/#limiting-directory-depth" class="feature-link">Depth limiting <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">💻</div>
    <div class="feature-title">Shell Completion</div>
    <div class="feature-description">Generate and install completion scripts for Bash, Zsh, Fish, and PowerShell to make command entry faster and easier with intelligent suggestions.</div>
    <a href="user-guide/shell-completion/" class="feature-link">Shell completion <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
</div>

## 🚀 Quick Install

```bash
pip install recursivist
```

!!! info "Dependencies"
Recursivist is built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output and [Typer](https://github.com/tiangolo/typer) for an intuitive command interface.

## 🏁 Getting Started

<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">📋</div>
    <div class="feature-title">Installation</div>
    <div class="feature-description">Follow our easy installation guide to get up and running in minutes with pip or from source.</div>
    <a href="getting-started/installation/" class="feature-link">Installation guide <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🚀</div>
    <div class="feature-title">Quick Start</div>
    <div class="feature-description">Jump in with basic commands and examples to visualize, export, and compare directory structures.</div>
    <a href="getting-started/quick-start/" class="feature-link">Quick start guide <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
</div>

!!! tip "Shell Completion"
Recursivist supports shell completion for easier command entry. See the [shell completion guide](user-guide/shell-completion.md) for instructions.

## 📚 Next Steps

<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">📋</div>
    <div class="feature-title">CLI Reference</div>
    <div class="feature-description">Complete reference for all commands, options, and arguments available in Recursivist with detailed explanations.</div>
    <a href="reference/cli-reference/" class="feature-link">View CLI Reference <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔧</div>
    <div class="feature-title">Examples</div>
    <div class="feature-description">Practical examples showing how to use Recursivist effectively for various scenarios and project types.</div>
    <a href="examples/basic/" class="feature-link">Explore Examples <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔄</div>
    <div class="feature-title">Contributing</div>
    <div class="feature-description">Guidelines for contributing to the project, including development setup, coding standards, and testing procedures.</div>
    <a href="contributing/" class="feature-link">Contribution Guide <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
</div>

## 📜 License

<div class="command-example">
  <div class="command-example-body">
    This project is licensed under the MIT License.
  </div>
</div>
