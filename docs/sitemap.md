# Sitemap

<link
  rel="stylesheet"
  href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/duotone/style.css"
/>

<div class="mm-controls">
  <button
    class="mm-btn mm-icon-btn"
    id="mm-expcol-toggle"
    title="Collapse All"
  >
    <i class="ph-duotone ph-arrows-in" id="mm-expcol-icon"></i>
  </button>

  <button class="mm-btn mm-icon-btn" id="mm-reset-view" title="Reset View">
    <i class="ph-duotone ph-arrows-counter-clockwise"></i>
  </button>

<button
class="mm-btn mm-orient-btn"
id="mm-orient-toggle"
title="Switch to Top → Bottom"

>

    <span id="mm-icons-lr" style="display: none">
      <i class="ph-duotone ph-arrow-circle-left"></i>
      <i class="ph-duotone ph-arrow-circle-right"></i>
    </span>

    <span id="mm-icons-tb">
      <i class="ph-duotone ph-arrow-circle-up"></i>
      <i class="ph-duotone ph-arrow-circle-down"></i>
    </span>

  </button>
</div>

<div
  id="mm-root"
  style="position: fixed; inset: 0; pointer-events: none; z-index: 9999; overflow: visible"
>
  <svg
    id="mm-svg"
    xmlns="http://www.w3.org/2000/svg"
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: visible"
  ></svg>
</div>

<style>
  .mm-controls i[class*="ph-"] {
    font-size: 1rem;
    line-height: 1;
    display: inline-flex;
    align-items: center;
  }

  .mm-controls {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin: 1rem 0;
    position: relative;
    z-index: 10000;
  }

  .mm-btn {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    border-radius: 8px;
    cursor: pointer;
    border: 1px solid transparent;
    background: transparent;
    color: var(--md-typeset-color, #1a1a1a);
    transition: background 0.15s ease, border-color 0.15s ease,
      transform 0.1s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    line-height: 1;
  }

  .mm-btn:hover {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.3);
    transform: translateY(-1px);
  }

  .mm-btn:active {
    transform: scale(0.96);
  }

  [data-md-color-scheme="slate"] .mm-btn {
    color: rgba(255, 255, 255, 0.85);
  }

  [data-md-color-scheme="slate"] .mm-btn:hover {
    background: rgba(34, 197, 94, 0.12);
    border-color: rgba(34, 197, 94, 0.35);
  }

  .mm-icon-btn {
    padding: 5px 6px;
  }

  .mm-orient-btn {
    padding: 5px 8px;
    gap: 3px;
  }

  .mm-orient-btn span {
    display: inline-flex;
    align-items: center;
    gap: 2px;
  }

  .mm-divider {
    width: 1px;
    height: 16px;
    background: var(--border, rgba(0, 0, 0, 0.1));
    margin: 0 2px;
    flex-shrink: 0;
  }

  [data-md-color-scheme="slate"] .mm-divider {
    background: rgba(255, 255, 255, 0.1);
  }

  .mm-node-g {
    cursor: grab;
    pointer-events: all;
  }

  .mm-node-g:active {
    cursor: grabbing;
  }

  .mm-pill {
    transition: filter 0.15s ease;
  }

  .mm-node-g:hover .mm-pill {
    filter: brightness(1.08)
      drop-shadow(0 4px 12px rgba(0, 0, 0, 0.35));
  }

  .mm-label {
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 600;
    fill: #fff;
    dominant-baseline: middle;
    text-anchor: middle;
    pointer-events: none;
    user-select: none;
  }

  .mm-toggle-g {
    cursor: pointer;
    pointer-events: all;
  }

  .mm-toggle-g circle {
    fill: rgba(0, 0, 0, 0.32);
    stroke: rgba(255, 255, 255, 0.75);
    stroke-width: 1.5;
    transition: fill 0.12s;
  }

  .mm-toggle-g:hover circle {
    fill: rgba(0, 0, 0, 0.52);
  }

  .mm-toggle-g text {
    fill: #fff;
    font-size: 11px;
    font-weight: 700;
    dominant-baseline: middle;
    text-anchor: middle;
    pointer-events: none;
    user-select: none;
  }

  [data-md-color-scheme="slate"] .mm-toggle-g circle {
    fill: rgba(0, 0, 0, 0.45);
    stroke: rgba(255, 255, 255, 0.6);
  }

  [data-md-color-scheme="slate"] .mm-toggle-g:hover circle {
    fill: rgba(0, 0, 0, 0.65);
  }

  .mm-edge {
    fill: none;
    stroke-linecap: round;
  }
</style>

