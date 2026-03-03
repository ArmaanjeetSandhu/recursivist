# Sitemap

<link
  rel="stylesheet"
  href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/duotone/style.css"
/>

<div class="mm-controls">
  <button class="mm-btn mm-icon-btn" id="mm-expcol-toggle" title="Collapse All">
    <i class="ph-duotone ph-arrows-in" id="mm-expcol-icon"></i>
  </button>

  <button class="mm-btn mm-icon-btn" id="mm-reset-view" title="Reset View">
    <i class="ph-duotone ph-arrows-counter-clockwise"></i>
  </button>

  <button class="mm-btn mm-orient-btn" id="mm-orient-toggle" title="Switch to Top → Bottom">

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

<div id="mm-root" style="position: fixed; inset: 0; pointer-events: none; z-index: 9999; overflow: visible">
  <svg id="mm-svg" xmlns="http://www.w3.org/2000/svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: visible"
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
      "id": "root/home",
      "label": "Home",
      "children": [
        {
          "id": "root/home/recursivist",
          "label": "Recursivist",
          "children": [
            {
              "id": "root/home/recursivist/key-features",
              "label": "Key Features"
            },
            {
              "id": "root/home/recursivist/quick-install",
              "label": "Quick Install"
            },
            {
              "id": "root/home/recursivist/getting-started",
              "label": "Getting Started"
            },
            {
              "id": "root/home/recursivist/next-steps",
              "label": "Next Steps"
            },
            {
              "id": "root/home/recursivist/license",
              "label": "License"
            }
          ]
        }
      ]
    },
    {
      "id": "root/getting-started",
      "label": "Getting Started",
      "children": [
        {
          "id": "root/getting-started/installation",
          "label": "Installation",
          "children": [
            {
              "id": "root/getting-started/installation/installation",
              "label": "Installation",
              "children": [
                {
                  "id": "root/getting-started/installation/installation/requirements",
                  "label": "Requirements"
                },
                {
                  "id": "root/getting-started/installation/installation/installing-from-pypi",
                  "label": "Installing from PyPI"
                },
                {
                  "id": "root/getting-started/installation/installation/installing-from-source",
                  "label": "Installing from Source"
                },
                {
                  "id": "root/getting-started/installation/installation/installing-for-development",
                  "label": "Installing for Development"
                },
                {
                  "id": "root/getting-started/installation/installation/verifying-installation",
                  "label": "Verifying Installation"
                },
                {
                  "id": "root/getting-started/installation/installation/system-specific-notes",
                  "label": "System-specific Notes",
                  "children": [
                    {
                      "id": "root/getting-started/installation/installation/system-specific-notes/windows",
                      "label": "Windows"
                    },
                    {
                      "id": "root/getting-started/installation/installation/system-specific-notes/macos",
                      "label": "macOS"
                    },
                    {
                      "id": "root/getting-started/installation/installation/system-specific-notes/linux",
                      "label": "Linux"
                    }
                  ]
                },
                {
                  "id": "root/getting-started/installation/installation/troubleshooting-installation-issues",
                  "label": "Troubleshooting Installation Issues",
                  "children": [
                    {
                      "id": "root/getting-started/installation/installation/troubleshooting-installation-issues/unicode-display-problems",
                      "label": "Unicode Display Problems"
                    },
                    {
                      "id": "root/getting-started/installation/installation/troubleshooting-installation-issues/color-display-issues",
                      "label": "Color Display Issues"
                    },
                    {
                      "id": "root/getting-started/installation/installation/troubleshooting-installation-issues/missing-dependencies",
                      "label": "Missing Dependencies"
                    }
                  ]
                },
                {
                  "id": "root/getting-started/installation/installation/next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        },
        {
          "id": "root/getting-started/quick-start",
          "label": "Quick Start",
          "children": [
            {
              "id": "root/getting-started/quick-start/quick-start-guide",
              "label": "Quick Start Guide",
              "children": [
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/basic-commands",
                  "label": "Basic Commands",
                  "children": [
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/basic-commands/visualize-a-directory",
                      "label": "Visualize a Directory"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/basic-commands/display-file-statistics",
                      "label": "Display File Statistics"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/basic-commands/export-a-directory-structure",
                      "label": "Export a Directory Structure"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/basic-commands/compare-two-directories",
                      "label": "Compare Two Directories"
                    }
                  ]
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/common-options",
                  "label": "Common Options",
                  "children": [
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/common-options/exclude-directories",
                      "label": "Exclude Directories"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/common-options/exclude-file-extensions",
                      "label": "Exclude File Extensions"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/common-options/pattern-filtering",
                      "label": "Pattern Filtering"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/common-options/limit-directory-depth",
                      "label": "Limit Directory Depth"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/common-options/show-full-paths",
                      "label": "Show Full Paths"
                    }
                  ]
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/quick-examples",
                  "label": "Quick Examples",
                  "children": [
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/quick-examples/basic-directory-visualization",
                      "label": "Basic Directory Visualization"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/quick-examples/visualizing-with-file-statistics",
                      "label": "Visualizing with File Statistics"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/quick-examples/export-to-multiple-formats",
                      "label": "Export to Multiple Formats"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/quick-examples/compare-with-exclusions",
                      "label": "Compare with Exclusions"
                    },
                    {
                      "id": "root/getting-started/quick-start/quick-start-guide/quick-examples/compare-with-file-statistics",
                      "label": "Compare with File Statistics"
                    }
                  ]
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/shell-completion",
                  "label": "Shell Completion"
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "root/user-guide",
      "label": "User Guide",
      "children": [
        {
          "id": "root/user-guide/basic-usage",
          "label": "Basic Usage",
          "children": [
            {
              "id": "root/user-guide/basic-usage/basic-usage",
              "label": "Basic Usage",
              "children": [
                {
                  "id": "root/user-guide/basic-usage/basic-usage/command-structure",
                  "label": "Command Structure"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/basic-commands",
                  "label": "Basic Commands",
                  "children": [
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/basic-commands/checking-version",
                      "label": "Checking Version"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/basic-commands/visualizing-the-current-directory",
                      "label": "Visualizing the Current Directory"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/basic-commands/visualizing-a-specific-directory",
                      "label": "Visualizing a Specific Directory"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/basic-commands/visualizing-with-file-statistics",
                      "label": "Visualizing with File Statistics"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/basic-commands/getting-help",
                      "label": "Getting Help"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/default-behavior",
                  "label": "Default Behavior"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/common-options",
                  "label": "Common Options",
                  "children": [
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/common-options/excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/common-options/excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/common-options/limiting-depth",
                      "label": "Limiting Depth"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/common-options/showing-full-paths",
                      "label": "Showing Full Paths"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/common-options/using-verbose-mode",
                      "label": "Using Verbose Mode"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/pattern-filtering",
                  "label": "Pattern Filtering",
                  "children": [
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/pattern-filtering/glob-patterns-(default)",
                      "label": "Glob Patterns (Default)"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/pattern-filtering/regular-expressions",
                      "label": "Regular Expressions"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/pattern-filtering/include-patterns-(override-exclusions)",
                      "label": "Include Patterns (Override Exclusions)"
                    },
                    {
                      "id": "root/user-guide/basic-usage/basic-usage/pattern-filtering/gitignore-integration",
                      "label": "Gitignore Integration"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/export-formats",
                  "label": "Export Formats"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/directory-comparison",
                  "label": "Directory Comparison"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/shell-completion",
                  "label": "Shell Completion"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/exit-codes",
                  "label": "Exit Codes"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        },
        {
          "id": "root/user-guide/visualization",
          "label": "Visualization",
          "children": [
            {
              "id": "root/user-guide/visualization/visualization",
              "label": "Visualization",
              "children": [
                {
                  "id": "root/user-guide/visualization/visualization/basic-visualization",
                  "label": "Basic Visualization"
                },
                {
                  "id": "root/user-guide/visualization/visualization/customizing-the-visualization",
                  "label": "Customizing the Visualization",
                  "children": [
                    {
                      "id": "root/user-guide/visualization/visualization/customizing-the-visualization/color-coding",
                      "label": "Color Coding"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/customizing-the-visualization/file-statistics",
                      "label": "File Statistics",
                      "children": [
                        {
                          "id": "root/user-guide/visualization/visualization/customizing-the-visualization/file-statistics/lines-of-code",
                          "label": "Lines of Code"
                        },
                        {
                          "id": "root/user-guide/visualization/visualization/customizing-the-visualization/file-statistics/file-sizes",
                          "label": "File Sizes"
                        },
                        {
                          "id": "root/user-guide/visualization/visualization/customizing-the-visualization/file-statistics/modification-times",
                          "label": "Modification Times"
                        },
                        {
                          "id": "root/user-guide/visualization/visualization/customizing-the-visualization/file-statistics/combining-statistics",
                          "label": "Combining Statistics"
                        }
                      ]
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/customizing-the-visualization/directory-depth-control",
                      "label": "Directory Depth Control"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/customizing-the-visualization/full-path-display",
                      "label": "Full Path Display"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/visualization/visualization/filtering-the-visualization",
                  "label": "Filtering the Visualization",
                  "children": [
                    {
                      "id": "root/user-guide/visualization/visualization/filtering-the-visualization/excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/filtering-the-visualization/excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/filtering-the-visualization/pattern-based-filtering",
                      "label": "Pattern-Based Filtering"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/filtering-the-visualization/using-gitignore-files",
                      "label": "Using Gitignore Files"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/visualization/visualization/output-example",
                  "label": "Output Example"
                },
                {
                  "id": "root/user-guide/visualization/visualization/verbose-mode",
                  "label": "Verbose Mode"
                },
                {
                  "id": "root/user-guide/visualization/visualization/terminal-compatibility",
                  "label": "Terminal Compatibility"
                },
                {
                  "id": "root/user-guide/visualization/visualization/performance-tips",
                  "label": "Performance Tips"
                },
                {
                  "id": "root/user-guide/visualization/visualization/related-commands",
                  "label": "Related Commands"
                }
              ]
            }
          ]
        },
        {
          "id": "root/user-guide/export",
          "label": "Export",
          "children": [
            {
              "id": "root/user-guide/export/export",
              "label": "Export",
              "children": [
                {
                  "id": "root/user-guide/export/export/basic-export-usage",
                  "label": "Basic Export Usage"
                },
                {
                  "id": "root/user-guide/export/export/available-export-formats",
                  "label": "Available Export Formats"
                },
                {
                  "id": "root/user-guide/export/export/exporting-to-multiple-formats",
                  "label": "Exporting to Multiple Formats"
                },
                {
                  "id": "root/user-guide/export/export/output-directory",
                  "label": "Output Directory"
                },
                {
                  "id": "root/user-guide/export/export/customizing-filenames",
                  "label": "Customizing Filenames"
                },
                {
                  "id": "root/user-guide/export/export/including-file-statistics",
                  "label": "Including File Statistics"
                },
                {
                  "id": "root/user-guide/export/export/filtering-exports",
                  "label": "Filtering Exports"
                },
                {
                  "id": "root/user-guide/export/export/depth-control",
                  "label": "Depth Control"
                },
                {
                  "id": "root/user-guide/export/export/full-path-display",
                  "label": "Full Path Display"
                },
                {
                  "id": "root/user-guide/export/export/format-specific-features",
                  "label": "Format-Specific Features",
                  "children": [
                    {
                      "id": "root/user-guide/export/export/format-specific-features/text-format-(.txt)",
                      "label": "Text Format (.txt)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-specific-features/json-format-(.json)",
                      "label": "JSON Format (.json)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-specific-features/html-format-(.html)",
                      "label": "HTML Format (.html)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-specific-features/markdown-format-(.md)",
                      "label": "Markdown Format (.md)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-specific-features/react-component-(.jsx)",
                      "label": "React Component (.jsx)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-specific-features/svg-format-(.svg)",
                      "label": "SVG Format (.svg)"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/export/export/using-the-react-component",
                  "label": "Using the React Component"
                },
                {
                  "id": "root/user-guide/export/export/examples",
                  "label": "Examples",
                  "children": [
                    {
                      "id": "root/user-guide/export/export/examples/basic-export-to-markdown",
                      "label": "Basic Export to Markdown"
                    },
                    {
                      "id": "root/user-guide/export/export/examples/export-to-multiple-formats-with-custom-prefix",
                      "label": "Export to Multiple Formats with Custom Prefix"
                    },
                    {
                      "id": "root/user-guide/export/export/examples/export-source-directory-only",
                      "label": "Export Source Directory Only"
                    },
                    {
                      "id": "root/user-guide/export/export/examples/export-with-depth-control-and-exclusions",
                      "label": "Export with Depth Control and Exclusions"
                    },
                    {
                      "id": "root/user-guide/export/export/examples/export-with-file-statistics",
                      "label": "Export with File Statistics"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "root/user-guide/compare",
          "label": "Compare",
          "children": [
            {
              "id": "root/user-guide/compare/compare",
              "label": "Compare",
              "children": [
                {
                  "id": "root/user-guide/compare/compare/basic-comparison",
                  "label": "Basic Comparison"
                },
                {
                  "id": "root/user-guide/compare/compare/understanding-the-output",
                  "label": "Understanding the Output"
                },
                {
                  "id": "root/user-guide/compare/compare/including-file-statistics",
                  "label": "Including File Statistics"
                },
                {
                  "id": "root/user-guide/compare/compare/exporting-comparison-results",
                  "label": "Exporting Comparison Results"
                },
                {
                  "id": "root/user-guide/compare/compare/filtering-the-comparison",
                  "label": "Filtering the Comparison",
                  "children": [
                    {
                      "id": "root/user-guide/compare/compare/filtering-the-comparison/excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "root/user-guide/compare/compare/filtering-the-comparison/excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "root/user-guide/compare/compare/filtering-the-comparison/pattern-based-filtering",
                      "label": "Pattern-Based Filtering"
                    },
                    {
                      "id": "root/user-guide/compare/compare/filtering-the-comparison/using-gitignore-files",
                      "label": "Using Gitignore Files"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/compare/compare/depth-control",
                  "label": "Depth Control"
                },
                {
                  "id": "root/user-guide/compare/compare/full-path-display",
                  "label": "Full Path Display"
                },
                {
                  "id": "root/user-guide/compare/compare/use-cases",
                  "label": "Use Cases",
                  "children": [
                    {
                      "id": "root/user-guide/compare/compare/use-cases/project-evolution",
                      "label": "Project Evolution"
                    },
                    {
                      "id": "root/user-guide/compare/compare/use-cases/code-reviews",
                      "label": "Code Reviews"
                    },
                    {
                      "id": "root/user-guide/compare/compare/use-cases/deployment-verification",
                      "label": "Deployment Verification"
                    },
                    {
                      "id": "root/user-guide/compare/compare/use-cases/backup-validation",
                      "label": "Backup Validation"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/compare/compare/examples",
                  "label": "Examples",
                  "children": [
                    {
                      "id": "root/user-guide/compare/compare/examples/basic-comparison",
                      "label": "Basic Comparison"
                    },
                    {
                      "id": "root/user-guide/compare/compare/examples/compare-with-exclusions",
                      "label": "Compare with Exclusions"
                    },
                    {
                      "id": "root/user-guide/compare/compare/examples/compare-with-depth-limit-and-html-export",
                      "label": "Compare with Depth Limit and HTML Export"
                    },
                    {
                      "id": "root/user-guide/compare/compare/examples/compare-source-directories-only",
                      "label": "Compare Source Directories Only"
                    },
                    {
                      "id": "root/user-guide/compare/compare/examples/compare-with-file-statistics",
                      "label": "Compare with File Statistics"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/compare/compare/html-output-features",
                  "label": "HTML Output Features"
                },
                {
                  "id": "root/user-guide/compare/compare/terminal-compatibility",
                  "label": "Terminal Compatibility"
                }
              ]
            }
          ]
        },
        {
          "id": "root/user-guide/pattern-filtering",
          "label": "Pattern Filtering",
          "children": [
            {
              "id": "root/user-guide/pattern-filtering/pattern-filtering",
              "label": "Pattern Filtering",
              "children": [
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/basic-filtering",
                  "label": "Basic Filtering",
                  "children": [
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/basic-filtering/excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/basic-filtering/excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/advanced-filtering",
                  "label": "Advanced Filtering",
                  "children": [
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/advanced-filtering/using-gitignore-files",
                      "label": "Using Gitignore Files"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/advanced-filtering/glob-pattern-filtering",
                      "label": "Glob Pattern Filtering"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/advanced-filtering/regex-pattern-filtering",
                      "label": "Regex Pattern Filtering"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/include-patterns",
                  "label": "Include Patterns"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/combining-filters",
                  "label": "Combining Filters"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/filter-order-of-precedence",
                  "label": "Filter Order of Precedence"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/examples",
                  "label": "Examples",
                  "children": [
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/examples/focus-on-source-code-only",
                      "label": "Focus on Source Code Only"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/examples/exclude-generated-files",
                      "label": "Exclude Generated Files"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/examples/view-only-documentation",
                      "label": "View Only Documentation"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/examples/complex-filtering-with-regex",
                      "label": "Complex Filtering with Regex"
                    },
                    {
                      "id": "root/user-guide/pattern-filtering/pattern-filtering/examples/filtering-with-file-statistics",
                      "label": "Filtering with File Statistics"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/filtering-in-export-and-compare-commands",
                  "label": "Filtering in Export and Compare Commands"
                }
              ]
            }
          ]
        },
        {
          "id": "root/user-guide/shell-completion",
          "label": "Shell Completion",
          "children": [
            {
              "id": "root/user-guide/shell-completion/shell-completion",
              "label": "Shell Completion",
              "children": [
                {
                  "id": "root/user-guide/shell-completion/shell-completion/what-is-shell-completion?",
                  "label": "What is Shell Completion?"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/generating-completion-scripts",
                  "label": "Generating Completion Scripts"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/setting-up-completion-for-different-shells",
                  "label": "Setting Up Completion for Different Shells",
                  "children": [
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/setting-up-completion-for-different-shells/bash",
                      "label": "Bash"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/setting-up-completion-for-different-shells/zsh",
                      "label": "Zsh"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/setting-up-completion-for-different-shells/fish",
                      "label": "Fish"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/setting-up-completion-for-different-shells/powershell",
                      "label": "PowerShell"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/using-shell-completion",
                  "label": "Using Shell Completion"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/completion-features",
                  "label": "Completion Features"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/troubleshooting",
                  "label": "Troubleshooting",
                  "children": [
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/troubleshooting/common-issues",
                      "label": "Common Issues",
                      "children": [
                        {
                          "id": "root/user-guide/shell-completion/shell-completion/troubleshooting/common-issues/permission-denied",
                          "label": "Permission Denied"
                        },
                        {
                          "id": "root/user-guide/shell-completion/shell-completion/troubleshooting/common-issues/completion-not-working",
                          "label": "Completion Not Working"
                        },
                        {
                          "id": "root/user-guide/shell-completion/shell-completion/troubleshooting/common-issues/zsh-insecure-directories-warning",
                          "label": "Zsh Insecure Directories Warning"
                        }
                      ]
                    }
                  ]
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/system-wide-installation",
                  "label": "System-Wide Installation",
                  "children": [
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/system-wide-installation/bash-(ubuntu/debian)",
                      "label": "Bash (Ubuntu/Debian)"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/system-wide-installation/bash-(rhel/centos/fedora)",
                      "label": "Bash (RHEL/CentOS/Fedora)"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/system-wide-installation/zsh",
                      "label": "Zsh"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/system-wide-installation/fish",
                      "label": "Fish"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/command-completion-options",
                  "label": "Command Completion Options",
                  "children": [
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/command-completion-options/complex-options",
                      "label": "Complex Options"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/command-completion-options/format-selection",
                      "label": "Format Selection"
                    },
                    {
                      "id": "root/user-guide/shell-completion/shell-completion/command-completion-options/shell-selection",
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
      "id": "root/reference",
      "label": "Reference",
      "children": [
        {
          "id": "root/reference/cli-reference",
          "label": "CLI Reference",
          "children": [
            {
              "id": "root/reference/cli-reference/cli-reference",
              "label": "CLI Reference",
              "children": [
                {
                  "id": "root/reference/cli-reference/cli-reference/command-overview",
                  "label": "Command Overview"
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/global-options",
                  "label": "Global Options"
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/visualize-command",
                  "label": "`visualize` Command",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/visualize-command/usage",
                      "label": "Usage"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/visualize-command/arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/visualize-command/options",
                      "label": "Options"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/visualize-command/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/export-command",
                  "label": "`export` Command",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/export-command/usage",
                      "label": "Usage"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/export-command/arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/export-command/options",
                      "label": "Options"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/export-command/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/compare-command",
                  "label": "`compare` Command",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/compare-command/usage",
                      "label": "Usage"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/compare-command/arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/compare-command/options",
                      "label": "Options"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/compare-command/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/completion-command",
                  "label": "`completion` Command",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/completion-command/usage",
                      "label": "Usage"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/completion-command/arguments",
                      "label": "Arguments"
                    },
                    {
                      "id": "root/reference/cli-reference/cli-reference/completion-command/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/version-command",
                  "label": "`version` Command",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/version-command/usage",
                      "label": "Usage"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "root/reference/api-reference",
          "label": "API Reference",
          "children": [
            {
              "id": "root/reference/api-reference/api-reference",
              "label": "API Reference",
              "children": [
                {
                  "id": "root/reference/api-reference/api-reference/core-module",
                  "label": "Core Module"
                },
                {
                  "id": "root/reference/api-reference/api-reference/exports-module",
                  "label": "Exports Module"
                },
                {
                  "id": "root/reference/api-reference/api-reference/compare-module",
                  "label": "Compare Module"
                },
                {
                  "id": "root/reference/api-reference/api-reference/jsx-export-module",
                  "label": "JSX Export Module"
                },
                {
                  "id": "root/reference/api-reference/api-reference/using-the-python-api-in-custom-scripts",
                  "label": "Using the Python API in Custom Scripts"
                },
                {
                  "id": "root/reference/api-reference/api-reference/api-extension-points",
                  "label": "API Extension Points"
                }
              ]
            }
          ]
        },
        {
          "id": "root/reference/export-formats",
          "label": "Export Formats",
          "children": [
            {
              "id": "root/reference/export-formats/export-formats",
              "label": "Export Formats",
              "children": [
                {
                  "id": "root/reference/export-formats/export-formats/available-formats",
                  "label": "Available Formats"
                },
                {
                  "id": "root/reference/export-formats/export-formats/basic-export-command",
                  "label": "Basic Export Command"
                },
                {
                  "id": "root/reference/export-formats/export-formats/exporting-to-multiple-formats",
                  "label": "Exporting to Multiple Formats"
                },
                {
                  "id": "root/reference/export-formats/export-formats/specifying-output-directory",
                  "label": "Specifying Output Directory"
                },
                {
                  "id": "root/reference/export-formats/export-formats/customizing-filename-prefix",
                  "label": "Customizing Filename Prefix"
                },
                {
                  "id": "root/reference/export-formats/export-formats/including-file-statistics",
                  "label": "Including File Statistics"
                },
                {
                  "id": "root/reference/export-formats/export-formats/format-details",
                  "label": "Format Details",
                  "children": [
                    {
                      "id": "root/reference/export-formats/export-formats/format-details/text-format-(txt)",
                      "label": "Text Format (TXT)"
                    },
                    {
                      "id": "root/reference/export-formats/export-formats/format-details/json-format",
                      "label": "JSON Format"
                    },
                    {
                      "id": "root/reference/export-formats/export-formats/format-details/html-format",
                      "label": "HTML Format"
                    },
                    {
                      "id": "root/reference/export-formats/export-formats/format-details/markdown-format-(md)",
                      "label": "Markdown Format (MD)"
                    },
                    {
                      "id": "root/reference/export-formats/export-formats/format-details/react-component-(jsx)",
                      "label": "React Component (JSX)"
                    },
                    {
                      "id": "root/reference/export-formats/export-formats/format-details/svg-format",
                      "label": "SVG Format"
                    }
                  ]
                },
                {
                  "id": "root/reference/export-formats/export-formats/using-the-react-component",
                  "label": "Using the React Component"
                },
                {
                  "id": "root/reference/export-formats/export-formats/export-with-filtering",
                  "label": "Export with Filtering"
                },
                {
                  "id": "root/reference/export-formats/export-formats/exporting-full-paths",
                  "label": "Exporting Full Paths"
                },
                {
                  "id": "root/reference/export-formats/export-formats/comparison-of-export-formats",
                  "label": "Comparison of Export Formats"
                }
              ]
            }
          ]
        },
        {
          "id": "root/reference/pattern-matching",
          "label": "Pattern Matching",
          "children": [
            {
              "id": "root/reference/pattern-matching/pattern-matching",
              "label": "Pattern Matching",
              "children": [
                {
                  "id": "root/reference/pattern-matching/pattern-matching/pattern-types",
                  "label": "Pattern Types"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/glob-patterns",
                  "label": "Glob Patterns",
                  "children": [
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/glob-patterns/glob-syntax",
                      "label": "Glob Syntax"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/glob-patterns/glob-examples",
                      "label": "Glob Examples"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/glob-patterns/using-glob-patterns",
                      "label": "Using Glob Patterns"
                    }
                  ]
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/regular-expressions",
                  "label": "Regular Expressions",
                  "children": [
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/regular-expressions/regex-syntax",
                      "label": "Regex Syntax"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/regular-expressions/regex-examples",
                      "label": "Regex Examples"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/regular-expressions/using-regex-patterns",
                      "label": "Using Regex Patterns"
                    }
                  ]
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/pattern-precedence",
                  "label": "Pattern Precedence"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/combining-include-and-exclude-patterns",
                  "label": "Combining Include and Exclude Patterns"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/pattern-matching-in-different-commands",
                  "label": "Pattern Matching in Different Commands"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples",
                  "label": "Advanced Pattern Examples",
                  "children": [
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples/show-only-source-code",
                      "label": "Show Only Source Code"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples/exclude-all-test-files",
                      "label": "Exclude All Test Files"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples/show-only-specific-file-types",
                      "label": "Show Only Specific File Types"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples/complex-filtering-with-regex",
                      "label": "Complex Filtering with Regex"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples/pattern-matching-with-file-statistics",
                      "label": "Pattern Matching with File Statistics"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/advanced-pattern-examples/filter-based-on-file-contents-(gitignore-style)",
                      "label": "Filter Based on File Contents (Gitignore Style)"
                    }
                  ]
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/performance-considerations",
                  "label": "Performance Considerations"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/common-use-cases",
                  "label": "Common Use Cases",
                  "children": [
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/common-use-cases/development-project",
                      "label": "Development Project"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/common-use-cases/documentation-project",
                      "label": "Documentation Project"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/common-use-cases/source-code-analysis",
                      "label": "Source Code Analysis"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/common-use-cases/backend-development",
                      "label": "Backend Development"
                    }
                  ]
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/troubleshooting-pattern-matching",
                  "label": "Troubleshooting Pattern Matching"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "root/examples",
      "label": "Examples",
      "children": [
        {
          "id": "root/examples/basic-examples",
          "label": "Basic Examples",
          "children": [
            {
              "id": "root/examples/basic-examples/basic-examples",
              "label": "Basic Examples",
              "children": [
                {
                  "id": "root/examples/basic-examples/basic-examples/simple-visualization",
                  "label": "Simple Visualization",
                  "children": [
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-visualization/viewing-the-current-directory",
                      "label": "Viewing the Current Directory"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-visualization/viewing-a-specific-directory",
                      "label": "Viewing a Specific Directory"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-visualization/limiting-directory-depth",
                      "label": "Limiting Directory Depth"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-visualization/showing-full-paths",
                      "label": "Showing Full Paths"
                    }
                  ]
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/file-statistics",
                  "label": "File Statistics",
                  "children": [
                    {
                      "id": "root/examples/basic-examples/basic-examples/file-statistics/showing-lines-of-code",
                      "label": "Showing Lines of Code"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/file-statistics/showing-file-sizes",
                      "label": "Showing File Sizes"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/file-statistics/showing-modification-times",
                      "label": "Showing Modification Times"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/file-statistics/combining-statistics",
                      "label": "Combining Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/simple-exclusions",
                  "label": "Simple Exclusions",
                  "children": [
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-exclusions/excluding-specific-directories",
                      "label": "Excluding Specific Directories"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-exclusions/excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-exclusions/combining-exclusions",
                      "label": "Combining Exclusions"
                    }
                  ]
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/basic-exports",
                  "label": "Basic Exports",
                  "children": [
                    {
                      "id": "root/examples/basic-examples/basic-examples/basic-exports/exporting-to-markdown",
                      "label": "Exporting to Markdown"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/basic-exports/exporting-to-multiple-formats",
                      "label": "Exporting to Multiple Formats"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/basic-exports/exporting-to-a-specific-directory",
                      "label": "Exporting to a Specific Directory"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/basic-exports/customizing-the-filename",
                      "label": "Customizing the Filename"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/basic-exports/exporting-with-statistics",
                      "label": "Exporting with Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/simple-comparisons",
                  "label": "Simple Comparisons",
                  "children": [
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-comparisons/comparing-two-directories",
                      "label": "Comparing Two Directories"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-comparisons/exporting-a-comparison",
                      "label": "Exporting a Comparison"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/simple-comparisons/comparing-with-statistics",
                      "label": "Comparing with Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/shell-completion",
                  "label": "Shell Completion",
                  "children": [
                    {
                      "id": "root/examples/basic-examples/basic-examples/shell-completion/generating-shell-completion-for-bash",
                      "label": "Generating Shell Completion for Bash"
                    },
                    {
                      "id": "root/examples/basic-examples/basic-examples/shell-completion/generating-shell-completion-for-zsh",
                      "label": "Generating Shell Completion for Zsh"
                    }
                  ]
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/version-information",
                  "label": "Version Information"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/next-steps",
                  "label": "Next Steps"
                }
              ]
            }
          ]
        },
        {
          "id": "root/examples/filtering-examples",
          "label": "Filtering Examples",
          "children": [
            {
              "id": "root/examples/filtering-examples/filtering-examples",
              "label": "Filtering Examples",
              "children": [
                {
                  "id": "root/examples/filtering-examples/filtering-examples/basic-exclusion-options",
                  "label": "Basic Exclusion Options",
                  "children": [
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/basic-exclusion-options/excluding-directories",
                      "label": "Excluding Directories"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/basic-exclusion-options/excluding-file-extensions",
                      "label": "Excluding File Extensions"
                    }
                  ]
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/pattern-based-filtering",
                  "label": "Pattern-Based Filtering",
                  "children": [
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/pattern-based-filtering/using-glob-patterns-(default)",
                      "label": "Using Glob Patterns (Default)"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/pattern-based-filtering/using-regular-expressions",
                      "label": "Using Regular Expressions"
                    }
                  ]
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/include-patterns",
                  "label": "Include Patterns"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/using-gitignore-files",
                  "label": "Using Gitignore Files"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/combining-filtering-methods",
                  "label": "Combining Filtering Methods"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/filter-order-of-precedence",
                  "label": "Filter Order of Precedence"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/language-specific-examples",
                  "label": "Language-Specific Examples",
                  "children": [
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-examples/python-project",
                      "label": "Python Project"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-examples/javascript/typescript-project",
                      "label": "JavaScript/TypeScript Project"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-examples/java/maven-project",
                      "label": "Java/Maven Project"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-examples/ruby-on-rails-project",
                      "label": "Ruby on Rails Project"
                    }
                  ]
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/task-specific-filtering",
                  "label": "Task-Specific Filtering",
                  "children": [
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/task-specific-filtering/code-review-focus",
                      "label": "Code Review Focus"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/task-specific-filtering/documentation-overview",
                      "label": "Documentation Overview"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/task-specific-filtering/security-audit",
                      "label": "Security Audit"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/task-specific-filtering/performance-analysis",
                      "label": "Performance Analysis"
                    }
                  ]
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/using-filters-with-export",
                  "label": "Using Filters with Export"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/using-filters-with-compare",
                  "label": "Using Filters with Compare"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples",
                  "label": "Advanced Pattern Examples",
                  "children": [
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples/frontend-files-only",
                      "label": "Frontend Files Only"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples/backend-files-only",
                      "label": "Backend Files Only"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples/configuration-files-only",
                      "label": "Configuration Files Only"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples/feature-specific-files",
                      "label": "Feature-Specific Files"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples/exclude-generated-code",
                      "label": "Exclude Generated Code"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/advanced-pattern-examples/focus-on-recently-modified-files",
                      "label": "Focus on Recently Modified Files"
                    }
                  ]
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/combining-with-file-statistics",
                  "label": "Combining with File Statistics"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/shell-script-for-filtered-analysis",
                  "label": "Shell Script for Filtered Analysis"
                }
              ]
            }
          ]
        },
        {
          "id": "root/examples/export-examples",
          "label": "Export Examples",
          "children": [
            {
              "id": "root/examples/export-examples/export-examples",
              "label": "Export Examples",
              "children": [
                {
                  "id": "root/examples/export-examples/export-examples/basic-export-examples",
                  "label": "Basic Export Examples",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-different-formats",
                      "label": "Exporting to Different Formats",
                      "children": [
                        {
                          "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-different-formats/markdown-export",
                          "label": "Markdown Export"
                        },
                        {
                          "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-different-formats/json-export",
                          "label": "JSON Export"
                        },
                        {
                          "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-different-formats/html-export",
                          "label": "HTML Export"
                        },
                        {
                          "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-different-formats/text-export",
                          "label": "Text Export"
                        },
                        {
                          "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-different-formats/react-component-export",
                          "label": "React Component Export"
                        }
                      ]
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/basic-export-examples/exporting-to-multiple-formats-simultaneously",
                      "label": "Exporting to Multiple Formats Simultaneously"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/including-file-statistics",
                  "label": "Including File Statistics",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/including-file-statistics/exporting-with-lines-of-code-statistics",
                      "label": "Exporting with Lines of Code Statistics"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/including-file-statistics/exporting-with-file-sizes",
                      "label": "Exporting with File Sizes"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/including-file-statistics/exporting-with-modification-times",
                      "label": "Exporting with Modification Times"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/including-file-statistics/combining-multiple-statistics",
                      "label": "Combining Multiple Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/customizing-export-output",
                  "label": "Customizing Export Output",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/customizing-export-output/custom-output-directory",
                      "label": "Custom Output Directory"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/customizing-export-output/custom-filename-prefix",
                      "label": "Custom Filename Prefix"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/customizing-export-output/combining-custom-directory-and-filename",
                      "label": "Combining Custom Directory and Filename"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/filtered-exports",
                  "label": "Filtered Exports",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/filtered-exports/exporting-with-directory-exclusions",
                      "label": "Exporting with Directory Exclusions"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/filtered-exports/exporting-with-file-extension-exclusions",
                      "label": "Exporting with File Extension Exclusions"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/filtered-exports/exporting-with-pattern-exclusions",
                      "label": "Exporting with Pattern Exclusions"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/filtered-exports/exporting-only-specific-files",
                      "label": "Exporting Only Specific Files"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/filtered-exports/exporting-with-gitignore-patterns",
                      "label": "Exporting with Gitignore Patterns"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/depth-limited-exports",
                  "label": "Depth-Limited Exports",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/depth-limited-exports/exporting-with-limited-depth",
                      "label": "Exporting with Limited Depth"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/depth-limited-exports/exporting-top-level-overview",
                      "label": "Exporting Top-Level Overview"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/full-path-exports",
                  "label": "Full Path Exports",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/full-path-exports/json-export-with-full-paths",
                      "label": "JSON Export with Full Paths"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/full-path-exports/markdown-export-with-full-paths",
                      "label": "Markdown Export with Full Paths"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/specific-project-exports",
                  "label": "Specific Project Exports",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/specific-project-exports/source-code-documentation-with-loc-stats",
                      "label": "Source Code Documentation with LOC Stats"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/specific-project-exports/project-overview-for-readme",
                      "label": "Project Overview for README"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/react-component-export-examples",
                  "label": "React Component Export Examples",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/react-component-export-examples/basic-react-component-export",
                      "label": "Basic React Component Export"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/react-component-export-examples/customized-react-component-with-statistics",
                      "label": "Customized React Component with Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/export-for-different-use-cases",
                  "label": "Export for Different Use Cases",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/export-for-different-use-cases/documentation-export-with-stats",
                      "label": "Documentation Export with Stats"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/export-for-different-use-cases/codebase-analysis-export",
                      "label": "Codebase Analysis Export"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/export-for-different-use-cases/website-integration-export",
                      "label": "Website Integration Export"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/batch-export-examples",
                  "label": "Batch Export Examples",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/batch-export-examples/multiple-export-configuration-script",
                      "label": "Multiple Export Configuration Script"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/batch-export-examples/project-subdirectory-exports-with-stats",
                      "label": "Project Subdirectory Exports with Stats"
                    }
                  ]
                },
                {
                  "id": "root/examples/export-examples/export-examples/combining-with-shell-commands",
                  "label": "Combining with Shell Commands",
                  "children": [
                    {
                      "id": "root/examples/export-examples/export-examples/combining-with-shell-commands/export-and-process-with-jq",
                      "label": "Export and Process with jq"
                    },
                    {
                      "id": "root/examples/export-examples/export-examples/combining-with-shell-commands/export-and-include-in-documentation",
                      "label": "Export and Include in Documentation"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "root/examples/compare-examples",
          "label": "Compare Examples",
          "children": [
            {
              "id": "root/examples/compare-examples/compare-examples",
              "label": "Compare Examples",
              "children": [
                {
                  "id": "root/examples/compare-examples/compare-examples/basic-comparison-examples",
                  "label": "Basic Comparison Examples",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/basic-comparison-examples/simple-directory-comparison",
                      "label": "Simple Directory Comparison"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/basic-comparison-examples/saving-comparison-as-html",
                      "label": "Saving Comparison as HTML"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/basic-comparison-examples/custom-output-location",
                      "label": "Custom Output Location"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/basic-comparison-examples/custom-filename",
                      "label": "Custom Filename"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/comparison-with-file-statistics",
                  "label": "Comparison with File Statistics",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/comparison-with-file-statistics/comparing-with-lines-of-code",
                      "label": "Comparing with Lines of Code"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/comparison-with-file-statistics/comparing-with-file-sizes",
                      "label": "Comparing with File Sizes"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/comparison-with-file-statistics/comparing-with-modification-times",
                      "label": "Comparing with Modification Times"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/comparison-with-file-statistics/combining-multiple-statistics",
                      "label": "Combining Multiple Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/filtered-comparisons",
                  "label": "Filtered Comparisons",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/filtered-comparisons/comparing-with-directory-exclusions",
                      "label": "Comparing with Directory Exclusions"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/filtered-comparisons/comparing-with-file-extension-exclusions",
                      "label": "Comparing with File Extension Exclusions"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/filtered-comparisons/comparing-with-pattern-exclusions",
                      "label": "Comparing with Pattern Exclusions"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/filtered-comparisons/focusing-on-specific-files",
                      "label": "Focusing on Specific Files"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/filtered-comparisons/comparing-with-gitignore-patterns",
                      "label": "Comparing with Gitignore Patterns"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/depth-limited-comparisons",
                  "label": "Depth-Limited Comparisons",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/depth-limited-comparisons/comparing-top-level-structure",
                      "label": "Comparing Top-Level Structure"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/depth-limited-comparisons/comparing-with-limited-depth",
                      "label": "Comparing with Limited Depth"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/full-path-comparisons",
                  "label": "Full Path Comparisons",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/full-path-comparisons/comparing-with-full-paths",
                      "label": "Comparing with Full Paths"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/real-world-use-cases",
                  "label": "Real-World Use Cases",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-use-cases/project-version-comparison-with-statistics",
                      "label": "Project Version Comparison with Statistics"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-use-cases/branch-comparison-with-statistics",
                      "label": "Branch Comparison with Statistics"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-use-cases/source-vs.-build-comparison-with-file-sizes",
                      "label": "Source vs. Build Comparison with File Sizes"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-use-cases/development-vs.-production-configuration-comparison",
                      "label": "Development vs. Production Configuration Comparison"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/specific-comparison-scenarios",
                  "label": "Specific Comparison Scenarios",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/specific-comparison-scenarios/code-library-upgrade-analysis",
                      "label": "Code Library Upgrade Analysis"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/specific-comparison-scenarios/project-fork-comparison",
                      "label": "Project Fork Comparison"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/specific-comparison-scenarios/backup-verification-with-file-sizes",
                      "label": "Backup Verification with File Sizes"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/specific-comparison-scenarios/framework-comparison-with-lines-of-code",
                      "label": "Framework Comparison with Lines of Code"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/combining-with-other-tools",
                  "label": "Combining with Other Tools",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/combining-with-other-tools/comparison-and-analysis-script",
                      "label": "Comparison and Analysis Script"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/combining-with-other-tools/continuous-integration-comparison-with-statistics",
                      "label": "Continuous Integration Comparison with Statistics"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/combining-with-other-tools/weekly-project-evolution-report",
                      "label": "Weekly Project Evolution Report"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "root/examples/advanced-examples",
          "label": "Advanced Examples",
          "children": [
            {
              "id": "root/examples/advanced-examples/advanced-examples",
              "label": "Advanced Examples",
              "children": [
                {
                  "id": "root/examples/advanced-examples/advanced-examples/working-with-file-statistics",
                  "label": "Working with File Statistics",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/working-with-file-statistics/finding-large-files-across-projects",
                      "label": "Finding Large Files Across Projects"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/working-with-file-statistics/lines-of-code-analysis-with-filtering",
                      "label": "Lines of Code Analysis with Filtering"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/working-with-file-statistics/finding-recently-modified-code",
                      "label": "Finding Recently Modified Code"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/combining-commands-with-shell-scripts",
                  "label": "Combining Commands with Shell Scripts",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/combining-commands-with-shell-scripts/batch-processing-multiple-directories",
                      "label": "Batch Processing Multiple Directories"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/combining-commands-with-shell-scripts/project-report-generator",
                      "label": "Project Report Generator"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/integration-with-other-tools",
                  "label": "Integration with Other Tools",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/integration-with-other-tools/git-hook-for-project-structure-documentation",
                      "label": "Git Hook for Project Structure Documentation"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/integration-with-other-tools/using-with-continuous-integration",
                      "label": "Using with Continuous Integration"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/integration-with-other-tools/mkdocs-integration-with-statistics",
                      "label": "MkDocs Integration with Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/using-with-git-repositories",
                  "label": "Using with Git Repositories",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/using-with-git-repositories/comparing-git-branches-with-statistics",
                      "label": "Comparing Git Branches with Statistics"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/using-with-git-repositories/analyzing-git-repository-structure-with-statistics",
                      "label": "Analyzing Git Repository Structure with Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/limiting-directory-depth-with-file-statistics",
                  "label": "Limiting Directory Depth with File Statistics",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/limiting-directory-depth-with-file-statistics/visualizing-deep-directories-incrementally-with-statistics",
                      "label": "Visualizing Deep Directories Incrementally with Statistics"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/limiting-directory-depth-with-file-statistics/creating-a-multi-level-project-map-with-statistics",
                      "label": "Creating a Multi-Level Project Map with Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/react-component-integration-with-statistics",
                  "label": "React Component Integration with Statistics",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/react-component-integration-with-statistics/creating-a-project-explorer-with-file-statistics",
                      "label": "Creating a Project Explorer with File Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/using-regex-patterns-with-file-statistics",
                  "label": "Using Regex Patterns with File Statistics",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/using-regex-patterns-with-file-statistics/finding-complex-files-by-size",
                      "label": "Finding Complex Files by Size"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/using-regex-patterns-with-file-statistics/finding-files-by-loc-and-type",
                      "label": "Finding Files by LOC and Type"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/integration-with-analysis-tools",
                  "label": "Integration with Analysis Tools",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/integration-with-analysis-tools/structure-analysis-with-loc-statistics",
                      "label": "Structure Analysis with LOC Statistics"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/using-with-ignore-files-and-file-statistics",
                  "label": "Using with Ignore Files and File Statistics",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/using-with-ignore-files-and-file-statistics/custom-ignore-file-for-documentation-with-statistics",
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
      "id": "root/advanced",
      "label": "Advanced",
      "children": [
        {
          "id": "root/advanced/integration",
          "label": "Integration",
          "children": [
            {
              "id": "root/advanced/integration/integration-with-other-tools",
              "label": "Integration with Other Tools",
              "children": [
                {
                  "id": "root/advanced/integration/integration-with-other-tools/using-with-git-repositories",
                  "label": "Using with Git Repositories",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/using-with-git-repositories/gitignore-integration",
                      "label": "Gitignore Integration"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/using-with-git-repositories/pre-commit-framework",
                      "label": "Pre-commit Framework"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/using-with-git-repositories/manual-git-hooks",
                      "label": "Manual Git Hooks"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/using-with-git-repositories/git-workflow-scripts",
                      "label": "Git Workflow Scripts"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/processing-json-exports-with-jq",
                  "label": "Processing JSON Exports with jq",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/processing-json-exports-with-jq/count-files-by-extension",
                      "label": "Count Files by Extension"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/processing-json-exports-with-jq/find-largest-files",
                      "label": "Find Largest Files"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/processing-json-exports-with-jq/find-files-with-most-lines-of-code",
                      "label": "Find Files with Most Lines of Code"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/processing-json-exports-with-jq/analyze-code-distribution-by-directory",
                      "label": "Analyze Code Distribution by Directory"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/programmatic-use-with-python",
                  "label": "Programmatic Use with Python",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/programmatic-use-with-python/basic-directory-analysis",
                      "label": "Basic Directory Analysis"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/programmatic-use-with-python/custom-file-analysis",
                      "label": "Custom File Analysis"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/web-application-integration",
                  "label": "Web Application Integration",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/web-application-integration/using-the-react-component-export",
                      "label": "Using the React Component Export"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/web-application-integration/custom-api-with-flask",
                      "label": "Custom API with Flask"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/continuous-integration-integration",
                  "label": "Continuous Integration Integration",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/continuous-integration-integration/github-actions-example",
                      "label": "GitHub Actions Example"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/continuous-integration-integration/gitlab-ci-example",
                      "label": "GitLab CI Example"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/documentation-tools-integration",
                  "label": "Documentation Tools Integration",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/documentation-tools-integration/mkdocs-integration",
                      "label": "MkDocs Integration"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/documentation-tools-integration/sphinx-integration",
                      "label": "Sphinx Integration"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/shell-script-integration",
                  "label": "Shell Script Integration",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/shell-script-integration/batch-processing-multiple-directories",
                      "label": "Batch Processing Multiple Directories"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/shell-script-integration/weekly-project-evolution-report",
                      "label": "Weekly Project Evolution Report"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/using-with-static-analysis-tools",
                  "label": "Using with Static Analysis Tools"
                }
              ]
            }
          ]
        },
        {
          "id": "root/advanced/development",
          "label": "Development",
          "children": [
            {
              "id": "root/advanced/development/development-guide",
              "label": "Development Guide",
              "children": [
                {
                  "id": "root/advanced/development/development-guide/setting-up-development-environment",
                  "label": "Setting Up Development Environment",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/setting-up-development-environment/prerequisites",
                      "label": "Prerequisites"
                    },
                    {
                      "id": "root/advanced/development/development-guide/setting-up-development-environment/clone-the-repository",
                      "label": "Clone the Repository"
                    },
                    {
                      "id": "root/advanced/development/development-guide/setting-up-development-environment/create-a-virtual-environment",
                      "label": "Create a Virtual Environment"
                    },
                    {
                      "id": "root/advanced/development/development-guide/setting-up-development-environment/install-development-dependencies",
                      "label": "Install Development Dependencies"
                    },
                    {
                      "id": "root/advanced/development/development-guide/setting-up-development-environment/install-pre-commit-hooks",
                      "label": "Install Pre-commit Hooks"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/project-structure",
                  "label": "Project Structure",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/project-structure/module-responsibilities",
                      "label": "Module Responsibilities"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/development-workflow",
                  "label": "Development Workflow",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/development-workflow/making-changes",
                      "label": "Making Changes"
                    },
                    {
                      "id": "root/advanced/development/development-guide/development-workflow/code-style",
                      "label": "Code Style"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/adding-a-new-feature",
                  "label": "Adding a New Feature",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/adding-a-new-feature/adding-a-new-command",
                      "label": "Adding a New Command"
                    },
                    {
                      "id": "root/advanced/development/development-guide/adding-a-new-feature/adding-a-new-export-format",
                      "label": "Adding a New Export Format"
                    },
                    {
                      "id": "root/advanced/development/development-guide/adding-a-new-feature/adding-new-file-statistics",
                      "label": "Adding New File Statistics"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/testing",
                  "label": "Testing",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/testing/basic-testing",
                      "label": "Basic Testing"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/debugging",
                  "label": "Debugging",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/debugging/verbose-output",
                      "label": "Verbose Output"
                    },
                    {
                      "id": "root/advanced/development/development-guide/debugging/using-a-debugger",
                      "label": "Using a Debugger"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/documentation",
                  "label": "Documentation",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/documentation/docstrings",
                      "label": "Docstrings"
                    },
                    {
                      "id": "root/advanced/development/development-guide/documentation/command-line-help",
                      "label": "Command-Line Help"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/performance-considerations",
                  "label": "Performance Considerations",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/performance-considerations/large-directory-structures",
                      "label": "Large Directory Structures"
                    },
                    {
                      "id": "root/advanced/development/development-guide/performance-considerations/profiling",
                      "label": "Profiling"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/extending-pattern-matching",
                  "label": "Extending Pattern Matching"
                },
                {
                  "id": "root/advanced/development/development-guide/release-process",
                  "label": "Release Process",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/release-process/version-numbering",
                      "label": "Version Numbering"
                    },
                    {
                      "id": "root/advanced/development/development-guide/release-process/creating-a-release",
                      "label": "Creating a Release"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/common-development-tasks",
                  "label": "Common Development Tasks",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/common-development-tasks/adding-a-new-command-line-option",
                      "label": "Adding a New Command-Line Option"
                    },
                    {
                      "id": "root/advanced/development/development-guide/common-development-tasks/improving-colorization",
                      "label": "Improving Colorization"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "id": "root/advanced/testing",
          "label": "Testing",
          "children": [
            {
              "id": "root/advanced/testing/testing-guide",
              "label": "Testing Guide",
              "children": [
                {
                  "id": "root/advanced/testing/testing-guide/testing-framework",
                  "label": "Testing Framework"
                },
                {
                  "id": "root/advanced/testing/testing-guide/running-tests",
                  "label": "Running Tests",
                  "children": [
                    {
                      "id": "root/advanced/testing/testing-guide/running-tests/basic-test-commands",
                      "label": "Basic Test Commands"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/running-tests/coverage",
                      "label": "Coverage"
                    }
                  ]
                },
                {
                  "id": "root/advanced/testing/testing-guide/test-organization",
                  "label": "Test Organization"
                },
                {
                  "id": "root/advanced/testing/testing-guide/writing-tests",
                  "label": "Writing Tests",
                  "children": [
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/test-structure",
                      "label": "Test Structure"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/testing-directory-operations",
                      "label": "Testing Directory Operations"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/testing-cli-commands",
                      "label": "Testing CLI Commands"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/testing-export-formats",
                      "label": "Testing Export Formats"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/testing-with-parametrization",
                      "label": "Testing with Parametrization"
                    }
                  ]
                },
                {
                  "id": "root/advanced/testing/testing-guide/test-fixtures",
                  "label": "Test Fixtures"
                },
                {
                  "id": "root/advanced/testing/testing-guide/mocking",
                  "label": "Mocking"
                },
                {
                  "id": "root/advanced/testing/testing-guide/testing-pattern-matching",
                  "label": "Testing Pattern Matching"
                },
                {
                  "id": "root/advanced/testing/testing-guide/testing-statistics",
                  "label": "Testing Statistics"
                },
                {
                  "id": "root/advanced/testing/testing-guide/testing-cli-options",
                  "label": "Testing CLI Options"
                },
                {
                  "id": "root/advanced/testing/testing-guide/debugging-tests",
                  "label": "Debugging Tests"
                },
                {
                  "id": "root/advanced/testing/testing-guide/testing-complex-directory-structures",
                  "label": "Testing Complex Directory Structures"
                },
                {
                  "id": "root/advanced/testing/testing-guide/testing-edge-cases",
                  "label": "Testing Edge Cases"
                },
                {
                  "id": "root/advanced/testing/testing-guide/continuous-integration",
                  "label": "Continuous Integration"
                },
                {
                  "id": "root/advanced/testing/testing-guide/test-driven-development",
                  "label": "Test-Driven Development"
                },
                {
                  "id": "root/advanced/testing/testing-guide/test-best-practices",
                  "label": "Test Best Practices"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "root/contributing",
      "label": "Contributing",
      "children": [
        {
          "id": "root/contributing/contributing-to-recursivist",
          "label": "Contributing to Recursivist",
          "children": [
            {
              "id": "root/contributing/contributing-to-recursivist/table-of-contents",
              "label": "Table of Contents"
            },
            {
              "id": "root/contributing/contributing-to-recursivist/code-of-conduct",
              "label": "Code of Conduct"
            },
            {
              "id": "root/contributing/contributing-to-recursivist/getting-started",
              "label": "Getting Started",
              "children": [
                {
                  "id": "root/contributing/contributing-to-recursivist/getting-started/setting-up-your-development-environment",
                  "label": "Setting Up Your Development Environment"
                }
              ]
            },
            {
              "id": "root/contributing/contributing-to-recursivist/development-workflow",
              "label": "Development Workflow",
              "children": [
                {
                  "id": "root/contributing/contributing-to-recursivist/development-workflow/creating-a-branch",
                  "label": "Creating a Branch"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/development-workflow/making-changes",
                  "label": "Making Changes"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/development-workflow/testing-your-changes",
                  "label": "Testing Your Changes"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/development-workflow/submitting-a-pull-request",
                  "label": "Submitting a Pull Request"
                }
              ]
            },
            {
              "id": "root/contributing/contributing-to-recursivist/coding-standards",
              "label": "Coding Standards",
              "children": [
                {
                  "id": "root/contributing/contributing-to-recursivist/coding-standards/code-style",
                  "label": "Code Style"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/coding-standards/documentation",
                  "label": "Documentation"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/coding-standards/type-annotations",
                  "label": "Type Annotations"
                }
              ]
            },
            {
              "id": "root/contributing/contributing-to-recursivist/testing",
              "label": "Testing",
              "children": [
                {
                  "id": "root/contributing/contributing-to-recursivist/testing/running-tests",
                  "label": "Running Tests"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/testing/writing-tests",
                  "label": "Writing Tests"
                }
              ]
            },
            {
              "id": "root/contributing/contributing-to-recursivist/bug-reports-and-feature-requests",
              "label": "Bug Reports and Feature Requests",
              "children": [
                {
                  "id": "root/contributing/contributing-to-recursivist/bug-reports-and-feature-requests/reporting-bugs",
                  "label": "Reporting Bugs"
                },
                {
                  "id": "root/contributing/contributing-to-recursivist/bug-reports-and-feature-requests/suggesting-features",
                  "label": "Suggesting Features"
                }
              ]
            },
            {
              "id": "root/contributing/contributing-to-recursivist/release-process",
              "label": "Release Process"
            },
            {
              "id": "root/contributing/contributing-to-recursivist/community",
              "label": "Community"
            }
          ]
        }
      ]
    },
    {
      "id": "root/sitemap",
      "label": "Sitemap",
      "children": [
        {
          "id": "root/sitemap/sitemap",
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

    const NH = 38,
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
      n._w = Math.max(110, n.label.length * 7 + 36);
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
      const cx = x + node._w + LR_HGAP;

      for (const c of node.children) {
        const h = lrH(c);
        lrPlace(c, cx, cy + h / 2);
        cy += h + LR_VGAP;
      }
    }

    function tbW(node) {
      if (collapsed.has(node.id) || !node.children?.length)
        return node._w;

      const w =
        node.children.reduce((s, c) => s + tbW(c), 0) +
        (node.children.length - 1) * TB_XGAP;

      return Math.max(node._w, w);
    }

    function tbPlace(node, x, y) {
      pos[node.id] = { x, y };

      if (collapsed.has(node.id) || !node.children?.length)
        return;

      const total =
        node.children.reduce((s, c) => s + tbW(c), 0) +
        (node.children.length - 1) * TB_XGAP;

      const parentCenterX = x + node._w / 2;
      let cx = parentCenterX - total / 2;
      const cy = y + NH + TB_YGAP;

      for (const c of node.children) {
        const w = tbW(c);
        tbPlace(c, cx + w / 2 - c._w / 2, cy);
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

    function lrCurve(p, c) {
      const startX = pos[p.id].x + p._w;
      const startY = pos[p.id].y;
      const endX = pos[c.id].x;
      const endY = pos[c.id].y;
      const mx = startX + (endX - startX) * 0.55;
      return `M${startX},${startY} C${mx},${startY} ${mx},${endY} ${endX},${endY}`;
    }

    function tbCurve(p, c) {
      const startX = pos[p.id].x + p._w / 2;
      const startY = pos[p.id].y + NH / 2;
      const endX = pos[c.id].x + c._w / 2;
      const endY = pos[c.id].y - NH / 2;
      const my = startY + (endY - startY) * 0.55;
      return `M${startX},${startY} C${startX},${my} ${endX},${my} ${endX},${endY}`;
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
                ? lrCurve(node, c)
                : tbCurve(node, c);

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
            width: node._w,
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
            x: x + node._w / 2,
            y,
          },
          g
        ).textContent = node.label;

        if (hasKids) {
          const [tx, ty] =
            orientation === "LR"
              ? [x + node._w - 2, y]
              : [x + node._w / 2, y + NH / 2 + 2];

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
