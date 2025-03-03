"""
This module adds React component export functionality to the Recursivist tool.
It generates a JSX file with a nested collapsible component for directory visualization.
"""

import html
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def generate_jsx_component(
    structure: Dict[str, Any],
    root_name: str,
    output_path: str,
    show_full_path: bool = False,
    base_path: Optional[str] = None,
) -> None:
    """
    Generate a React component file for directory structure visualization.

    Args:
        structure: Directory structure dictionary
        root_name: Root directory name
        output_path: Path where the React component file will be saved
        show_full_path: Whether to show full paths instead of just filenames
        base_path: Base path for full path display
    """

    def _build_structure_jsx(
        structure: Dict[str, Any], level: int = 0, path_prefix: str = ""
    ) -> str:
        jsx_content = []

        for name, content in sorted(
            [
                (k, v)
                for k, v in structure.items()
                if k != "_files" and k != "_max_depth_reached"
            ],
            key=lambda x: x[0].lower(),
        ):
            jsx_content.append(
                f'<CollapsibleItem title="{html.escape(name)}" level={{level}}>'
            )

            next_path = f"{path_prefix}/{name}" if path_prefix else name

            if isinstance(content, dict):
                if content.get("_max_depth_reached"):
                    jsx_content.append(
                        '<div className="p-3 bg-gray-50 rounded-lg border border-gray-100 ml-4 my-1">'
                    )
                    jsx_content.append(
                        '<p className="text-gray-500">⋯ (max depth reached)</p>'
                    )
                    jsx_content.append("</div>")
                else:
                    jsx_content.append(
                        _build_structure_jsx(content, level + 1, next_path)
                    )

            jsx_content.append("</CollapsibleItem>")

        if "_files" in structure:
            files = structure["_files"]
            for file_item in sorted(
                files, key=lambda f: f[0].lower() if isinstance(f, tuple) else f.lower()
            ):
                file_content = (
                    '<div className="p-3 bg-white rounded-lg border border-gray-100">'
                )

                if show_full_path and isinstance(file_item, tuple):
                    _, full_path = file_item
                    file_content += f'<p className="flex items-center"><span className="mr-2">📄</span> {html.escape(full_path)}</p>'
                else:
                    file_name = file_item
                    if isinstance(file_name, tuple):
                        file_name = file_name[0]
                    file_content += f'<p className="flex items-center"><span className="mr-2">📄</span> {html.escape(file_name)}</p>'

                file_content += "</div>"
                jsx_content.append(file_content)

        return "\n".join(jsx_content)

    component_template = f"""import React, {{ useState, useEffect }} from 'react';
import {{ ChevronDown, ChevronUp, Folder, Maximize2, Minimize2 }} from 'lucide-react';

const CollapsibleContext = React.createContext();

const CollapsibleItem = ({{ title, children, level = 0 }}) => {{
  const [isOpen, setIsOpen] = useState(false);
  const {{ expandAll, collapseAll, resetTrigger }} = React.useContext(CollapsibleContext);

  useEffect(() => {{
    if (expandAll) {{
      setIsOpen(true);
    }}
  }}, [expandAll]);

  useEffect(() => {{
    if (collapseAll) {{
      setIsOpen(false);
    }}
  }}, [collapseAll]);

  useEffect(() => {{
  }}, [resetTrigger]);

  const indentClass = level === 0 ? '' : 'ml-4';
  const bgClass = level === 0 ? 'bg-gray-100 hover:bg-gray-200' : 'bg-gray-50 hover:bg-gray-100';

  return (
    <div className={{`w-full ${{indentClass}}`}}>
      <button
        onClick={{() => setIsOpen(!isOpen)}}
        className={{`w-full flex items-center justify-between p-3 ${{bgClass}} rounded-lg transition-colors mb-1`}}
      >
        <div className="flex items-center">
          <Folder className="w-4 h-4 mr-2 text-blue-500" />
          <span className="font-medium">{{title}}</span>
        </div>
        {{isOpen ? (
          <ChevronUp className="w-4 h-4 transition-transform" />
        ) : (
          <ChevronDown className="w-4 h-4 transition-transform" />
        )}}
      </button>

      <div
        className={{`overflow-hidden transition-all duration-300 ease-in-out ${{
          isOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0'
        }}`}}
      >
        <div className={{`py-2 ${{isOpen ? 'animate-fadeIn' : ''}}`}}>
          {{children}}
        </div>
      </div>
    </div>
  );
}};

const DirectoryViewer = () => {{
  const [expandAll, setExpandAll] = useState(false);
  const [collapseAll, setCollapseAll] = useState(false);
  const [resetTrigger, setResetTrigger] = useState(0);

  const handleExpandAll = () => {{
    setExpandAll(true);
    setCollapseAll(false);
    setTimeout(() => {{
      setExpandAll(false);
      setResetTrigger(prev => prev + 1);
    }}, 100);
  }};

  const handleCollapseAll = () => {{
    setCollapseAll(true);
    setExpandAll(false);
    setTimeout(() => {{
      setCollapseAll(false);
      setResetTrigger(prev => prev + 1);
    }}, 100);
  }};

  return (
    <CollapsibleContext.Provider value={{{{ expandAll, collapseAll, resetTrigger }}}}>
      <div className="w-full max-w-5xl mx-auto space-y-2">
        <h1 className="text-xl font-bold mb-4">Directory Structure: {html.escape(root_name)}</h1>
        <div className="flex justify-end mb-4 space-x-2">
          <button
            onClick={{handleExpandAll}}
            className="flex items-center px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md transition-colors"
          >
            <Maximize2 className="w-4 h-4 mr-1" />
            Expand All
          </button>
          <button
            onClick={{handleCollapseAll}}
            className="flex items-center px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
          >
            <Minimize2 className="w-4 h-4 mr-1" />
            Collapse All
          </button>
        </div>
        <CollapsibleItem title="{html.escape(root_name)}">
{_build_structure_jsx(structure, 1, root_name if show_full_path else "")}
        </CollapsibleItem>
      </div>
    </CollapsibleContext.Provider>
  );
}};

export default DirectoryViewer;
"""

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(component_template)
        logger.info(f"Successfully exported React component to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting to React component: {e}")
        raise