<script>
  (function () {
    const TREE = {
  "id": "root",
  "label": "Recursivist",
  "children": [
    {
      "id": "home",
      "label": "Home",
      "children": [
        {
          "id": "recursivist",
          "label": "Recursivist",
          "children": [
            {
              "id": "key-features",
              "label": "Key Features"
            },
            {
              "id": "quick-install",
              "label": "Quick Install"
            },
            {
              "id": "getting-started",
              "label": "Getting Started"
            },
            {
              "id": "next-steps",
              "label": "Next Steps"
            },
            {
              "id": "license",
              "label": "License"
            }
          ]
        }
      ]
    },
    {
      "id": "getting-started",
      "label": "Getting Started",
      "children": [
        {
          "id": "installation",
          "label": "Installation",
          "children": [
            {
              "id": "installation",
              "label": "Installation",
              "children": [
                {
                  "id": "requirements",
                  "label": "Requirements"
                },
                {
                  "id": "installing-from-pypi",
                  "label": "Installing from PyPI"
                },
                {
                  "id": "installing-from-source",
                  "label": "Installing from Source"
                },
                {
                  "id": "installing-for-development",
                  "label": "Installing for Development"
                },
                {
                  "id": "verifying-installation",
                  "label": "Verifying Installation"
                },
                {
                  "id": "system-specific-notes",
                  "label": "System-specific Notes",
                  "children": [
                    {
                      "id": "windows",
                      "label": "Windows"
                    },
                    {
                      "id": "macos",
                      "label": "macOS"
                    },
                    {
                      "id": "linux",
                      "label": "Linux"
                    }
                  ]
                },
                {
                  "id": "troubleshooting-installation-issues",
                  "label": "Troubleshooting Installation Issues",
                  "children": [
                    {
                      "id": "unicode-display-problems",
                      "label": "Unicode Display Problems"
                    },
                    {
                      "id": "color-display-issues",
                      "label": "Color Display Issues"
                    },
                    {
                      "id": "missing-dependencies",
                      "label": "Missing Dependencies"
                    }
                  ]
                },
                {
                  "id": "next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        },
        {
          "id": "quick-start",
          "label": "Quick Start",
          "children": [
            {
              "id": "quick-start-guide",
              "label": "Quick Start Guide",
              "children": [
                {
                  "id": "basic-commands",
                  "label": "Basic Commands",
                  "children": [
                    {
                      "id": "visualize-a-directory",
                      "label": "Visualize a Directory"
                    },
                    {
                      "id": "display-file-statistics",
                      "label": "Display File Statistics"
                    },
                    {
                      "id": "export-a-directory-structure",
                      "label": "Export a Directory Structure"
                    },
                    {
                      "id": "compare-two-directories",
                      "label": "Compare Two Directories"
                    }
                  ]
                },
                {
                  "id": "common-options",
                  "label": "Common Options",
                  "children": [
                    {
                      "id": "exclude-directories",
                      "label": "Exclude Directories"
                    },
                    {
                      "id": "exclude-file-extensions",
                      "label": "Exclude File Extensions"
                    },
                    {
                      "id": "pattern-filtering",
                      "label": "Pattern Filtering"
                    },
                    {
                      "id": "limit-directory-depth",
                      "label": "Limit Directory Depth"
                    },
                    {
                      "id": "show-full-paths",
                      "label": "Show Full Paths"
                    }
                  ]
                },
                {
                  "id": "quick-examples",
                  "label": "Quick Examples",
                  "children": [
                    {
                      "id": "basic-directory-visualization",
                      "label": "Basic Directory Visualization"
                    },
                    {
                      "id": "visualizing-with-file-statistics",
                      "label": "Visualizing with File Statistics"
                    },
                    {
                      "id": "export-to-multiple-formats",
                      "label": "Export to Multiple Formats"
                    },
                    {
                      "id": "compare-with-exclusions",
                      "label": "Compare with Exclusions"
                    },
                    {
                      "id": "compare-with-file-statistics",
                      "label": "Compare with File Statistics"
                    }
                  ]
                },
                {
                  "id": "shell-completion",
                  "label": "Shell Completion"
                },
                {
                  "id": "next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "user-guide",
      "label": "User Guide",
      "children": [
        {
          "id": "basic-usage",
          "label": "Basic Usage",
          "children": [
            {
              "id": "basic-usage",
              "label": "Basic Usage",
              "children": [
                {
                  "id": "command-structure",
                  "label": "Command Structure"
                },
                {
                  "id": "basic-commands",
                  "label": "Basic Commands",
                  "children": [
                    {
                      "id": "checking-version",
                      "label": "Checking Version"
                    },
                    {
                      "id": "visualizing-the-current-directory",
                      "label": "Visualizing the Current Directory"
                    },
                    {
                      "id": "visualizing-a-specific-directory",
                      "label": "Visualizing a Specific Directory"
                    },
                    {
                      "id": "visualizing-with-file-statistics",
                      "label": "Visualizing with File Statistics"
                    },
                    {
                      "id": "getting-help",
                      "label": "Getting Help"
                    }
                  ]
                },
                {
                  "id": "default-behavior",
                  "label": "Default Behavior"
                },
                {
                  "id": "common-options",
                  "label": "Common Options",
                  "children": [
                    {
                      "id": "excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "limiting-depth",
                      "label": "Limiting Depth"
                    },
                    {
                      "id": "showing-full-paths",
                      "label": "Showing Full Paths"
                    },
                    {
                      "id": "using-verbose-mode",
                      "label": "Using Verbose Mode"
                    }
                  ]
                },
                {
                  "id": "pattern-filtering",
                  "label": "Pattern Filtering",
                  "children": [
                    {
                      "id": "glob-patterns-(default)",
                      "label": "Glob Patterns (Default)"
                    },
                    {
                      "id": "regular-expressions",
                      "label": "Regular Expressions"
                    },
                    {
                      "id": "include-patterns-(override-exclusions)",
                      "label": "Include Patterns (Override Exclusions)"
                    },
                    {
                      "id": "gitignore-integration",
                      "label": "Gitignore Integration"
                    }
                  ]
                },
                {
                  "id": "export-formats",
                  "label": "Export Formats"
                },
                {
                  "id": "directory-comparison",
                  "label": "Directory Comparison"
                },
                {
                  "id": "shell-completion",
                  "label": "Shell Completion"
                },
                {
                  "id": "exit-codes",
                  "label": "Exit Codes"
                },
                {
                  "id": "next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        },
        {
          "id": "visualization",
          "label": "Visualization",
          "children": [
            {
              "id": "visualization",
              "label": "Visualization",
              "children": [
                {
                  "id": "basic-visualization",
                  "label": "Basic Visualization"
                },
                {
                  "id": "customizing-the-visualization",
                  "label": "Customizing the Visualization",
                  "children": [
                    {
                      "id": "color-coding",
                      "label": "Color Coding"
                    },
                    {
                      "id": "file-statistics",
                      "label": "File Statistics",
                      "children": [
                        {
                          "id": "lines-of-code",
                          "label": "Lines of Code"
                        },
                        {
                          "id": "file-sizes",
                          "label": "File Sizes"
                        },
                        {
                          "id": "modification-times",
                          "label": "Modification Times"
                        },
                        {
                          "id": "combining-statistics",
                          "label": "Combining Statistics"
                        }
                      ]
                    },
                    {
                      "id": "directory-depth-control",
                      "label": "Directory Depth Control"
                    },
                    {
                      "id": "full-path-display",
                      "label": "Full Path Display"
                    }
                  ]
                },
                {
                  "id": "filtering-the-visualization",
                  "label": "Filtering the Visualization",
                  "children": [
                    {
                      "id": "excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "pattern-based-filtering",
                      "label": "Pattern-Based Filtering"
                    },
                    {
                      "id": "using-gitignore-files",
                      "label": "Using Gitignore Files"
                    }
                  ]
                },
                {
                  "id": "output-example",
                  "label": "Output Example"
                },
                {
                  "id": "verbose-mode",
                  "label": "Verbose Mode"
                },
                {
                  "id": "terminal-compatibility",
                  "label": "Terminal Compatibility"
                },
                {
                  "id": "performance-tips",
                  "label": "Performance Tips"
                },
                {
                  "id": "related-commands",
                  "label": "Related Commands"
                }
              ]
            }
          ]
        },
        {
          "id": "export",
          "label": "Export",
          "children": [
            {
              "id": "export",
              "label": "Export",
              "children": [
                {
                  "id": "basic-export-usage",
                  "label": "Basic Export Usage"
                },
                {
                  "id": "available-export-formats",
                  "label": "Available Export Formats"
                },
                {
                  "id": "exporting-to-multiple-formats",
                  "label": "Exporting to Multiple Formats"
                },
                {
                  "id": "output-directory",
                  "label": "Output Directory"
                },
                {
                  "id": "customizing-filenames",
                  "label": "Customizing Filenames"
                },
                {
                  "id": "including-file-statistics",
                  "label": "Including File Statistics"
                },
                {
                  "id": "filtering-exports",
                  "label": "Filtering Exports"
                },
                {
                  "id": "depth-control",
                  "label": "Depth Control"
                },
                {
                  "id": "full-path-display",
                  "label": "Full Path Display"
                },
                {
                  "id": "format-specific-features",
                  "label": "Format-Specific Features",
                  "children": [
                    {
                      "id": "text-format-(.txt)",
                      "label": "Text Format (.txt)"
                    },
                    {
                      "id": "json-format-(.json)",
                      "label": "JSON Format (.json)"
                    },
                    {
                      "id": "html-format-(.html)",
                      "label": "HTML Format (.html)"
                    },
                    {
                      "id": "markdown-format-(.md)",
                      "label": "Markdown Format (.md)"
                    },
                    {
                      "id": "react-component-(.jsx)",
                      "label": "React Component (.jsx)"
                    },
                    {
                      "id": "svg-format-(.svg)",
                      "label": "SVG Format (.svg)"
                    }
                  ]
                },
                {
                  "id": "using-the-react-component",
                  "label": "Using the React Component"
                },
                {
                  "id": "examples",
                  "label": "Examples",
                  "children": [
                    {
                      "id": "basic-export-to-markdown",
                      "label": "Basic Export to Markdown"
                    },
                    {
                      "id": "export-to-multiple-formats-with-custom-prefix",
                      "label": "Export to Multiple Formats with Custom Prefix"
                    },
                    {
                      "id": "export-source-directory-only",
                      "label": "Export Source Directory Only"
                    },
                    {
                      "id": "export-with-depth-control-and-exclusions",
                      "label": "Export with Depth Control and Exclusions"
                    },
                    {
                      "id": "export-with-file-statistics",
                      "label": "Export with File Statistics"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "compare",
          "label": "Compare",
          "children": [
            {
              "id": "compare",
              "label": "Compare",
              "children": [
                {
                  "id": "basic-comparison",
                  "label": "Basic Comparison"
                },
                {
                  "id": "understanding-the-output",
                  "label": "Understanding the Output"
                },
                {
                  "id": "including-file-statistics",
                  "label": "Including File Statistics"
                },
                {
                  "id": "exporting-comparison-results",
                  "label": "Exporting Comparison Results"
                },
                {
                  "id": "filtering-the-comparison",
                  "label": "Filtering the Comparison",
                  "children": [
                    {
                      "id": "excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "pattern-based-filtering",
                      "label": "Pattern-Based Filtering"
                    },
                    {
                      "id": "using-gitignore-files",
                      "label": "Using Gitignore Files"
                    }
                  ]
                },
                {
                  "id": "depth-control",
                  "label": "Depth Control"
                },
                {
                  "id": "full-path-display",
                  "label": "Full Path Display"
                },
                {
                  "id": "use-cases",
                  "label": "Use Cases",
                  "children": [
                    {
                      "id": "project-evolution",
                      "label": "Project Evolution"
                    },
                    {
                      "id": "code-reviews",
                      "label": "Code Reviews"
                    },
                    {
                      "id": "deployment-verification",
                      "label": "Deployment Verification"
                    },
                    {
                      "id": "backup-validation",
                      "label": "Backup Validation"
                    }
                  ]
                },
                {
                  "id": "examples",
                  "label": "Examples",
                  "children": [
                    {
                      "id": "basic-comparison",
                      "label": "Basic Comparison"
                    },
                    {
                      "id": "compare-with-exclusions",
                      "label": "Compare with Exclusions"
                    },
                    {
                      "id": "compare-with-depth-limit-and-html-export",
                      "label": "Compare with Depth Limit and HTML Export"
                    },
                    {
                      "id": "compare-source-directories-only",
                      "label": "Compare Source Directories Only"
                    },
                    {
                      "id": "compare-with-file-statistics",
                      "label": "Compare with File Statistics"
                    }
                  ]
                },
                {
                  "id": "html-output-features",
                  "label": "HTML Output Features"
                },
                {
                  "id": "terminal-compatibility",
                  "label": "Terminal Compatibility"
                }
              ]
            }
          ]
        },
        {
          "id": "pattern-filtering",
          "label": "Pattern Filtering",
          "children": [
            {
              "id": "pattern-filtering",
              "label": "Pattern Filtering",
              "children": [
                {
                  "id": "basic-filtering",
                  "label": "Basic Filtering",
                  "children": [
                    {
                      "id": "excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    }
                  ]
                },
                {
                  "id": "advanced-filtering",
                  "label": "Advanced Filtering",
                  "children": [
                    {
                      "id": "using-gitignore-files",
                      "label": "Using Gitignore Files"
                    },
                    {
                      "id": "glob-pattern-filtering",
                      "label": "Glob Pattern Filtering"
                    },
                    {
                      "id": "regex-pattern-filtering",
                      "label": "Regex Pattern Filtering"
                    }
                  ]
                },
                {
                  "id": "include-patterns",
                  "label": "Include Patterns"
                },
                {
                  "id": "combining-filters",
                  "label": "Combining Filters"
                },
                {
                  "id": "filter-order-of-precedence",
                  "label": "Filter Order of Precedence"
                },
                {
                  "id": "examples",
                  "label": "Examples",
                  "children": [
                    {
                      "id": "focus-on-source-code-only",
                      "label": "Focus on Source Code Only"
                    },
                    {
                      "id": "exclude-generated-files",
                      "label": "Exclude Generated Files"
                    },
                    {
                      "id": "view-only-documentation",
                      "label": "View Only Documentation"
                    },
                    {
                      "id": "complex-filtering-with-regex",
                      "label": "Complex Filtering with Regex"
                    },
                    {
                      "id": "filtering-with-file-statistics",
                      "label": "Filtering with File Statistics"
                    }
                  ]
                },
                {
                  "id": "filtering-in-export-and-compare-commands",
                  "label": "Filtering in Export and Compare Commands"
                }
              ]
            }
          ]
        },
        {
          "id": "shell-completion",
          "label": "Shell Completion",
          "children": [
            {
              "id": "shell-completion",
              "label": "Shell Completion",
              "children": [
                {
                  "id": "what-is-shell-completion?",
                  "label": "What is Shell Completion?"
                },
                {
                  "id": "generating-completion-scripts",
                  "label": "Generating Completion Scripts"
                },
                {
                  "id": "setting-up-completion-for-different-shells",
                  "label": "Setting Up Completion for Different Shells",
                  "children": [
                    {
                      "id": "bash",
                      "label": "Bash"
                    },
                    {
                      "id": "zsh",
                      "label": "Zsh"
                    },
                    {
                      "id": "fish",
                      "label": "Fish"
                    },
                    {
                      "id": "powershell",
                      "label": "PowerShell"
                    }
                  ]
                },
                {
                  "id": "using-shell-completion",
                  "label": "Using Shell Completion"
                },
                {
                  "id": "completion-features",
                  "label": "Completion Features"
                },
                {
                  "id": "troubleshooting",
                  "label": "Troubleshooting",
                  "children": [
                    {
                      "id": "common-issues",
                      "label": "Common Issues",
                      "children": [
                        {
                          "id": "permission-denied",
                          "label": "Permission Denied"
                        },
                        {
                          "id": "completion-not-working",
                          "label": "Completion Not Working"
                        },
                        {
                          "id": "zsh-insecure-directories-warning",
                          "label": "Zsh Insecure Directories Warning"
                        }
                      ]
                    }
                  ]
                },
                {
                  "id": "system-wide-installation",
                  "label": "System-Wide Installation",
                  "children": [
                    {
                      "id": "bash-(ubuntu/debian)",
                      "label": "Bash (Ubuntu/Debian)"
                    },
                    {
                      "id": "bash-(rhel/centos/fedora)",
                      "label": "Bash (RHEL/CentOS/Fedora)"
                    },
                    {
                      "id": "zsh",
                      "label": "Zsh"
                    },
                    {
                      "id": "fish",
                      "label": "Fish"
                    }
                  ]
                },
                {
                  "id": "command-completion-options",
                  "label": "Command Completion Options",
                  "children": [
                    {
                      "id": "complex-options",
                      "label": "Complex Options"
                    },
                    {
                      "id": "format-selection",
                      "label": "Format Selection"
                    },
                    {
                      "id": "shell-selection",
                      "label": "Shell Selection"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "reference",
      "label": "Reference",
      "children": [
        {
          "id": "cli-reference",
          "label": "CLI Reference",
          "children": [
            {
              "id": "cli-reference",
              "label": "CLI Reference",
              "children": [
                {
                  "id": "command-overview",
                  "label": "Command Overview"
                },
                {
                  "id": "global-options",
                  "label": "Global Options"
                },
                {
                  "id": "visualize-command",
                  "label": "`visualize` Command",
                  "children": [
                    {
                      "id": "usage",
                      "label": "Usage"
                    },
                    {
                      "id": "arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "options",
                      "label": "Options"
                    },
                    {
                      "id": "examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "export-command",
                  "label": "`export` Command",
                  "children": [
                    {
                      "id": "usage",
                      "label": "Usage"
                    },
                    {
                      "id": "arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "options",
                      "label": "Options"
                    },
                    {
                      "id": "examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "compare-command",
                  "label": "`compare` Command",
                  "children": [
                    {
                      "id": "usage",
                      "label": "Usage"
                    },
                    {
                      "id": "arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "options",
                      "label": "Options"
                    },
                    {
                      "id": "examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "completion-command",
                  "label": "`completion` Command",
                  "children": [
                    {
                      "id": "usage",
                      "label": "Usage"
                    },
                    {
                      "id": "arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "version-command",
                  "label": "`version` Command",
                  "children": [
                    {
                      "id": "usage",
                      "label": "Usage"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "api-reference",
          "label": "API Reference",
          "children": [
            {
              "id": "api-reference",
              "label": "API Reference",
              "children": [
                {
                  "id": "core-module",
                  "label": "Core Module"
                },
                {
                  "id": "exports-module",
                  "label": "Exports Module"
                },
                {
                  "id": "compare-module",
                  "label": "Compare Module"
                },
                {
                  "id": "jsx-export-module",
                  "label": "JSX Export Module"
                },
                {
                  "id": "using-the-python-api-in-custom-scripts",
                  "label": "Using the Python API in Custom Scripts"
                },
                {
                  "id": "api-extension-points",
                  "label": "API Extension Points"
                }
              ]
            }
          ]
        },
        {
          "id": "export-formats",
          "label": "Export Formats",
          "children": [
            {
              "id": "export-formats",
              "label": "Export Formats",
              "children": [
                {
                  "id": "available-formats",
                  "label": "Available Formats"
                },
                {
                  "id": "basic-export-command",
                  "label": "Basic Export Command"
                },
                {
                  "id": "exporting-to-multiple-formats",
                  "label": "Exporting to Multiple Formats"
                },
                {
                  "id": "specifying-output-directory",
                  "label": "Specifying Output Directory"
                },
                {
                  "id": "customizing-filename-prefix",
                  "label": "Customizing Filename Prefix"
                },
                {
                  "id": "including-file-statistics",
                  "label": "Including File Statistics"
                },
                {
                  "id": "format-details",
                  "label": "Format Details",
                  "children": [
                    {
                      "id": "text-format-(txt)",
                      "label": "Text Format (TXT)"
                    },
                    {
                      "id": "json-format",
                      "label": "JSON Format"
                    },
                    {
                      "id": "html-format",
                      "label": "HTML Format"
                    },
                    {
                      "id": "markdown-format-(md)",
                      "label": "Markdown Format (MD)"
                    },
                    {
                      "id": "react-component-(jsx)",
                      "label": "React Component (JSX)"
                    },
                    {
                      "id": "svg-format",
                      "label": "SVG Format"
                    }
                  ]
                },
                {
                  "id": "using-the-react-component",
                  "label": "Using the React Component"
                },
                {
                  "id": "export-with-filtering",
                  "label": "Export with Filtering"
                },
                {
                  "id": "exporting-full-paths",
                  "label": "Exporting Full Paths"
                },
                {
                  "id": "comparison-of-export-formats",
                  "label": "Comparison of Export Formats"
                }
              ]
            }
          ]
        },
        {
          "id": "pattern-matching",
          "label": "Pattern Matching",
          "children": [
            {
              "id": "pattern-matching",
              "label": "Pattern Matching",
              "children": [
                {
                  "id": "pattern-types",
                  "label": "Pattern Types"
                },
                {
                  "id": "glob-patterns",
                  "label": "Glob Patterns",
                  "children": [
                    {
                      "id": "glob-syntax",
                      "label": "Glob Syntax"
                    },
                    {
                      "id": "glob-examples",
                      "label": "Glob Examples"
                    },
                    {
                      "id": "using-glob-patterns",
                      "label": "Using Glob Patterns"
                    }
                  ]
                },
                {
                  "id": "regular-expressions",
                  "label": "Regular Expressions",
                  "children": [
                    {
                      "id": "regex-syntax",
                      "label": "Regex Syntax"
                    },
                    {
                      "id": "regex-examples",
                      "label": "Regex Examples"
                    },
                    {
                      "id": "using-regex-patterns",
                      "label": "Using Regex Patterns"
                    }
                  ]
                },
                {
                  "id": "pattern-precedence",
                  "label": "Pattern Precedence"
                },
                {
                  "id": "combining-include-and-exclude-patterns",
                  "label": "Combining Include and Exclude Patterns"
                },
                {
                  "id": "pattern-matching-in-different-commands",
                  "label": "Pattern Matching in Different Commands"
                },
                {
                  "id": "advanced-pattern-examples",
                  "label": "Advanced Pattern Examples",
                  "children": [
                    {
                      "id": "show-only-source-code",
                      "label": "Show Only Source Code"
                    },
                    {
                      "id": "exclude-all-test-files",
                      "label": "Exclude All Test Files"
                    },
                    {
                      "id": "show-only-specific-file-types",
                      "label": "Show Only Specific File Types"
                    },
                    {
                      "id": "complex-filtering-with-regex",
                      "label": "Complex Filtering with Regex"
                    },
                    {
                      "id": "pattern-matching-with-file-statistics",
                      "label": "Pattern Matching with File Statistics"
                    },
                    {
                      "id": "filter-based-on-file-contents-(gitignore-style)",
                      "label": "Filter Based on File Contents (Gitignore Style)"
                    }
                  ]
                },
                {
                  "id": "performance-considerations",
                  "label": "Performance Considerations"
                },
                {
                  "id": "common-use-cases",
                  "label": "Common Use Cases",
                  "children": [
                    {
                      "id": "development-project",
                      "label": "Development Project"
                    },
                    {
                      "id": "documentation-project",
                      "label": "Documentation Project"
                    },
                    {
                      "id": "source-code-analysis",
                      "label": "Source Code Analysis"
                    },
                    {
                      "id": "backend-development",
                      "label": "Backend Development"
                    }
                  ]
                },
                {
                  "id": "troubleshooting-pattern-matching",
                  "label": "Troubleshooting Pattern Matching"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "examples",
      "label": "Examples",
      "children": [
        {
          "id": "basic-examples",
          "label": "Basic Examples",
          "children": [
            {
              "id": "basic-examples",
              "label": "Basic Examples",
              "children": [
                {
                  "id": "simple-visualization",
                  "label": "Simple Visualization",
                  "children": [
                    {
                      "id": "viewing-the-current-directory",
                      "label": "Viewing the Current Directory"
                    },
                    {
                      "id": "viewing-a-specific-directory",
                      "label": "Viewing a Specific Directory"
                    },
                    {
                      "id": "limiting-directory-depth",
                      "label": "Limiting Directory Depth"
                    },
                    {
                      "id": "showing-full-paths",
                      "label": "Showing Full Paths"
                    }
                  ]
                },
                {
                  "id": "file-statistics",
                  "label": "File Statistics",
                  "children": [
                    {
                      "id": "showing-lines-of-code",
                      "label": "Showing Lines of Code"
                    },
                    {
                      "id": "showing-file-sizes",
                      "label": "Showing File Sizes"
                    },
                    {
                      "id": "showing-modification-times",
                      "label": "Showing Modification Times"
                    },
                    {
                      "id": "combining-statistics",
                      "label": "Combining Statistics"
                    }
                  ]
                },
                {
                  "id": "simple-exclusions",
                  "label": "Simple Exclusions",
                  "children": [
                    {
                      "id": "excluding-specific-directories",
                      "label": "Excluding Specific Directories"
                    },
                    {
                      "id": "excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "combining-exclusions",
                      "label": "Combining Exclusions"
                    }
                  ]
                },
                {
                  "id": "basic-exports",
                  "label": "Basic Exports",
                  "children": [
                    {
                      "id": "exporting-to-markdown",
                      "label": "Exporting to Markdown"
                    },
                    {
                      "id": "exporting-to-multiple-formats",
                      "label": "Exporting to Multiple Formats"
                    },
                    {
                      "id": "exporting-to-a-specific-directory",
                      "label": "Exporting to a Specific Directory"
                    },
                    {
                      "id": "customizing-the-filename",
                      "label": "Customizing the Filename"
                    },
                    {
                      "id": "exporting-with-statistics",
                      "label": "Exporting with Statistics"
                    }
                  ]
                },
                {
                  "id": "simple-comparisons",
                  "label": "Simple Comparisons",
                  "children": [
                    {
                      "id": "comparing-two-directories",
                      "label": "Comparing Two Directories"
                    },
                    {
                      "id": "exporting-a-comparison",
                      "label": "Exporting a Comparison"
                    },
                    {
                      "id": "comparing-with-statistics",
                      "label": "Comparing with Statistics"
                    }
                  ]
                },
                {
                  "id": "shell-completion",
                  "label": "Shell Completion",
                  "children": [
                    {
                      "id": "generating-shell-completion-for-bash",
                      "label": "Generating Shell Completion for Bash"
                    },
                    {
                      "id": "generating-shell-completion-for-zsh",
                      "label": "Generating Shell Completion for Zsh"
                    }
                  ]
                },
                {
                  "id": "version-information",
                  "label": "Version Information"
                },
                {
                  "id": "next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        },
        {
          "id": "filtering-examples",
          "label": "Filtering Examples",
          "children": [
            {
              "id": "filtering-examples",
              "label": "Filtering Examples",
              "children": [
                {
                  "id": "basic-exclusion-options",
                  "label": "Basic Exclusion Options",
                  "children": [
                    {
                      "id": "excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    }
                  ]
                },
                {
                  "id": "pattern-based-filtering",
                  "label": "Pattern-Based Filtering",
                  "children": [
                    {
                      "id": "using-glob-patterns-(default)",
                      "label": "Using Glob Patterns (Default)"
                    },
                    {
                      "id": "using-regular-expressions",
                      "label": "Using Regular Expressions"
                    }
                  ]
                },
                {
                  "id": "include-patterns",
                  "label": "Include Patterns"
                },
                {
                  "id": "using-gitignore-files",
                  "label": "Using Gitignore Files"
                },
                {
                  "id": "combining-filtering-methods",
                  "label": "Combining Filtering Methods"
                },
                {
                  "id": "filter-order-of-precedence",
                  "label": "Filter Order of Precedence"
                },
                {
                  "id": "language-specific-examples",
                  "label": "Language-Specific Examples",
                  "children": [
                    {
                      "id": "python-project",
                      "label": "Python Project"
                    },
                    {
                      "id": "javascript/typescript-project",
                      "label": "JavaScript/TypeScript Project"
                    },
                    {
                      "id": "java/maven-project",
                      "label": "Java/Maven Project"
                    },
                    {
                      "id": "ruby-on-rails-project",
                      "label": "Ruby on Rails Project"
                    }
                  ]
                },
                {
                  "id": "task-specific-filtering",
                  "label": "Task-Specific Filtering",
                  "children": [
                    {
                      "id": "code-review-focus",
                      "label": "Code Review Focus"
                    },
                    {
                      "id": "documentation-overview",
                      "label": "Documentation Overview"
                    },
                    {
                      "id": "security-audit",
                      "label": "Security Audit"
                    },
                    {
                      "id": "performance-analysis",
                      "label": "Performance Analysis"
                    }
                  ]
                },
                {
                  "id": "using-filters-with-export",
                  "label": "Using Filters with Export"
                },
                {
                  "id": "using-filters-with-compare",
                  "label": "Using Filters with Compare"
                },
                {
                  "id": "advanced-pattern-examples",
                  "label": "Advanced Pattern Examples",
                  "children": [
                    {
                      "id": "frontend-files-only",
                      "label": "Frontend Files Only"
                    },
                    {
                      "id": "backend-files-only",
                      "label": "Backend Files Only"
                    },
                    {
                      "id": "configuration-files-only",
                      "label": "Configuration Files Only"
                    },
                    {
                      "id": "feature-specific-files",
                      "label": "Feature-Specific Files"
                    },
                    {
                      "id": "exclude-generated-code",
                      "label": "Exclude Generated Code"
                    },
                    {
                      "id": "focus-on-recently-modified-files",
                      "label": "Focus on Recently Modified Files"
                    }
                  ]
                },
                {
                  "id": "combining-with-file-statistics",
                  "label": "Combining with File Statistics"
                },
                {
                  "id": "shell-script-for-filtered-analysis",
                  "label": "Shell Script for Filtered Analysis"
                }
              ]
            }
          ]
        },
        {
          "id": "export-examples",
          "label": "Export Examples",
          "children": [
            {
              "id": "export-examples",
              "label": "Export Examples",
              "children": [
                {
                  "id": "basic-export-examples",
                  "label": "Basic Export Examples",
                  "children": [
                    {
                      "id": "exporting-to-different-formats",
                      "label": "Exporting to Different Formats",
                      "children": [
                        {
                          "id": "markdown-export",
                          "label": "Markdown Export"
                        },
                        {
                          "id": "json-export",
                          "label": "JSON Export"
                        },
                        {
                          "id": "html-export",
                          "label": "HTML Export"
                        },
                        {
                          "id": "text-export",
                          "label": "Text Export"
                        },
                        {
                          "id": "react-component-export",
                          "label": "React Component Export"
                        }
                      ]
                    },
                    {
                      "id": "exporting-to-multiple-formats-simultaneously",
                      "label": "Exporting to Multiple Formats Simultaneously"
                    }
                  ]
                },
                {
                  "id": "including-file-statistics",
                  "label": "Including File Statistics",
                  "children": [
                    {
                      "id": "exporting-with-lines-of-code-statistics",
                      "label": "Exporting with Lines of Code Statistics"
                    },
                    {
                      "id": "exporting-with-file-sizes",
                      "label": "Exporting with File Sizes"
                    },
                    {
                      "id": "exporting-with-modification-times",
                      "label": "Exporting with Modification Times"
                    },
                    {
                      "id": "combining-multiple-statistics",
                      "label": "Combining Multiple Statistics"
                    }
                  ]
                },
                {
                  "id": "customizing-export-output",
                  "label": "Customizing Export Output",
                  "children": [
                    {
                      "id": "custom-output-directory",
                      "label": "Custom Output Directory"
                    },
                    {
                      "id": "custom-filename-prefix",
                      "label": "Custom Filename Prefix"
                    },
                    {
                      "id": "combining-custom-directory-and-filename",
                      "label": "Combining Custom Directory and Filename"
                    }
                  ]
                },
                {
                  "id": "filtered-exports",
                  "label": "Filtered Exports",
                  "children": [
                    {
                      "id": "exporting-with-directory-exclusions",
                      "label": "Exporting with Directory Exclusions"
                    },
                    {
                      "id": "exporting-with-file-extension-exclusions",
                      "label": "Exporting with File Extension Exclusions"
                    },
                    {
                      "id": "exporting-with-pattern-exclusions",
                      "label": "Exporting with Pattern Exclusions"
                    },
                    {
                      "id": "exporting-only-specific-files",
                      "label": "Exporting Only Specific Files"
                    },
                    {
                      "id": "exporting-with-gitignore-patterns",
                      "label": "Exporting with Gitignore Patterns"
                    }
                  ]
                },
                {
                  "id": "depth-limited-exports",
                  "label": "Depth-Limited Exports",
                  "children": [
                    {
                      "id": "exporting-with-limited-depth",
                      "label": "Exporting with Limited Depth"
                    },
                    {
                      "id": "exporting-top-level-overview",
                      "label": "Exporting Top-Level Overview"
                    }
                  ]
                },
                {
                  "id": "full-path-exports",
                  "label": "Full Path Exports",
                  "children": [
                    {
                      "id": "json-export-with-full-paths",
                      "label": "JSON Export with Full Paths"
                    },
                    {
                      "id": "markdown-export-with-full-paths",
                      "label": "Markdown Export with Full Paths"
                    }
                  ]
                },
                {
                  "id": "specific-project-exports",
                  "label": "Specific Project Exports",
                  "children": [
                    {
                      "id": "source-code-documentation-with-loc-stats",
                      "label": "Source Code Documentation with LOC Stats"
                    },
                    {
                      "id": "project-overview-for-readme",
                      "label": "Project Overview for README"
                    }
                  ]
                },
                {
                  "id": "react-component-export-examples",
                  "label": "React Component Export Examples",
                  "children": [
                    {
                      "id": "basic-react-component-export",
                      "label": "Basic React Component Export"
                    },
                    {
                      "id": "customized-react-component-with-statistics",
                      "label": "Customized React Component with Statistics"
                    }
                  ]
                },
                {
                  "id": "export-for-different-use-cases",
                  "label": "Export for Different Use Cases",
                  "children": [
                    {
                      "id": "documentation-export-with-stats",
                      "label": "Documentation Export with Stats"
                    },
                    {
                      "id": "codebase-analysis-export",
                      "label": "Codebase Analysis Export"
                    },
                    {
                      "id": "website-integration-export",
                      "label": "Website Integration Export"
                    }
                  ]
                },
                {
                  "id": "batch-export-examples",
                  "label": "Batch Export Examples",
                  "children": [
                    {
                      "id": "multiple-export-configuration-script",
                      "label": "Multiple Export Configuration Script"
                    },
                    {
                      "id": "project-subdirectory-exports-with-stats",
                      "label": "Project Subdirectory Exports with Stats"
                    }
                  ]
                },
                {
                  "id": "combining-with-shell-commands",
                  "label": "Combining with Shell Commands",
                  "children": [
                    {
                      "id": "export-and-process-with-jq",
                      "label": "Export and Process with jq"
                    },
                    {
                      "id": "export-and-include-in-documentation",
                      "label": "Export and Include in Documentation"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "compare-examples",
          "label": "Compare Examples",
          "children": [
            {
              "id": "compare-examples",
              "label": "Compare Examples",
              "children": [
                {
                  "id": "basic-comparison-examples",
                  "label": "Basic Comparison Examples",
                  "children": [
                    {
                      "id": "simple-directory-comparison",
                      "label": "Simple Directory Comparison"
                    },
                    {
                      "id": "saving-comparison-as-html",
                      "label": "Saving Comparison as HTML"
                    },
                    {
                      "id": "custom-output-location",
                      "label": "Custom Output Location"
                    },
                    {
                      "id": "custom-filename",
                      "label": "Custom Filename"
                    }
                  ]
                },
                {
                  "id": "comparison-with-file-statistics",
                  "label": "Comparison with File Statistics",
                  "children": [
                    {
                      "id": "comparing-with-lines-of-code",
                      "label": "Comparing with Lines of Code"
                    },
                    {
                      "id": "comparing-with-file-sizes",
                      "label": "Comparing with File Sizes"
                    },
                    {
                      "id": "comparing-with-modification-times",
                      "label": "Comparing with Modification Times"
                    },
                    {
                      "id": "combining-multiple-statistics",
                      "label": "Combining Multiple Statistics"
                    }
                  ]
                },
                {
                  "id": "filtered-comparisons",
                  "label": "Filtered Comparisons",
                  "children": [
                    {
                      "id": "comparing-with-directory-exclusions",
                      "label": "Comparing with Directory Exclusions"
                    },
                    {
                      "id": "comparing-with-file-extension-exclusions",
                      "label": "Comparing with File Extension Exclusions"
                    },
                    {
                      "id": "comparing-with-pattern-exclusions",
                      "label": "Comparing with Pattern Exclusions"
                    },
                    {
                      "id": "focusing-on-specific-files",
                      "label": "Focusing on Specific Files"
                    },
                    {
                      "id": "comparing-with-gitignore-patterns",
                      "label": "Comparing with Gitignore Patterns"
                    }
                  ]
                },
                {
                  "id": "depth-limited-comparisons",
                  "label": "Depth-Limited Comparisons",
                  "children": [
                    {
                      "id": "comparing-top-level-structure",
                      "label": "Comparing Top-Level Structure"
                    },
                    {
                      "id": "comparing-with-limited-depth",
                      "label": "Comparing with Limited Depth"
                    }
                  ]
                },
                {
                  "id": "full-path-comparisons",
                  "label": "Full Path Comparisons",
                  "children": [
                    {
                      "id": "comparing-with-full-paths",
                      "label": "Comparing with Full Paths"
                    }
                  ]
                },
                {
                  "id": "real-world-use-cases",
                  "label": "Real-World Use Cases",
                  "children": [
                    {
                      "id": "project-version-comparison-with-statistics",
                      "label": "Project Version Comparison with Statistics"
                    },
                    {
                      "id": "branch-comparison-with-statistics",
                      "label": "Branch Comparison with Statistics"
                    },
                    {
                      "id": "source-vs.-build-comparison-with-file-sizes",
                      "label": "Source vs. Build Comparison with File Sizes"
                    },
                    {
                      "id": "development-vs.-production-configuration-comparison",
                      "label": "Development vs. Production Configuration Comparison"
                    }
                  ]
                },
                {
                  "id": "specific-comparison-scenarios",
                  "label": "Specific Comparison Scenarios",
                  "children": [
                    {
                      "id": "code-library-upgrade-analysis",
                      "label": "Code Library Upgrade Analysis"
                    },
                    {
                      "id": "project-fork-comparison",
                      "label": "Project Fork Comparison"
                    },
                    {
                      "id": "backup-verification-with-file-sizes",
                      "label": "Backup Verification with File Sizes"
                    },
                    {
                      "id": "framework-comparison-with-lines-of-code",
                      "label": "Framework Comparison with Lines of Code"
                    }
                  ]
                },
                {
                  "id": "combining-with-other-tools",
                  "label": "Combining with Other Tools",
                  "children": [
                    {
                      "id": "comparison-and-analysis-script",
                      "label": "Comparison and Analysis Script"
                    },
                    {
                      "id": "continuous-integration-comparison-with-statistics",
                      "label": "Continuous Integration Comparison with Statistics"
                    },
                    {
                      "id": "weekly-project-evolution-report",
                      "label": "Weekly Project Evolution Report"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "advanced-examples",
          "label": "Advanced Examples",
          "children": [
            {
              "id": "advanced-examples",
              "label": "Advanced Examples",
              "children": [
                {
                  "id": "working-with-file-statistics",
                  "label": "Working with File Statistics",
                  "children": [
                    {
                      "id": "finding-large-files-across-projects",
                      "label": "Finding Large Files Across Projects"
                    },
                    {
                      "id": "lines-of-code-analysis-with-filtering",
                      "label": "Lines of Code Analysis with Filtering"
                    },
                    {
                      "id": "finding-recently-modified-code",
                      "label": "Finding Recently Modified Code"
                    }
                  ]
                },
                {
                  "id": "combining-commands-with-shell-scripts",
                  "label": "Combining Commands with Shell Scripts",
                  "children": [
                    {
                      "id": "batch-processing-multiple-directories",
                      "label": "Batch Processing Multiple Directories"
                    },
                    {
                      "id": "project-report-generator",
                      "label": "Project Report Generator"
                    }
                  ]
                },
                {
                  "id": "integration-with-other-tools",
                  "label": "Integration with Other Tools",
                  "children": [
                    {
                      "id": "git-hook-for-project-structure-documentation",
                      "label": "Git Hook for Project Structure Documentation"
                    },
                    {
                      "id": "using-with-continuous-integration",
                      "label": "Using with Continuous Integration"
                    },
                    {
                      "id": "mkdocs-integration-with-statistics",
                      "label": "MkDocs Integration with Statistics"
                    }
                  ]
                },
                {
                  "id": "using-with-git-repositories",
                  "label": "Using with Git Repositories",
                  "children": [
                    {
                      "id": "comparing-git-branches-with-statistics",
                      "label": "Comparing Git Branches with Statistics"
                    },
                    {
                      "id": "analyzing-git-repository-structure-with-statistics",
                      "label": "Analyzing Git Repository Structure with Statistics"
                    }
                  ]
                },
                {
                  "id": "limiting-directory-depth-with-file-statistics",
                  "label": "Limiting Directory Depth with File Statistics",
                  "children": [
                    {
                      "id": "visualizing-deep-directories-incrementally-with-statistics",
                      "label": "Visualizing Deep Directories Incrementally with Statistics"
                    },
                    {
                      "id": "creating-a-multi-level-project-map-with-statistics",
                      "label": "Creating a Multi-Level Project Map with Statistics"
                    }
                  ]
                },
                {
                  "id": "react-component-integration-with-statistics",
                  "label": "React Component Integration with Statistics",
                  "children": [
                    {
                      "id": "creating-a-project-explorer-with-file-statistics",
                      "label": "Creating a Project Explorer with File Statistics"
                    }
                  ]
                },
                {
                  "id": "using-regex-patterns-with-file-statistics",
                  "label": "Using Regex Patterns with File Statistics",
                  "children": [
                    {
                      "id": "finding-complex-files-by-size",
                      "label": "Finding Complex Files by Size"
                    },
                    {
                      "id": "finding-files-by-loc-and-type",
                      "label": "Finding Files by LOC and Type"
                    }
                  ]
                },
                {
                  "id": "integration-with-analysis-tools",
                  "label": "Integration with Analysis Tools",
                  "children": [
                    {
                      "id": "structure-analysis-with-loc-statistics",
                      "label": "Structure Analysis with LOC Statistics"
                    }
                  ]
                },
                {
                  "id": "using-with-ignore-files-and-file-statistics",
                  "label": "Using with Ignore Files and File Statistics",
                  "children": [
                    {
                      "id": "custom-ignore-file-for-documentation-with-statistics",
                      "label": "Custom Ignore File for Documentation with Statistics"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "advanced",
      "label": "Advanced",
      "children": [
        {
          "id": "integration",
          "label": "Integration",
          "children": [
            {
              "id": "integration-with-other-tools",
              "label": "Integration with Other Tools",
              "children": [
                {
                  "id": "using-with-git-repositories",
                  "label": "Using with Git Repositories",
                  "children": [
                    {
                      "id": "gitignore-integration",
                      "label": "Gitignore Integration"
                    },
                    {
                      "id": "pre-commit-framework",
                      "label": "Pre-commit Framework"
                    },
                    {
                      "id": "manual-git-hooks",
                      "label": "Manual Git Hooks"
                    },
                    {
                      "id": "git-workflow-scripts",
                      "label": "Git Workflow Scripts"
                    }
                  ]
                },
                {
                  "id": "processing-json-exports-with-jq",
                  "label": "Processing JSON Exports with jq",
                  "children": [
                    {
                      "id": "count-files-by-extension",
                      "label": "Count Files by Extension"
                    },
                    {
                      "id": "find-largest-files",
                      "label": "Find Largest Files"
                    },
                    {
                      "id": "find-files-with-most-lines-of-code",
                      "label": "Find Files with Most Lines of Code"
                    },
                    {
                      "id": "analyze-code-distribution-by-directory",
                      "label": "Analyze Code Distribution by Directory"
                    }
                  ]
                },
                {
                  "id": "programmatic-use-with-python",
                  "label": "Programmatic Use with Python",
                  "children": [
                    {
                      "id": "basic-directory-analysis",
                      "label": "Basic Directory Analysis"
                    },
                    {
                      "id": "custom-file-analysis",
                      "label": "Custom File Analysis"
                    }
                  ]
                },
                {
                  "id": "web-application-integration",
                  "label": "Web Application Integration",
                  "children": [
                    {
                      "id": "using-the-react-component-export",
                      "label": "Using the React Component Export"
                    },
                    {
                      "id": "custom-api-with-flask",
                      "label": "Custom API with Flask"
                    }
                  ]
                },
                {
                  "id": "continuous-integration-integration",
                  "label": "Continuous Integration Integration",
                  "children": [
                    {
                      "id": "github-actions-example",
                      "label": "GitHub Actions Example"
                    },
                    {
                      "id": "gitlab-ci-example",
                      "label": "GitLab CI Example"
                    }
                  ]
                },
                {
                  "id": "documentation-tools-integration",
                  "label": "Documentation Tools Integration",
                  "children": [
                    {
                      "id": "mkdocs-integration",
                      "label": "MkDocs Integration"
                    },
                    {
                      "id": "sphinx-integration",
                      "label": "Sphinx Integration"
                    }
                  ]
                },
                {
                  "id": "shell-script-integration",
                  "label": "Shell Script Integration",
                  "children": [
                    {
                      "id": "batch-processing-multiple-directories",
                      "label": "Batch Processing Multiple Directories"
                    },
                    {
                      "id": "weekly-project-evolution-report",
                      "label": "Weekly Project Evolution Report"
                    }
                  ]
                },
                {
                  "id": "using-with-static-analysis-tools",
                  "label": "Using with Static Analysis Tools"
                }
              ]
            }
          ]
        },
        {
          "id": "development",
          "label": "Development",
          "children": [
            {
              "id": "development-guide",
              "label": "Development Guide",
              "children": [
                {
                  "id": "setting-up-development-environment",
                  "label": "Setting Up Development Environment",
                  "children": [
                    {
                      "id": "prerequisites",
                      "label": "Prerequisites"
                    },
                    {
                      "id": "clone-the-repository",
                      "label": "Clone the Repository"
                    },
                    {
                      "id": "create-a-virtual-environment",
                      "label": "Create a Virtual Environment"
                    },
                    {
                      "id": "install-development-dependencies",
                      "label": "Install Development Dependencies"
                    },
                    {
                      "id": "install-pre-commit-hooks",
                      "label": "Install Pre-commit Hooks"
                    }
                  ]
                },
                {
                  "id": "project-structure",
                  "label": "Project Structure",
                  "children": [
                    {
                      "id": "module-responsibilities",
                      "label": "Module Responsibilities"
                    }
                  ]
                },
                {
                  "id": "development-workflow",
                  "label": "Development Workflow",
                  "children": [
                    {
                      "id": "making-changes",
                      "label": "Making Changes"
                    },
                    {
                      "id": "code-style",
                      "label": "Code Style"
                    }
                  ]
                },
                {
                  "id": "adding-a-new-feature",
                  "label": "Adding a New Feature",
                  "children": [
                    {
                      "id": "adding-a-new-command",
                      "label": "Adding a New Command"
                    },
                    {
                      "id": "adding-a-new-export-format",
                      "label": "Adding a New Export Format"
                    },
                    {
                      "id": "adding-new-file-statistics",
                      "label": "Adding New File Statistics"
                    }
                  ]
                },
                {
                  "id": "testing",
                  "label": "Testing",
                  "children": [
                    {
                      "id": "basic-testing",
                      "label": "Basic Testing"
                    }
                  ]
                },
                {
                  "id": "debugging",
                  "label": "Debugging",
                  "children": [
                    {
                      "id": "verbose-output",
                      "label": "Verbose Output"
                    },
                    {
                      "id": "using-a-debugger",
                      "label": "Using a Debugger"
                    }
                  ]
                },
                {
                  "id": "documentation",
                  "label": "Documentation",
                  "children": [
                    {
                      "id": "docstrings",
                      "label": "Docstrings"
                    },
                    {
                      "id": "command-line-help",
                      "label": "Command-Line Help"
                    }
                  ]
                },
                {
                  "id": "performance-considerations",
                  "label": "Performance Considerations",
                  "children": [
                    {
                      "id": "large-directory-structures",
                      "label": "Large Directory Structures"
                    },
                    {
                      "id": "profiling",
                      "label": "Profiling"
                    }
                  ]
                },
                {
                  "id": "extending-pattern-matching",
                  "label": "Extending Pattern Matching"
                },
                {
                  "id": "release-process",
                  "label": "Release Process",
                  "children": [
                    {
                      "id": "version-numbering",
                      "label": "Version Numbering"
                    },
                    {
                      "id": "creating-a-release",
                      "label": "Creating a Release"
                    }
                  ]
                },
                {
                  "id": "common-development-tasks",
                  "label": "Common Development Tasks",
                  "children": [
                    {
                      "id": "adding-a-new-command-line-option",
                      "label": "Adding a New Command-Line Option"
                    },
                    {
                      "id": "improving-colorization",
                      "label": "Improving Colorization"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "testing",
          "label": "Testing",
          "children": [
            {
              "id": "testing-guide",
              "label": "Testing Guide",
              "children": [
                {
                  "id": "testing-framework",
                  "label": "Testing Framework"
                },
                {
                  "id": "running-tests",
                  "label": "Running Tests",
                  "children": [
                    {
                      "id": "basic-test-commands",
                      "label": "Basic Test Commands"
                    },
                    {
                      "id": "coverage",
                      "label": "Coverage"
                    }
                  ]
                },
                {
                  "id": "test-organization",
                  "label": "Test Organization"
                },
                {
                  "id": "writing-tests",
                  "label": "Writing Tests",
                  "children": [
                    {
                      "id": "test-structure",
                      "label": "Test Structure"
                    },
                    {
                      "id": "testing-directory-operations",
                      "label": "Testing Directory Operations"
                    },
                    {
                      "id": "testing-cli-commands",
                      "label": "Testing CLI Commands"
                    },
                    {
                      "id": "testing-export-formats",
                      "label": "Testing Export Formats"
                    },
                    {
                      "id": "testing-with-parametrization",
                      "label": "Testing with Parametrization"
                    }
                  ]
                },
                {
                  "id": "test-fixtures",
                  "label": "Test Fixtures"
                },
                {
                  "id": "mocking",
                  "label": "Mocking"
                },
                {
                  "id": "testing-pattern-matching",
                  "label": "Testing Pattern Matching"
                },
                {
                  "id": "testing-statistics",
                  "label": "Testing Statistics"
                },
                {
                  "id": "testing-cli-options",
                  "label": "Testing CLI Options"
                },
                {
                  "id": "debugging-tests",
                  "label": "Debugging Tests"
                },
                {
                  "id": "testing-complex-directory-structures",
                  "label": "Testing Complex Directory Structures"
                },
                {
                  "id": "testing-edge-cases",
                  "label": "Testing Edge Cases"
                },
                {
                  "id": "continuous-integration",
                  "label": "Continuous Integration"
                },
                {
                  "id": "test-driven-development",
                  "label": "Test-Driven Development"
                },
                {
                  "id": "test-best-practices",
                  "label": "Test Best Practices"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "contributing",
      "label": "Contributing",
      "children": [
        {
          "id": "contributing-to-recursivist",
          "label": "Contributing to Recursivist",
          "children": [
            {
              "id": "table-of-contents",
              "label": "Table of Contents"
            },
            {
              "id": "code-of-conduct",
              "label": "Code of Conduct"
            },
            {
              "id": "getting-started",
              "label": "Getting Started",
              "children": [
                {
                  "id": "setting-up-your-development-environment",
                  "label": "Setting Up Your Development Environment"
                }
              ]
            },
            {
              "id": "development-workflow",
              "label": "Development Workflow",
              "children": [
                {
                  "id": "creating-a-branch",
                  "label": "Creating a Branch"
                },
                {
                  "id": "making-changes",
                  "label": "Making Changes"
                },
                {
                  "id": "testing-your-changes",
                  "label": "Testing Your Changes"
                },
                {
                  "id": "submitting-a-pull-request",
                  "label": "Submitting a Pull Request"
                }
              ]
            },
            {
              "id": "coding-standards",
              "label": "Coding Standards",
              "children": [
                {
                  "id": "code-style",
                  "label": "Code Style"
                },
                {
                  "id": "documentation",
                  "label": "Documentation"
                },
                {
                  "id": "type-annotations",
                  "label": "Type Annotations"
                }
              ]
            },
            {
              "id": "testing",
              "label": "Testing",
              "children": [
                {
                  "id": "running-tests",
                  "label": "Running Tests"
                },
                {
                  "id": "writing-tests",
                  "label": "Writing Tests"
                }
              ]
            },
            {
              "id": "bug-reports-and-feature-requests",
              "label": "Bug Reports and Feature Requests",
              "children": [
                {
                  "id": "reporting-bugs",
                  "label": "Reporting Bugs"
                },
                {
                  "id": "suggesting-features",
                  "label": "Suggesting Features"
                }
              ]
            },
            {
              "id": "release-process",
              "label": "Release Process"
            },
            {
              "id": "community",
              "label": "Community"
            }
          ]
        }
      ]
    },
    {
      "id": "sitemap",
      "label": "Sitemap",
      "children": [
        {
          "id": "sitemap",
          "label": "Sitemap"
        }
      ]
    }
  ]
};

    const BRANCH_COLORS = ["#7c3aed", "#ec4899", "#10b981", "#f59e0b"];

    function isDark() {
      return (
        document.documentElement.getAttribute("data-md-color-scheme") ===
        "slate"
      );
    }

    function assignColors(node, branchIdx, depth) {
      if (depth === 0) {
        node._color = "#3b82f6";
      } else if (depth === 1) {
        const i = TREE.children.indexOf(node);
        node._branchIdx = i;
        node._color =
          BRANCH_COLORS[i % BRANCH_COLORS.length];
      } else {
        const bi = branchIdx ?? 0;
        node._branchIdx = bi;
        node._color = BRANCH_COLORS[bi % BRANCH_COLORS.length];
      }

      if (node.children) {
        const nextBI = node._branchIdx ?? branchIdx;
        node.children.forEach((c) =>
          assignColors(c, nextBI, depth + 1)
        );
      }
    }

    const NW = 128,
      NH = 38,
      TR = 9;
    const LR_HGAP = 58,
      LR_VGAP = 14;
    const TB_XGAP = 22,
      TB_YGAP = 58;

    const collapsed = new Set();
    const pos = {};
    const nodeMap = {};

    let orientation = "LR";
    let allCollapsed = false;
    let panX = 0,
      panY = 0;

    function index(n) {
      nodeMap[n.id] = n;
      (n.children || []).forEach(index);
    }
    index(TREE);

    function setInitialCollapse(node, depth) {
      if (depth >= 1 && node.children?.length) {
        collapsed.add(node.id);
      }
      (node.children || []).forEach((c) => setInitialCollapse(c, depth + 1));
    }

    setInitialCollapse(TREE, 0);

    function lrH(node) {
      if (collapsed.has(node.id) || !node.children?.length)
        return NH;

      const h =
        node.children.reduce((s, c) => s + lrH(c), 0) +
        (node.children.length - 1) * LR_VGAP;

      return Math.max(NH, h);
    }

    function lrPlace(node, x, y) {
      pos[node.id] = { x, y };

      if (collapsed.has(node.id) || !node.children?.length)
        return;

      const total =
        node.children.reduce((s, c) => s + lrH(c), 0) +
        (node.children.length - 1) * LR_VGAP;

      let cy = y - total / 2;
      const cx = x + NW + LR_HGAP;

      for (const c of node.children) {
        const h = lrH(c);
        lrPlace(c, cx, cy + h / 2);
        cy += h + LR_VGAP;
      }
    }

    function tbW(node) {
      if (collapsed.has(node.id) || !node.children?.length)
        return NW;

      const w =
        node.children.reduce((s, c) => s + tbW(c), 0) +
        (node.children.length - 1) * TB_XGAP;

      return Math.max(NW, w);
    }

    function tbPlace(node, x, y) {
      pos[node.id] = { x, y };

      if (collapsed.has(node.id) || !node.children?.length)
        return;

      const total =
        node.children.reduce((s, c) => s + tbW(c), 0) +
        (node.children.length - 1) * TB_XGAP;

      let cx = x - total / 2;
      const cy = y + NH + TB_YGAP;

      for (const c of node.children) {
        const w = tbW(c);
        tbPlace(c, cx + w / 2, cy);
        cx += w + TB_XGAP;
      }
    }

    function doLayout() {
      const isFirstRender = !pos[TREE.id];

      const targetX = isFirstRender ? (orientation === "LR" ? 300 : window.innerWidth / 2) : pos[TREE.id].x;
      const targetY = isFirstRender ? (orientation === "LR" ? 325 : 300) : pos[TREE.id].y;

      if (orientation === "LR") {
        lrPlace(TREE, 0, 0);
      } else {
        tbPlace(TREE, 0, 0);
      }

      const dx = targetX - pos[TREE.id].x;
      const dy = targetY - pos[TREE.id].y;

      Object.keys(pos).forEach((id) => {
        pos[id].x += dx;
        pos[id].y += dy;
      });
    }

    const NS = "http://www.w3.org/2000/svg";

    function el(tag, attrs, parent) {
      const e = document.createElementNS(NS, tag);
      for (const [k, v] of Object.entries(attrs || {})) {
        e.setAttribute(k, v);
      }
      if (parent) parent.appendChild(e);
      return e;
    }

    function lrCurve(px, py, cx, cy) {
      const mx =
        px + NW + (cx - px - NW) * 0.55;
      return `M${px + NW},${py} C${mx},${py} ${mx},${cy} ${cx},${cy}`;
    }

    function tbCurve(px, py, cx, cy) {
      const my =
        py + NH + (cy - py - NH) * 0.55;
      return `M${px + NW / 2},${py + NH} C${px + NW / 2},${my} ${cx + NW / 2},${my} ${cx + NW / 2},${cy}`;
    }

    function doDraw() {
      const svg = document.getElementById("mm-svg");
      svg.innerHTML = "";

      assignColors(TREE, null, 0);

      const eL = el("g", {}, svg);
      const nL = el("g", {}, svg);

      function drawNode(node) {
        const p = pos[node.id];
        if (!p) return;

        const { x, y } = p;
        const isCol = collapsed.has(node.id);
        const hasKids =
          node.children?.length > 0;

        if (!isCol && node.children) {
          for (const c of node.children) {
            const cp = pos[c.id];
            if (!cp) continue;

            const d =
              orientation === "LR"
                ? lrCurve(x, y, cp.x, cp.y)
                : tbCurve(x, y, cp.x, cp.y);

            el(
              "path",
              {
                class: "mm-edge",
                d,
                stroke: c._color,
                "stroke-width": 2,
                "stroke-opacity": 0.5,
              },
              eL
            );
          }
        }

        const g = el(
          "g",
          { class: "mm-node-g", "data-id": node.id },
          nL
        );

        el(
          "rect",
          {
            x,
            y: y - NH / 2,
            width: NW,
            height: NH,
            rx: NH / 2,
            ry: NH / 2,
            fill: node._color,
            class: "mm-pill",
          },
          g
        );

        el(
          "text",
          {
            class: "mm-label",
            x: x + NW / 2,
            y,
          },
          g
        ).textContent = node.label;

        if (hasKids) {
          const [tx, ty] =
            orientation === "LR"
              ? [x + NW - 2, y]
              : [x + NW / 2, y + NH / 2 + 2];

          const tg = el(
            "g",
            {
              class: "mm-toggle-g",
              "data-id": node.id,
              transform: `translate(${tx},${ty})`,
            },
            nL
          );

          el("circle", { r: TR }, tg);
          el("text", { x: 0, y: 0.5 }, tg).textContent =
            isCol ? "+" : "−";

          tg.addEventListener("click", (e) => {
            e.stopPropagation();
            collapsed.has(node.id)
              ? collapsed.delete(node.id)
              : collapsed.add(node.id);
            render();
          });
        }

        if (!isCol && node.children) {
          node.children.forEach(drawNode);
        }
      }

      drawNode(TREE);
      attachNodeDrag();
    }

    function shiftTree(node, dx, dy) {
      if (!pos[node.id]) return;

      pos[node.id].x += dx;
      pos[node.id].y += dy;

      if (
        !collapsed.has(node.id) &&
        node.children
      ) {
        node.children.forEach((c) =>
          shiftTree(c, dx, dy)
        );
      }
    }

    function attachNodeDrag() {
      const svg =
        document.getElementById("mm-svg");

      let drag = null,
        sx,
        sy,
        snx,
        sny;

      svg
        .querySelectorAll(".mm-node-g")
        .forEach((g) => {
          g.addEventListener("mousedown", (e) => {
            if (e.target.closest(".mm-toggle-g"))
              return;

            drag = g.dataset.id;
            sx = e.clientX;
            sy = e.clientY;
            snx = pos[drag].x;
            sny = pos[drag].y;

            e.preventDefault();
            e.stopPropagation();
          });
        });

      function onMove(e) {
        if (!drag) return;

        const ddx =
          snx + (e.clientX - sx) - pos[drag].x;
        const ddy =
          sny + (e.clientY - sy) - pos[drag].y;

        shiftTree(
          nodeMap[drag],
          ddx,
          ddy
        );
        doDraw();
      }

      document.addEventListener(
        "mousemove",
        onMove
      );
      document.addEventListener(
        "mouseup",
        () => {
          drag = null;
        }
      );
    }

    (function () {
      const svg =
        document.getElementById("mm-svg");

      let panning = false,
        px,
        py;

      svg.addEventListener("mousedown", (e) => {
        if (
          e.target.closest(".mm-node-g") ||
          e.target.closest(".mm-toggle-g")
        )
          return;

        panning = true;
        px = e.clientX;
        py = e.clientY;
        e.preventDefault();
      });

      document.addEventListener(
        "mousemove",
        (e) => {
          if (!panning) return;

          const dx = e.clientX - px;
          const dy = e.clientY - py;

          panX += dx;
          panY += dy;

          shiftTree(TREE, dx, dy);
          doDraw();

          px = e.clientX;
          py = e.clientY;
        }
      );

      document.addEventListener(
        "mouseup",
        () => {
          panning = false;
        }
      );
    })();

    function render() {
      doLayout();
      doDraw();
    }

    const expcolBtn =
      document.getElementById(
        "mm-expcol-toggle"
      );
    const expcolIcon =
      document.getElementById(
        "mm-expcol-icon"
      );

    function syncExpcolBtn() {
      if (allCollapsed) {
        expcolIcon.className =
          "ph-duotone ph-arrows-out";
        expcolBtn.title = "Expand All";
      } else {
        expcolIcon.className =
          "ph-duotone ph-arrows-in";
        expcolBtn.title = "Collapse All";
      }
    }

    expcolBtn.onclick = () => {
      if (allCollapsed) {
        collapsed.clear();
        allCollapsed = false;
      } else {
        function col(n) {
          if (n.children?.length) {
            collapsed.add(n.id);
            n.children.forEach(col);
          }
        }
        col(TREE);
        allCollapsed = true;
      }

      panX = 0;
      panY = 0;

      syncExpcolBtn();
      render();
    };

    document.getElementById(
      "mm-reset-view"
    ).onclick = () => {
      collapsed.clear();
      setInitialCollapse(TREE, 0);
      allCollapsed = false;
      panX = 0;
      panY = 0;
      Object.keys(pos).forEach(k => delete pos[k]);
      syncExpcolBtn();
      render();
    };

    const orientBtn =
      document.getElementById(
        "mm-orient-toggle"
      );
    const iconsLR =
      document.getElementById(
        "mm-icons-lr"
      );
    const iconsTB =
      document.getElementById(
        "mm-icons-tb"
      );

    orientBtn.onclick = () => {
      orientation =
        orientation === "LR" ? "TB" : "LR";

      const isLR =
        orientation === "LR";

      iconsLR.style.display = isLR
        ? "none"
        : "";
      iconsTB.style.display = isLR
        ? ""
        : "none";

      orientBtn.title = isLR
        ? "Switch to Top → Bottom"
        : "Switch to Left → Right";

      panX = 0;
      panY = 0;

      render();
    };

    new MutationObserver(() =>
      doDraw()
    ).observe(document.documentElement, {
      attributes: true,
      attributeFilter: [
        "data-md-color-scheme",
      ],
    });

    syncExpcolBtn();
    render();

    window.addEventListener(
      "resize",
      () => {
        panX = 0;
        panY = 0;
        Object.keys(pos).forEach(k => delete pos[k]);
        render();
      }
    );

    (function transplantControls() {
      function doTransplant() {
        const sidebar = document.querySelector(
          ".md-sidebar--primary .md-sidebar__inner"
        );
        const controls =
          document.querySelector(
            ".mm-controls"
          );

        if (!sidebar || !controls) return;

        sidebar.innerHTML = "";

        const panel =
          document.createElement("div");
        panel.className =
          "mm-sidebar-panel";
        panel.innerHTML =
          '<span class="mm-sidebar-label">Map Controls</span>';

        panel.appendChild(controls);
        sidebar.appendChild(panel);

        const mapRoot = document.getElementById("mm-root");
        if (mapRoot) {
          document.body.appendChild(mapRoot);
        }
      }

      if (
        document.readyState === "loading"
      ) {
        document.addEventListener(
          "DOMContentLoaded",
          doTransplant
        );
      } else {
        doTransplant();
      }
    })();
  })();
</script>
