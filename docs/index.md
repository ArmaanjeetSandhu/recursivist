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

## Key Features

<div class="feature-grid">

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M200,168a40,40,0,1,1-68.93-27.73L96,48H160l-34.93,92.29A40,40,0,0,1,200,168Z" opacity="0.2" fill="currentColor"/><path d="M200,168a40,40,0,1,1-68.93-27.73L96,48H160l-34.93,92.29A40,40,0,0,1,200,168Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="96" y1="48" x2="160" y2="48" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="108" y1="80" x2="148" y2="80" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Colorful Visualization</div>
    <div class="feature-description">Each file type is assigned a unique color for easy identification, created deterministically from file extensions for consistent visual mapping.</div>
    <a href="user-guide/visualization/" class="feature-link">See visualization <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><rect x="32" y="48" width="64" height="160" rx="8" opacity="0.2" fill="currentColor"/><rect x="96" y="120" width="64" height="88" rx="8" opacity="0.2" fill="currentColor"/><rect x="160" y="88" width="64" height="120" rx="8" opacity="0.2" fill="currentColor"/><rect x="32" y="48" width="64" height="160" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><rect x="96" y="120" width="64" height="88" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><rect x="160" y="88" width="64" height="120" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">File Statistics</div>
    <div class="feature-description">Display and sort by lines of code, file sizes, or modification times with formatting appropriate to each metric for better project understanding.</div>
    <a href="user-guide/visualization/#file-statistics" class="feature-link">File statistics <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M40,67.2V48A8,8,0,0,1,48,40H208a8,8,0,0,1,8,8V67.2a8,8,0,0,1-2.4,5.7L152,128v64l-48-16V128L42.4,72.9A8,8,0,0,1,40,67.2Z" opacity="0.2" fill="currentColor"/><path d="M40,67.2V48A8,8,0,0,1,48,40H208a8,8,0,0,1,8,8V67.2a8,8,0,0,1-2.4,5.7L152,128v64l-48-16V128L42.4,72.9A8,8,0,0,1,40,67.2Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Smart Filtering</div>
    <div class="feature-description">Powerful filtering options combining directory exclusions, extension filtering, glob patterns, regex matching, and gitignore integration for surgical precision.</div>
    <a href="user-guide/pattern-filtering/" class="feature-link">Filtering options <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><circle cx="80" cy="56" r="24" opacity="0.2" fill="currentColor"/><circle cx="80" cy="200" r="24" opacity="0.2" fill="currentColor"/><circle cx="192" cy="120" r="24" opacity="0.2" fill="currentColor"/><circle cx="80" cy="56" r="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><circle cx="80" cy="200" r="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><circle cx="192" cy="120" r="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="80" y1="80" x2="80" y2="176" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M80,80c0,52,112,48,112,40" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Gitignore Support</div>
    <div class="feature-description">Automatically respects your `.gitignore` patterns and similar ignore files to exclude files and directories you don't want to include in the visualization.</div>
    <a href="examples/advanced/#using-with-git-repositories" class="feature-link">Using with Git <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><circle cx="112" cy="112" r="80" opacity="0.2" fill="currentColor"/><circle cx="112" cy="112" r="80" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="168.57" y1="168.57" x2="224" y2="224" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Pattern Matching</div>
    <div class="feature-description">Use glob patterns for simplicity or regular expressions for complex matching needs, with options for both inclusion and exclusion patterns.</div>
    <a href="reference/pattern-matching/" class="feature-link">Pattern matching <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><polyline points="48 160 16 128 48 96" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><polyline points="208 160 240 128 208 96" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="16" y1="128" x2="240" y2="128" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Directory Comparison</div>
    <div class="feature-description">Compare two directory structures side by side with color-coded highlighting of differences for effective visual differentiation and change analysis.</div>
    <a href="user-guide/compare/" class="feature-link">Compare command <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M216,112v96a8,8,0,0,1-8,8H48a8,8,0,0,1-8-8V112a8,8,0,0,1,8-8H80" opacity="0.2" fill="currentColor"/><path d="M216,112v96a8,8,0,0,1-8,8H48a8,8,0,0,1-8-8V112a8,8,0,0,1,8-8H80" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="128" y1="24" x2="128" y2="152" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><polyline points="80 72 128 24 176 72" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Multiple Export Formats</div>
    <div class="feature-description">Export to TXT, JSON, HTML, Markdown, and React components with consistent styling across formats for documentation and integration needs.</div>
    <a href="reference/export-formats/" class="feature-link">Export formats <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><rect x="152" y="32" width="80" height="56" rx="8" opacity="0.2" fill="currentColor"/><rect x="152" y="168" width="80" height="56" rx="8" opacity="0.2" fill="currentColor"/><rect x="24" y="100" width="80" height="56" rx="8" opacity="0.2" fill="currentColor"/><rect x="152" y="32" width="80" height="56" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><rect x="152" y="168" width="80" height="56" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><rect x="24" y="100" width="80" height="56" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M104,128h24a8,8,0,0,1,8,8v52a8,8,0,0,0,8,8h8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M152,60H136a8,8,0,0,0-8,8v60" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Depth Control</div>
    <div class="feature-description">Limit directory traversal depth to focus on higher-level structure or specific layers of your project hierarchy for better visualization management.</div>
    <a href="examples/advanced/#limiting-directory-depth" class="feature-link">Depth limiting <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><rect x="32" y="48" width="192" height="160" rx="8" opacity="0.2" fill="currentColor"/><rect x="32" y="48" width="192" height="160" rx="8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><polyline points="80 96 120 128 80 160" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="136" y1="160" x2="176" y2="160" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Shell Completion</div>
    <div class="feature-description">Generate and install completion scripts for Bash, Zsh, Fish, and PowerShell to make command entry faster and easier with intelligent suggestions.</div>
    <a href="user-guide/shell-completion/" class="feature-link">Shell completion <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

