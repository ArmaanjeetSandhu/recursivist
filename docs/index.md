# Recursivist

<div class="hero-section">
  <p class="hero-subtitle">A beautiful command-line tool for visualizing directory structures with rich formatting, color-coding, and multiple export options.</p>
  
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
      <span class="terminal-command">recursivist visualize</span>
    </div>
    <div style="height: 6px;"></div>
    <div class="terminal-output">
      <pre>📂 my-project
├── 📁 src
│   ├── 📄 <span style="color: #83e43d;">main.py</span>
│   ├── 📄 <span style="color: #83e43d;">utils.py</span>
│   └── 📁 tests
│       ├── 📄 <span style="color: #83e43d;">test_main.py</span>
│       └── 📄 <span style="color: #83e43d;">test_utils.py</span>
├── 📄 <span style="color: #f1fa8c;">README.md</span>
├── 📄 <span style="color: #bd93f9;">requirements.txt</span>
└── 📄 <span style="color: #83e43d;">setup.py</span></pre>
    </div>
  </div>
</div>

## ✨ Key Features

<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">🎨</div>
    <div class="feature-title">Colorful Visualization</div>
    <div class="feature-description">Each file type is assigned a unique color for easy identification. Customize your color schemes for different file types.</div>
    <a href="user-guide/visualization/" class="feature-link">See visualization <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🌳</div>
    <div class="feature-title">Tree Structure</div>
    <div class="feature-description">Displays your directories in an intuitive, hierarchical tree format. Clear visualization of complex directory structures.</div>
    <a href="user-guide/basic-usage/" class="feature-link">Basic usage <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📁</div>
    <div class="feature-title">Smart Filtering</div>
    <div class="feature-description">Easily exclude directories and file extensions you don't want to see. Focus on what matters most in your project.</div>
    <a href="user-guide/pattern-filtering/" class="feature-link">Filtering options <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🧩</div>
    <div class="feature-title">Gitignore Support</div>
    <div class="feature-description">Automatically respects your `.gitignore` patterns to exclude files you don't want in version control.</div>
    <a href="examples/advanced/#using-with-git-repositories" class="feature-link">Using with Git <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔍</div>
    <div class="feature-title">Pattern Matching</div>
    <div class="feature-description">Use glob and regex patterns to precisely include or exclude files based on your specific requirements.</div>
    <a href="reference/pattern-matching/" class="feature-link">Pattern matching <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔄</div>
    <div class="feature-title">Directory Comparison</div>
    <div class="feature-description">Compare two directory structures side by side with highlighted differences to spot changes easily.</div>
    <a href="user-guide/compare/" class="feature-link">Compare command <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">📊</div>
    <div class="feature-title">Multiple Export Formats</div>
    <div class="feature-description">Export to TXT, JSON, HTML, Markdown, and React components for integration into documentation or applications.</div>
    <a href="reference/export-formats/" class="feature-link">Export formats <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔎</div>
    <div class="feature-title">Depth Control</div>
    <div class="feature-description">Limit the display depth to focus on higher-level structure and avoid overwhelming output for large directories.</div>
    <a href="examples/advanced/#limiting-directory-depth" class="feature-link">Depth limiting <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
</div>

## 🚀 Quick Install

```bash
pip install recursivist
```

!!! info "Dependencies"
Recursivist is built with [Rich](https://github.com/Textualize/rich) and [Typer](https://github.com/tiangolo/typer) for beautiful terminal output and an intuitive command interface.

## 🏁 Getting Started

<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">📋</div>
    <div class="feature-title">Installation</div>
    <div class="feature-description">Follow our easy installation guide to get up and running in minutes.</div>
    <a href="getting-started/installation/" class="feature-link">Installation guide <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🚀</div>
    <div class="feature-title">Quick Start</div>
    <div class="feature-description">Check out the quick start guide for an overview of basic usage patterns.</div>
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
    <div class="feature-description">Complete reference for all commands and options available in Recursivist.</div>
    <a href="reference/cli-reference/" class="feature-link">View CLI Reference <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔧</div>
    <div class="feature-title">Examples</div>
    <div class="feature-description">Practical examples to help you make the most of Recursivist in your projects.</div>
    <a href="examples/basic/" class="feature-link">Explore Examples <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔄</div>
    <div class="feature-title">Contributing</div>
    <div class="feature-description">Guidelines for contributing to the project and helping it grow.</div>
    <a href="contributing/" class="feature-link">Contribution Guide <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
  </div>
</div>

## 📜 License

<div class="command-example">
  <div class="command-example-body">
    This project is licensed under the MIT License.
  </div>
</div>
