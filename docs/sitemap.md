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
                  "id": "root/getting-started/installation/installation/verifying-the-installation",
                  "label": "Verifying the Installation"
                },
                {
                  "id": "root/getting-started/installation/installation/nerd-font-icons-(optional)",
                  "label": "Nerd Font Icons (Optional)"
                },
                {
                  "id": "root/getting-started/installation/installation/terminal-compatibility",
                  "label": "Terminal Compatibility"
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
                  "id": "root/getting-started/quick-start/quick-start-guide/visualize-a-directory",
                  "label": "Visualize a Directory"
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/show-file-statistics",
                  "label": "Show File Statistics"
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/show-git-status",
                  "label": "Show Git Status"
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/export-a-directory-structure",
                  "label": "Export a Directory Structure"
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/compare-two-directories",
                  "label": "Compare Two Directories"
                },
                {
                  "id": "root/getting-started/quick-start/quick-start-guide/common-options",
                  "label": "Common Options"
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
                  "id": "root/user-guide/basic-usage/basic-usage/getting-help",
                  "label": "Getting Help"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/default-behavior",
                  "label": "Default Behavior"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/icon-styles",
                  "label": "Icon Styles"
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
                      "id": "root/user-guide/basic-usage/basic-usage/common-options/verbose-output",
                      "label": "Verbose Output"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/file-statistics",
                  "label": "File Statistics"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/grouping-by-name-similarity",
                  "label": "Grouping by Name Similarity"
                },
                {
                  "id": "root/user-guide/basic-usage/basic-usage/pattern-filtering",
                  "label": "Pattern Filtering"
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
                  "id": "root/user-guide/visualization/visualization/color-coding",
                  "label": "Color Coding"
                },
                {
                  "id": "root/user-guide/visualization/visualization/icon-styles",
                  "label": "Icon Styles"
                },
                {
                  "id": "root/user-guide/visualization/visualization/file-statistics",
                  "label": "File Statistics",
                  "children": [
                    {
                      "id": "root/user-guide/visualization/visualization/file-statistics/lines-of-code",
                      "label": "Lines of Code"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/file-statistics/file-sizes",
                      "label": "File Sizes"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/file-statistics/modification-times",
                      "label": "Modification Times"
                    },
                    {
                      "id": "root/user-guide/visualization/visualization/file-statistics/combining-statistics",
                      "label": "Combining Statistics"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/visualization/visualization/grouping-by-name-similarity",
                  "label": "Grouping by Name Similarity"
                },
                {
                  "id": "root/user-guide/visualization/visualization/git-status",
                  "label": "Git Status"
                },
                {
                  "id": "root/user-guide/visualization/visualization/directory-depth-control",
                  "label": "Directory Depth Control"
                },
                {
                  "id": "root/user-guide/visualization/visualization/full-path-display",
                  "label": "Full Path Display"
                },
                {
                  "id": "root/user-guide/visualization/visualization/filtering",
                  "label": "Filtering"
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
                  "id": "root/user-guide/export/export/basic-usage",
                  "label": "Basic Usage"
                },
                {
                  "id": "root/user-guide/export/export/available-formats",
                  "label": "Available Formats"
                },
                {
                  "id": "root/user-guide/export/export/multiple-formats-at-once",
                  "label": "Multiple Formats at Once"
                },
                {
                  "id": "root/user-guide/export/export/output-location-and-filename",
                  "label": "Output Location and Filename"
                },
                {
                  "id": "root/user-guide/export/export/file-statistics",
                  "label": "File Statistics"
                },
                {
                  "id": "root/user-guide/export/export/git-status",
                  "label": "Git Status"
                },
                {
                  "id": "root/user-guide/export/export/icon-style",
                  "label": "Icon Style"
                },
                {
                  "id": "root/user-guide/export/export/filtering-and-depth",
                  "label": "Filtering and Depth"
                },
                {
                  "id": "root/user-guide/export/export/format-details",
                  "label": "Format Details",
                  "children": [
                    {
                      "id": "root/user-guide/export/export/format-details/text-(.txt)",
                      "label": "Text (`.txt`)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-details/json-(.json)",
                      "label": "JSON (`.json`)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-details/html-(.html)",
                      "label": "HTML (`.html`)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-details/markdown-(.md)",
                      "label": "Markdown (`.md`)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-details/react-component-(.jsx)",
                      "label": "React Component (`.jsx`)"
                    },
                    {
                      "id": "root/user-guide/export/export/format-details/svg-(.svg)",
                      "label": "SVG (`.svg`)"
                    }
                  ]
                },
                {
                  "id": "root/user-guide/export/export/using-the-react-component",
                  "label": "Using the React Component"
                },
                {
                  "id": "root/user-guide/export/export/examples",
                  "label": "Examples"
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
                  "id": "root/user-guide/compare/compare/reading-the-output",
                  "label": "Reading the Output"
                },
                {
                  "id": "root/user-guide/compare/compare/file-statistics",
                  "label": "File Statistics"
                },
                {
                  "id": "root/user-guide/compare/compare/saving-as-html",
                  "label": "Saving as HTML"
                },
                {
                  "id": "root/user-guide/compare/compare/filtering-and-depth",
                  "label": "Filtering and Depth"
                },
                {
                  "id": "root/user-guide/compare/compare/use-cases",
                  "label": "Use Cases"
                },
                {
                  "id": "root/user-guide/compare/compare/html-output",
                  "label": "HTML Output"
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
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/the-four-filtering-mechanisms",
                  "label": "The Four Filtering Mechanisms"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/directory-exclusion",
                  "label": "Directory Exclusion"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/extension-exclusion",
                  "label": "Extension Exclusion"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/include-and-exclude-patterns",
                  "label": "Include and Exclude Patterns"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/ignore-files",
                  "label": "Ignore Files"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/order-of-precedence",
                  "label": "Order of Precedence"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/combining-filters",
                  "label": "Combining Filters"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/same-behavior-across-commands",
                  "label": "Same Behavior Across Commands"
                },
                {
                  "id": "root/user-guide/pattern-filtering/pattern-filtering/examples",
                  "label": "Examples"
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
                  "id": "root/user-guide/shell-completion/shell-completion/recommended:-built-in-installer",
                  "label": "Recommended: Built-in Installer"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/the-completion-command",
                  "label": "The `completion` Command"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/using-completion",
                  "label": "Using Completion"
                },
                {
                  "id": "root/user-guide/shell-completion/shell-completion/troubleshooting",
                  "label": "Troubleshooting"
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
                  "id": "root/reference/cli-reference/cli-reference/commands",
                  "label": "Commands"
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/shared-options",
                  "label": "Shared Options"
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/visualize",
                  "label": "`visualize`",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/visualize/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/export",
                  "label": "`export`",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/export/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/compare",
                  "label": "`compare`",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/compare/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/config",
                  "label": "`config`",
                  "children": [
                    {
                      "id": "root/reference/cli-reference/cli-reference/config/examples",
                      "label": "Examples"
                    }
                  ]
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/completion",
                  "label": "`completion`"
                },
                {
                  "id": "root/reference/cli-reference/cli-reference/version",
                  "label": "`version`"
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
                  "id": "root/reference/api-reference/api-reference/module-overview",
                  "label": "Module Overview"
                },
                {
                  "id": "root/reference/api-reference/api-reference/the-structure-dictionary",
                  "label": "The Structure Dictionary",
                  "children": [
                    {
                      "id": "root/reference/api-reference/api-reference/the-structure-dictionary/fileentry",
                      "label": "FileEntry"
                    }
                  ]
                },
                {
                  "id": "root/reference/api-reference/api-reference/scanner",
                  "label": "Scanner"
                },
                {
                  "id": "root/reference/api-reference/api-reference/tree-rendering",
                  "label": "Tree Rendering"
                },
                {
                  "id": "root/reference/api-reference/api-reference/exporters",
                  "label": "Exporters"
                },
                {
                  "id": "root/reference/api-reference/api-reference/compare",
                  "label": "Compare"
                },
                {
                  "id": "root/reference/api-reference/api-reference/filtering",
                  "label": "Filtering"
                },
                {
                  "id": "root/reference/api-reference/api-reference/sorting",
                  "label": "Sorting"
                },
                {
                  "id": "root/reference/api-reference/api-reference/metrics",
                  "label": "Metrics"
                },
                {
                  "id": "root/reference/api-reference/api-reference/colors",
                  "label": "Colors"
                },
                {
                  "id": "root/reference/api-reference/api-reference/icons",
                  "label": "Icons"
                },
                {
                  "id": "root/reference/api-reference/api-reference/git-status",
                  "label": "Git Status"
                },
                {
                  "id": "root/reference/api-reference/api-reference/configuration",
                  "label": "Configuration"
                },
                {
                  "id": "root/reference/api-reference/api-reference/example:-custom-analysis-script",
                  "label": "Example: Custom Analysis Script"
                },
                {
                  "id": "root/reference/api-reference/api-reference/extending-recursivist",
                  "label": "Extending Recursivist"
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
                  "id": "root/reference/export-formats/export-formats/basic-usage",
                  "label": "Basic Usage"
                },
                {
                  "id": "root/reference/export-formats/export-formats/text-(.txt)",
                  "label": "Text (`.txt`)"
                },
                {
                  "id": "root/reference/export-formats/export-formats/json-(.json)",
                  "label": "JSON (`.json`)"
                },
                {
                  "id": "root/reference/export-formats/export-formats/html-(.html)",
                  "label": "HTML (`.html`)"
                },
                {
                  "id": "root/reference/export-formats/export-formats/markdown-(.md)",
                  "label": "Markdown (`.md`)"
                },
                {
                  "id": "root/reference/export-formats/export-formats/react-component-(.jsx)",
                  "label": "React Component (`.jsx`)"
                },
                {
                  "id": "root/reference/export-formats/export-formats/svg-(.svg)",
                  "label": "SVG (`.svg`)"
                },
                {
                  "id": "root/reference/export-formats/export-formats/using-the-react-component",
                  "label": "Using the React Component"
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
                  "id": "root/reference/pattern-matching/pattern-matching/what-patterns-match",
                  "label": "What Patterns Match"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/glob-patterns",
                  "label": "Glob Patterns",
                  "children": [
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/glob-patterns/syntax",
                      "label": "Syntax"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/glob-patterns/examples",
                      "label": "Examples"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/glob-patterns/usage",
                      "label": "Usage"
                    }
                  ]
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/regular-expressions",
                  "label": "Regular Expressions",
                  "children": [
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/regular-expressions/common-syntax",
                      "label": "Common Syntax"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/regular-expressions/examples",
                      "label": "Examples"
                    },
                    {
                      "id": "root/reference/pattern-matching/pattern-matching/regular-expressions/usage",
                      "label": "Usage"
                    }
                  ]
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/precedence",
                  "label": "Precedence"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/performance",
                  "label": "Performance"
                },
                {
                  "id": "root/reference/pattern-matching/pattern-matching/troubleshooting",
                  "label": "Troubleshooting"
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
                  "id": "root/examples/basic-examples/basic-examples/visualization",
                  "label": "Visualization"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/file-statistics",
                  "label": "File Statistics"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/git-status",
                  "label": "Git Status"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/exclusions",
                  "label": "Exclusions"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/exports",
                  "label": "Exports"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/comparisons",
                  "label": "Comparisons"
                },
                {
                  "id": "root/examples/basic-examples/basic-examples/configuration-and-version",
                  "label": "Configuration and Version"
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
                  "id": "root/examples/filtering-examples/filtering-examples/excluding-directories-and-extensions",
                  "label": "Excluding Directories and Extensions"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/glob-patterns",
                  "label": "Glob Patterns"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/regular-expressions",
                  "label": "Regular Expressions"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/include-patterns",
                  "label": "Include Patterns"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/ignore-files",
                  "label": "Ignore Files"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/combining-filters",
                  "label": "Combining Filters"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/language-specific-recipes",
                  "label": "Language-Specific Recipes",
                  "children": [
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-recipes/python",
                      "label": "Python"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-recipes/javascript-/-typescript",
                      "label": "JavaScript / TypeScript"
                    },
                    {
                      "id": "root/examples/filtering-examples/filtering-examples/language-specific-recipes/java-/-maven",
                      "label": "Java / Maven"
                    }
                  ]
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/filtering-with-statistics",
                  "label": "Filtering with Statistics"
                },
                {
                  "id": "root/examples/filtering-examples/filtering-examples/filtering-in-export-and-compare",
                  "label": "Filtering in Export and Compare"
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
                  "id": "root/examples/export-examples/export-examples/exporting-to-each-format",
                  "label": "Exporting to Each Format"
                },
                {
                  "id": "root/examples/export-examples/export-examples/statistics-in-exports",
                  "label": "Statistics in Exports"
                },
                {
                  "id": "root/examples/export-examples/export-examples/output-location-and-filename",
                  "label": "Output Location and Filename"
                },
                {
                  "id": "root/examples/export-examples/export-examples/filtered-and-depth-limited-exports",
                  "label": "Filtered and Depth-Limited Exports"
                },
                {
                  "id": "root/examples/export-examples/export-examples/react-component-exports",
                  "label": "React Component Exports"
                },
                {
                  "id": "root/examples/export-examples/export-examples/processing-json-with-jq",
                  "label": "Processing JSON with jq"
                },
                {
                  "id": "root/examples/export-examples/export-examples/including-a-structure-in-documentation",
                  "label": "Including a Structure in Documentation"
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
                  "id": "root/examples/compare-examples/compare-examples/basic-comparisons",
                  "label": "Basic Comparisons"
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/comparisons-with-statistics",
                  "label": "Comparisons with Statistics"
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/filtered-comparisons",
                  "label": "Filtered Comparisons"
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/real-world-uses",
                  "label": "Real-World Uses",
                  "children": [
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-uses/compare-two-versions",
                      "label": "Compare Two Versions"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-uses/compare-two-git-branches",
                      "label": "Compare Two Git Branches"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-uses/source-vs.-build",
                      "label": "Source vs. Build"
                    },
                    {
                      "id": "root/examples/compare-examples/compare-examples/real-world-uses/backup-verification",
                      "label": "Backup Verification"
                    }
                  ]
                },
                {
                  "id": "root/examples/compare-examples/compare-examples/in-continuous-integration",
                  "label": "In Continuous Integration"
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
                  "id": "root/examples/advanced-examples/advanced-examples/codebase-analysis-with-jq",
                  "label": "Codebase Analysis with jq"
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/focusing-on-recent-or-similar-files",
                  "label": "Focusing on Recent or Similar Files"
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/keeping-structure-docs-up-to-date",
                  "label": "Keeping Structure Docs Up to Date",
                  "children": [
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/keeping-structure-docs-up-to-date/pre-commit-framework",
                      "label": "Pre-commit Framework"
                    },
                    {
                      "id": "root/examples/advanced-examples/advanced-examples/keeping-structure-docs-up-to-date/manual-git-hook",
                      "label": "Manual Git Hook"
                    }
                  ]
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/continuous-integration",
                  "label": "Continuous Integration"
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/multi-level-project-map",
                  "label": "Multi-Level Project Map"
                },
                {
                  "id": "root/examples/advanced-examples/advanced-examples/embedding-a-react-component",
                  "label": "Embedding a React Component"
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
                  "id": "root/advanced/integration/integration-with-other-tools/git",
                  "label": "Git",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/git/use-your-.gitignore",
                      "label": "Use Your `.gitignore`"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/git/pre-commit-framework",
                      "label": "Pre-commit Framework"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/git/manual-git-hook",
                      "label": "Manual Git Hook"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/processing-json-with-jq",
                  "label": "Processing JSON with jq"
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/python",
                  "label": "Python",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/python/serving-structures-from-flask",
                      "label": "Serving Structures from Flask"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/web-applications",
                  "label": "Web Applications"
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/continuous-integration",
                  "label": "Continuous Integration",
                  "children": [
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/continuous-integration/github-actions",
                      "label": "GitHub Actions"
                    },
                    {
                      "id": "root/advanced/integration/integration-with-other-tools/continuous-integration/gitlab-ci",
                      "label": "GitLab CI"
                    }
                  ]
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/documentation-tools",
                  "label": "Documentation Tools"
                },
                {
                  "id": "root/advanced/integration/integration-with-other-tools/shell-automation",
                  "label": "Shell Automation"
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
                  "id": "root/advanced/development/development-guide/setting-up-a-development-environment",
                  "label": "Setting Up a Development Environment",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/setting-up-a-development-environment/prerequisites",
                      "label": "Prerequisites"
                    },
                    {
                      "id": "root/advanced/development/development-guide/setting-up-a-development-environment/clone-and-install",
                      "label": "Clone and Install"
                    },
                    {
                      "id": "root/advanced/development/development-guide/setting-up-a-development-environment/install-pre-commit-hooks",
                      "label": "Install Pre-commit Hooks"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/project-structure",
                  "label": "Project Structure"
                },
                {
                  "id": "root/advanced/development/development-guide/development-workflow",
                  "label": "Development Workflow"
                },
                {
                  "id": "root/advanced/development/development-guide/code-style-and-checks",
                  "label": "Code Style and Checks"
                },
                {
                  "id": "root/advanced/development/development-guide/extending-recursivist",
                  "label": "Extending Recursivist",
                  "children": [
                    {
                      "id": "root/advanced/development/development-guide/extending-recursivist/add-a-new-command",
                      "label": "Add a New Command"
                    },
                    {
                      "id": "root/advanced/development/development-guide/extending-recursivist/add-a-new-export-format",
                      "label": "Add a New Export Format"
                    },
                    {
                      "id": "root/advanced/development/development-guide/extending-recursivist/add-a-new-file-statistic",
                      "label": "Add a New File Statistic"
                    },
                    {
                      "id": "root/advanced/development/development-guide/extending-recursivist/extend-pattern-matching",
                      "label": "Extend Pattern Matching"
                    },
                    {
                      "id": "root/advanced/development/development-guide/extending-recursivist/customize-colorization",
                      "label": "Customize Colorization"
                    }
                  ]
                },
                {
                  "id": "root/advanced/development/development-guide/debugging",
                  "label": "Debugging"
                },
                {
                  "id": "root/advanced/development/development-guide/documentation",
                  "label": "Documentation"
                },
                {
                  "id": "root/advanced/development/development-guide/release-process",
                  "label": "Release Process"
                },
                {
                  "id": "root/advanced/development/development-guide/performance-notes",
                  "label": "Performance Notes"
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
                  "id": "root/advanced/testing/testing-guide/framework",
                  "label": "Framework"
                },
                {
                  "id": "root/advanced/testing/testing-guide/running-tests",
                  "label": "Running Tests",
                  "children": [
                    {
                      "id": "root/advanced/testing/testing-guide/running-tests/markers",
                      "label": "Markers"
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
                      "id": "root/advanced/testing/testing-guide/writing-tests/directory-operations",
                      "label": "Directory Operations"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/cli-commands",
                      "label": "CLI Commands"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/export-formats",
                      "label": "Export Formats"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/file-statistics",
                      "label": "File Statistics"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/parametrization",
                      "label": "Parametrization"
                    },
                    {
                      "id": "root/advanced/testing/testing-guide/writing-tests/property-based-tests",
                      "label": "Property-Based Tests"
                    }
                  ]
                },
                {
                  "id": "root/advanced/testing/testing-guide/fixtures-and-mocking",
                  "label": "Fixtures and Mocking"
                },
                {
                  "id": "root/advanced/testing/testing-guide/edge-cases",
                  "label": "Edge Cases"
                },
                {
                  "id": "root/advanced/testing/testing-guide/debugging-failing-tests",
                  "label": "Debugging Failing Tests"
                },
                {
                  "id": "root/advanced/testing/testing-guide/continuous-integration",
                  "label": "Continuous Integration"
                },
                {
                  "id": "root/advanced/testing/testing-guide/best-practices",
                  "label": "Best Practices"
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