</div>

## Quick Install

```bash
pip install recursivist
```

!!! info "Dependencies"
Recursivist is built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output and [Typer](https://github.com/tiangolo/typer) for an intuitive command interface.

## Getting Started

<div class="feature-grid">

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M160,40H192a8,8,0,0,1,8,8V216a8,8,0,0,1-8,8H64a8,8,0,0,1-8-8V48a8,8,0,0,1,8-8H96" opacity="0.2" fill="currentColor"/><path d="M160,40H192a8,8,0,0,1,8,8V216a8,8,0,0,1-8,8H64a8,8,0,0,1-8-8V48a8,8,0,0,1,8-8H96" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M96,40a32,32,0,0,1,64,0Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="96" y1="136" x2="160" y2="136" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="96" y1="168" x2="160" y2="168" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="96" y1="104" x2="128" y2="104" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Installation</div>
    <div class="feature-description">Follow our easy installation guide to get up and running in minutes with pip or from source.</div>
    <a href="getting-started/installation/" class="feature-link">Installation guide <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M82.34,114.34,56,120l-24-24,40-16Z" opacity="0.2" fill="currentColor"/><path d="M141.66,173.66,136,200l-24-24,5.66-26.34Z" opacity="0.2" fill="currentColor"/><path d="M200,24C160,24,128,88,128,88L168,128s64-32,64-72A32,32,0,0,0,200,24Z" opacity="0.2" fill="currentColor"/><path d="M82.34,114.34,56,120l-24-24,40-16Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M141.66,173.66,136,200l-24-24,5.66-26.34Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M200,24C160,24,128,88,128,88L168,128s64-32,64-72A32,32,0,0,0,200,24Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="40" y1="216" x2="88" y2="168" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M80,160c0,0-32,8-48,48,40-16,48-48,48-48Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Quick Start</div>
    <div class="feature-description">Jump in with basic commands and examples to visualize, export, and compare directory structures.</div>
    <a href="getting-started/quick-start/" class="feature-link">Quick start guide <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

</div>

!!! tip "Shell Completion"
Recursivist supports shell completion for easier command entry. See the [shell completion guide](user-guide/shell-completion.md) for instructions.

## Next Steps

<div class="feature-grid">

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M128,88a32,32,0,0,1,32-32h72V200H160a32,32,0,0,0-32,32Z" opacity="0.2" fill="currentColor"/><path d="M128,88a32,32,0,0,0-32-32H24V200H96a32,32,0,0,1,32,32Z" opacity="0.2" fill="currentColor"/><path d="M128,88a32,32,0,0,1,32-32h72V200H160a32,32,0,0,0-32,32Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M128,88a32,32,0,0,0-32-32H24V200H96a32,32,0,0,1,32,32Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="128" y1="88" x2="128" y2="232" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">CLI Reference</div>
    <div class="feature-description">Complete reference for all commands, options, and arguments available in Recursivist with detailed explanations.</div>
    <a href="reference/cli-reference/" class="feature-link">View CLI Reference <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><path d="M218.87,75.06A72,72,0,0,1,96,144L40.28,199.75a20,20,0,0,0,28.28,28.28L124.31,172A72,72,0,0,1,218.87,75.06Z" opacity="0.2" fill="currentColor"/><path d="M218.87,75.06A72,72,0,0,1,96,144L40.28,199.75a20,20,0,0,0,28.28,28.28L124.31,172A72,72,0,0,1,218.87,75.06Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M165.07,110.46l-27.1-62.43a8,8,0,0,1,3.63-10.11l27.71-14.3a8,8,0,0,1,11.1,4l12,36Z" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Examples</div>
    <div class="feature-description">Practical examples showing how to use Recursivist effectively for various scenarios and project types.</div>
    <a href="examples/basic/" class="feature-link">Explore Examples <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

  <div class="feature-card">
    <div class="feature-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" aria-hidden="true"><rect width="256" height="256" fill="none"/><circle cx="64" cy="200" r="24" opacity="0.2" fill="currentColor"/><circle cx="64" cy="56" r="24" opacity="0.2" fill="currentColor"/><circle cx="192" cy="200" r="24" opacity="0.2" fill="currentColor"/><circle cx="64" cy="200" r="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><circle cx="64" cy="56" r="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><circle cx="192" cy="200" r="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><line x1="64" y1="80" x2="64" y2="176" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><path d="M192,176V128a48,48,0,0,0-48-48H120" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/><polyline points="96 104 120 80 96 56" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="16"/></svg>
    </div>
    <div class="feature-title">Contributing</div>
    <div class="feature-description">Guidelines for contributing to the project, including development setup, coding standards, and testing procedures.</div>
    <a href="contributing/" class="feature-link">Contribution Guide <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>

</div>

## License

<div class="command-example">
  <div class="command-example-body">
    This project is licensed under the MIT License.
  </div>
</div>
