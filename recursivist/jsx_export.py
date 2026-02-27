"""
React component export functionality for the Recursivist directory visualization tool.

This module generates a JSX file containing a sophisticated, interactive directory viewer React component with advanced features:

- Folder expansion/collapse functionality
- Breadcrumb navigation
- Search with highlighted matches
- Dark mode toggle
- Optional file statistics display
- Sorting by different metrics
- Path copying
- Mobile-responsive design

The generated component is standalone and can be integrated into React applications
with minimal dependencies.
"""

import html
import logging
from typing import Any, Dict, Tuple, Union

from recursivist.core import format_size, format_timestamp

logger = logging.getLogger(__name__)


def generate_jsx_component(
    structure: Dict[str, Any],
    root_name: str,
    output_path: str,
    show_full_path: bool = False,
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    show_git_status: bool = False,
) -> None:
    """Generate a React component file for directory structure visualization.

    Creates a standalone JSX file containing a sophisticated directory viewer component with:
    - Reliable folder expand/collapse functionality
    - Breadcrumbs navigation
    - Search functionality with highlighted matches
    - Dark mode toggle
    - Path copying
    - Expand/collapse all buttons
    - Optional statistics display (LOC, size, modification times)
    - Optional Git status markers (untracked, modified, added, deleted)
    - Mobile-responsive design

    Args:
        structure: Directory structure dictionary
        root_name: Root directory name
        output_path: Path where the React component file will be saved
        show_full_path: Whether to show full paths instead of just filenames
        sort_by_loc: Whether to show lines of code counts and sort by them
        sort_by_size: Whether to show file sizes and sort by them
        sort_by_mtime: Whether to show file modification times and sort by them
        show_git_status: Whether to show Git status markers on files
    """

    def _build_structure_jsx(
        structure: Dict[str, Any], level: int = 0, path_prefix: str = ""
    ) -> str:
        jsx_content = []
        for name, content in sorted(
            [
                (k, v)
                for k, v in structure.items()
                if k != "_files"
                and k != "_max_depth_reached"
                and k != "_loc"
                and k != "_size"
                and k != "_mtime"
                and k != "_git_markers"
            ],
            key=lambda x: x[0].lower(),
        ):
            current_path = f"{path_prefix}/{name}" if path_prefix else name
            path_parts = current_path.split("/") if current_path else [name]
            if path_parts[0] == root_name and len(path_parts) > 1:
                path_parts = [root_name] + [p for p in path_parts[1:] if p]
            else:
                path_parts = [p for p in path_parts if p]
                if not path_parts or path_parts[0] != root_name:
                    path_parts = [root_name] + path_parts
            path_json = ",".join([f'"{html.escape(part)}"' for part in path_parts])
            loc_prop = ""
            size_prop = ""
            mtime_prop = ""
            if sort_by_loc and isinstance(content, dict) and "_loc" in content:
                loc_prop = f" locCount={{{content['_loc']}}}"
            if sort_by_size and isinstance(content, dict) and "_size" in content:
                size_prop = f" sizeCount={{{content['_size']}}}"
            if sort_by_mtime and isinstance(content, dict) and "_mtime" in content:
                mtime_prop = f" mtimeCount={{{content['_mtime']}}}"
            jsx_content.append(
                f"<DirectoryItem "
                f'name="{html.escape(name)}" '
                f"level={{{level}}} "
                f"path={{[{path_json}]}} "
                f'type="directory"{loc_prop}{size_prop}{mtime_prop}>'
            )
            next_path = current_path
            if isinstance(content, dict):
                if content.get("_max_depth_reached"):
                    jsx_content.append(
                        '<div className="max-depth p-3 bg-gray-50 rounded-lg border border-gray-100 ml-4 my-1">'
                    )
                    jsx_content.append(
                        '<p className="text-gray-500">⋯ (max depth reached)</p>'
                    )
                    jsx_content.append("</div>")
                else:
                    jsx_content.append(
                        _build_structure_jsx(content, level + 1, next_path)
                    )
            jsx_content.append("</DirectoryItem>")
        if "_files" in structure:
            files = structure["_files"]
            sorted_files = []

            valid_files = [
                f for f in files if not (isinstance(f, tuple) and len(f) == 0)
            ]

            def safe_get(tup: Any, idx: int, default: int = 0) -> int:
                if not isinstance(tup, tuple):
                    return default
                return int(tup[idx]) if len(tup) > idx else default

            def sort_key_all(
                f: Union[Tuple[Any, ...], str],
            ) -> Tuple[int, int, int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, 0, 0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    loc = safe_get(f, 2) if len(f) > 2 else 0
                    size = safe_get(f, 3) if len(f) > 3 else 0
                    mtime = safe_get(f, 4) if len(f) > 4 else 0
                    return (-loc, -size, -mtime, file_name)
                return (0, 0, 0, f.lower() if isinstance(f, str) else "")

            def sort_key_loc_size(
                f: Union[Tuple[Any, ...], str],
            ) -> Tuple[int, int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, 0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    loc = safe_get(f, 2) if len(f) > 2 else 0
                    size = safe_get(f, 3) if len(f) > 3 else 0
                    return (-loc, -size, file_name)
                return (0, 0, f.lower() if isinstance(f, str) else "")

            def sort_key_loc_mtime(
                f: Union[Tuple[Any, ...], str],
            ) -> Tuple[int, int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, 0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    loc = safe_get(f, 2) if len(f) > 2 else 0
                    mtime = safe_get(f, 3) if len(f) > 3 and sort_by_loc else 0
                    if len(f) > 4 and sort_by_loc and sort_by_size:
                        mtime = safe_get(f, 4)
                    return (-loc, -mtime, file_name)
                return (0, 0, f.lower() if isinstance(f, str) else "")

            def sort_key_size_mtime(
                f: Union[Tuple[Any, ...], str],
            ) -> Tuple[int, int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, 0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    size = safe_get(f, 2) if len(f) > 2 else 0
                    mtime = safe_get(f, 3) if len(f) > 3 else 0
                    return (-size, -mtime, file_name)
                return (0, 0, f.lower() if isinstance(f, str) else "")

            def sort_key_mtime(f: Union[Tuple[Any, ...], str]) -> Tuple[int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    mtime = 0
                    if len(f) > 4 and sort_by_loc and sort_by_size:
                        mtime = safe_get(f, 4)
                    elif len(f) > 3 and (sort_by_loc or sort_by_size):
                        mtime = safe_get(f, 3)
                    elif len(f) > 2:
                        mtime = safe_get(f, 2)
                    return (-mtime, file_name)
                return (0, f.lower() if isinstance(f, str) else "")

            def sort_key_size(f: Union[Tuple[Any, ...], str]) -> Tuple[int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    size = 0
                    if len(f) > 3 and sort_by_loc:
                        size = safe_get(f, 3)
                    elif len(f) > 2:
                        size = safe_get(f, 2)
                    return (-size, file_name)
                return (0, f.lower() if isinstance(f, str) else "")

            def sort_key_loc(f: Union[Tuple[Any, ...], str]) -> Tuple[int, str]:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return (0, "")
                    file_name = f[0].lower() if len(f) > 0 else ""
                    loc = safe_get(f, 2) if len(f) > 2 else 0
                    return (-loc, file_name)
                return (0, f.lower() if isinstance(f, str) else "")

            def sort_key_name(f: Union[Tuple[Any, ...], str]) -> str:
                if isinstance(f, tuple):
                    if len(f) == 0:
                        return ""
                    return f[0].lower() if len(f) > 0 else ""
                return f.lower() if isinstance(f, str) else ""

            if sort_by_loc and sort_by_size and sort_by_mtime:
                sorted_files = sorted(valid_files, key=sort_key_all)
            elif sort_by_loc and sort_by_size:
                sorted_files = sorted(valid_files, key=sort_key_loc_size)
            elif sort_by_loc and sort_by_mtime:
                sorted_files = sorted(valid_files, key=sort_key_loc_mtime)
            elif sort_by_size and sort_by_mtime:
                sorted_files = sorted(valid_files, key=sort_key_size_mtime)
            elif sort_by_mtime:
                sorted_files = sorted(valid_files, key=sort_key_mtime)
            elif sort_by_size:
                sorted_files = sorted(valid_files, key=sort_key_size)
            elif sort_by_loc:
                sorted_files = sorted(valid_files, key=sort_key_loc)
            else:
                sorted_files = sorted(valid_files, key=sort_key_name)

            for file_item in sorted_files:
                file_name = "unknown"
                display_path = "unknown"
                loc = 0
                size = 0
                mtime = 0

                if isinstance(file_item, tuple):
                    if len(file_item) == 0:
                        continue

                    file_name = file_item[0] if len(file_item) > 0 else "unknown"
                    display_path = file_item[1] if len(file_item) > 1 else file_name

                    if (
                        sort_by_loc
                        and sort_by_size
                        and sort_by_mtime
                        and len(file_item) > 4
                    ):
                        loc = file_item[2]
                        size = file_item[3]
                        mtime = file_item[4]
                    elif sort_by_loc and sort_by_size and len(file_item) > 3:
                        loc = file_item[2]
                        size = file_item[3]
                    elif sort_by_loc and sort_by_mtime and len(file_item) > 3:
                        loc = file_item[2]
                        mtime = file_item[3]
                    elif sort_by_size and sort_by_mtime and len(file_item) > 3:
                        size = file_item[2]
                        mtime = file_item[3]
                    elif sort_by_loc and len(file_item) > 2:
                        loc = file_item[2]
                    elif sort_by_size and len(file_item) > 2:
                        size = file_item[2]
                    elif sort_by_mtime and len(file_item) > 2:
                        mtime = file_item[2]
                else:
                    file_name = file_item
                    display_path = file_name

                if path_prefix:
                    path_parts = path_prefix.split("/")
                    if path_parts and path_parts[0] == root_name:
                        path_parts = [root_name] + [p for p in path_parts[1:] if p]
                    else:
                        path_parts = [p for p in path_parts if p]
                        if not path_parts or path_parts[0] != root_name:
                            path_parts = [root_name] + path_parts
                else:
                    path_parts = [root_name]
                path_parts.append(file_name)
                path_json = ",".join(
                    [f'"{html.escape(part)}"' for part in path_parts if part]
                )

                props = [
                    f'name="{html.escape(file_name)}"',
                    f'displayPath="{html.escape(display_path)}"',
                    f"path={{[{path_json}]}}",
                    f"level={{{level}}}",
                ]

                if sort_by_loc:
                    props.append(f"locCount={{{loc}}}")

                if sort_by_size:
                    props.append(f"sizeCount={{{size}}}")
                    props.append(f'sizeFormatted="{format_size(size)}"')

                if sort_by_mtime:
                    props.append(f"mtimeCount={{{mtime}}}")
                    props.append(f'mtimeFormatted="{format_timestamp(mtime)}"')

                if show_git_status:
                    _git_markers_jsx = structure.get("_git_markers", {})
                    _gs = _git_markers_jsx.get(file_name, "")
                    if _gs:
                        props.append(f'gitStatus="{_gs}"')

                jsx_content.append(f"<FileItem {' '.join(props)} />")

        return "\n".join(jsx_content)

    combined_imports = ""
    if sort_by_loc and sort_by_size and sort_by_mtime:
        combined_imports = (
            """import { BarChart2, Database, Clock } from 'lucide-react';"""
        )
    elif sort_by_loc and sort_by_size:
        combined_imports = """import { BarChart2, Database } from 'lucide-react';"""
    elif sort_by_loc and sort_by_mtime:
        combined_imports = """import { BarChart2, Clock } from 'lucide-react';"""
    elif sort_by_size and sort_by_mtime:
        combined_imports = """import { Database, Clock } from 'lucide-react';"""
    elif sort_by_loc:
        combined_imports = """import { BarChart2 } from 'lucide-react';"""
    elif sort_by_size:
        combined_imports = """import { Database } from 'lucide-react';"""
    elif sort_by_mtime:
        combined_imports = """import { Clock } from 'lucide-react';"""
    loc_state = (
        """const showLoc = true;""" if sort_by_loc else """const showLoc = false;"""
    )
    size_state = (
        """const showSize = true;""" if sort_by_size else """const showSize = false;"""
    )
    mtime_state = (
        """const showMtime = true;"""
        if sort_by_mtime
        else """const showMtime = false;"""
    )
    git_status_state = (
        """const showGitStatus = true;"""
        if show_git_status
        else """const showGitStatus = false;"""
    )
    loc_sort_state = (
        """const sortByLoc = true;""" if sort_by_loc else """const sortByLoc = false;"""
    )
    size_sort_state = (
        """const sortBySize = true;"""
        if sort_by_size
        else """const sortBySize = false;"""
    )
    mtime_sort_state = (
        """const sortByMtime = true;"""
        if sort_by_mtime
        else """const sortByMtime = false;"""
    )
    loc_toggle_function = ""
    size_toggle_function = ""
    mtime_toggle_function = ""
    loc_toggle_button = ""
    size_toggle_button = ""
    mtime_toggle_button = ""
    root_loc_prop = ""
    root_size_prop = ""
    root_mtime_prop = ""
    if sort_by_loc and "_loc" in structure:
        root_loc_prop = f" locCount={{{structure['_loc']}}}"
    if sort_by_size and "_size" in structure:
        root_size_prop = f" sizeCount={{{structure['_size']}}}"
    if sort_by_mtime and "_mtime" in structure:
        root_mtime_prop = f" mtimeCount={{{structure['_mtime']}}}"
    format_size_function = ""
    if sort_by_size:
        format_size_function = """
  const format_size = (size_in_bytes) => {
    if (size_in_bytes < 1024) {
      return `${size_in_bytes} B`;
    } else if (size_in_bytes < 1024 * 1024) {
      return `${(size_in_bytes / 1024).toFixed(1)} KB`;
    } else if (size_in_bytes < 1024 * 1024 * 1024) {
      return `${(size_in_bytes / (1024 * 1024)).toFixed(1)} MB`;
    } else {
      return `${(size_in_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    }
  };"""
    format_timestamp_function = ""
    if sort_by_mtime:
        format_timestamp_function = """
  const format_timestamp = (timestamp) => {
    const dt = new Date(timestamp * 1000);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (dt >= today) {
      return `Today ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`;
    }
    else if (dt >= yesterday) {
      return `Yesterday ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`;
    }
    else if ((today - dt) / (1000 * 60 * 60 * 24) < 7) {
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      return `${days[dt.getDay()]} ${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`;
    }
    else if (dt.getFullYear() === now.getFullYear()) {
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${months[dt.getMonth()]} ${dt.getDate()}`;
    }
    else {
      return `${dt.getFullYear()}-${(dt.getMonth() + 1).toString().padStart(2, '0')}-${dt.getDate().toString().padStart(2, '0')}`;
    }
  };"""
    component_template = f"""import React, {{ useState, useEffect, useRef }} from 'react';
    import PropTypes from 'prop-types';
    import {{ ChevronDown, ChevronUp, Folder, FolderOpen, File, Maximize2, Minimize2, Search, X, Info, Home, ChevronRight, Copy, Check }} from 'lucide-react';
    {combined_imports}
    const AppContext = React.createContext();
    const highlightMatch = (text, searchTerm) => {{
      if (!searchTerm) return text;
      const parts = text.split(new RegExp(`(${{searchTerm}})`, 'gi'));
      return (
        <>
          {{parts.map((part, i) =>
            part.toLowerCase() === searchTerm.toLowerCase()
              ? <mark key={{i}} className="bg-yellow-200 px-1 rounded">{{part}}</mark>
              : part
          )}}
        </>
      );
    }};
    const Breadcrumbs = () => {{
      const {{
        currentPath,
        setCurrentPath,
        selectedItem,
        darkMode
      }} = React.useContext(AppContext);
      const [copied, setCopied] = useState(false);
      const breadcrumbRef = useRef(null);
      const copyPath = () => {{
        let path = currentPath.join('/');
        if (selectedItem) {{
          path = [...currentPath, selectedItem.name].join('/');
        }}
        navigator.clipboard.writeText(path).then(() => {{
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }});
      }};
      const navigateTo = (index) => {{
        setCurrentPath(currentPath.slice(0, index + 1));
      }};
      useEffect(() => {{
        if (breadcrumbRef.current) {{
          breadcrumbRef.current.scrollLeft = breadcrumbRef.current.scrollWidth;
        }}
      }}, [currentPath, selectedItem]);
      return (
        <div className={{`sticky top-0 left-0 right-0 ${{darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800'}} p-3 shadow-md z-50 overflow-visible`}}>
          <div className="container mx-auto max-w-5xl flex items-center justify-between">
            <div
              ref={{breadcrumbRef}}
              className="overflow-x-auto whitespace-nowrap flex items-center flex-grow mr-2"
              style={{{{ overflowX: 'auto' }}}}
            >
              <button
                onClick={{() => navigateTo(0)}}
                className={{`${{darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'}} flex items-center mr-1 flex-shrink-0`}}
                title="Home directory"
              >
                <Home className="w-4 h-4 mr-1" />
                <span className="font-medium">{{currentPath[0]}}</span>
              </button>
              {{currentPath.length > 1 && currentPath.slice(1).map((segment, index) => (
                <React.Fragment key={{index}}>
                  <ChevronRight className={{`w-4 h-4 mx-1 ${{darkMode ? 'text-gray-500' : 'text-gray-400'}} flex-shrink-0`}} />
                  <button
                    onClick={{() => navigateTo(index + 1)}}
                    className={{`${{
                      index === currentPath.length - 2 && !selectedItem ?
                        (darkMode ? 'text-yellow-300 font-medium' : 'text-blue-700 font-medium') :
                        (darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800')
                    }} flex-shrink-0`}}
                  >
                    {{segment}}
                  </button>
                </React.Fragment>
              ))}}
              {{selectedItem && (
                <>
                  <ChevronRight className={{`w-4 h-4 mx-1 ${{darkMode ? 'text-gray-500' : 'text-gray-400'}} flex-shrink-0`}} />
                  <span className={{`${{darkMode ? 'text-yellow-300 font-medium' : 'text-blue-700 font-medium'}} flex-shrink-0`}}>
                    {{selectedItem.name}}
                  </span>
                </>
              )}}
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0">
              {{copied ? (
                <span className={{`text-xs px-2 py-1 rounded ${{darkMode ? 'bg-green-800 text-green-200' : 'bg-green-100 text-green-800'}}`}}>
                  <Check className="w-3 h-3 inline mr-1" />
                  Copied
                </span>
              ) : (
                <button
                  onClick={{copyPath}}
                  className={{`p-1 rounded ${{darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}}`}}
                  title="Copy path"
                >
                  <Copy className="w-4 h-4" />
                </button>
              )}}
            </div>
          </div>
        </div>
      );
    }};
    const DirectoryItem = (props) => {{
      const {{
        openFolders,
        setOpenFolders,
        searchTerm,
        darkMode,
        expandAll,
        collapseAll,
        setCurrentPath,
        currentPath,
        setSelectedItem,
        showLoc,
        showSize,
        showMtime,
        format_size,
        format_timestamp
      }} = React.useContext(AppContext);
      const {{ name, children, level = 0, path = [] }} = props;
      const folderId = path.join('/');
      const isOpen = openFolders.has(folderId);
      const isCurrentPath = currentPath.length === path.length &&
        path.every((segment, index) => segment === currentPath[index]);
      const isInCurrentPath = currentPath.length > path.length &&
        path.every((segment, index) => segment === currentPath[index]);
      const matchesSearch = searchTerm && name.toLowerCase().includes(searchTerm.toLowerCase());
      const toggleFolder = (e) => {{
        e.stopPropagation();
        const newOpenFolders = new Set(openFolders);
        if (isOpen) {{
          newOpenFolders.delete(folderId);
        }} else {{
          newOpenFolders.add(folderId);
        }}
        setOpenFolders(newOpenFolders);
      }};
      const navigateToFolder = (e) => {{
        e.stopPropagation();
        setCurrentPath(path);
        setSelectedItem(null);
      }};
      useEffect(() => {{
        if (expandAll) {{
          setOpenFolders(prev => new Set([...prev, folderId]));
        }}
      }}, [expandAll, folderId, setOpenFolders]);
      useEffect(() => {{
        if (collapseAll && folderId !== '{html.escape(root_name)}') {{
          setOpenFolders(prev => {{
            const newFolders = new Set(prev);
            newFolders.delete(folderId);
            return newFolders;
          }});
        }}
      }}, [collapseAll, folderId, setOpenFolders]);
      useEffect(() => {{
        if (searchTerm && matchesSearch) {{
          setOpenFolders(prev => new Set([...prev, folderId]));
        }}
      }}, [searchTerm, matchesSearch, folderId, setOpenFolders]);
      useEffect(() => {{
        if (isCurrentPath || isInCurrentPath) {{
          setOpenFolders(prev => new Set([...prev, folderId]));
        }}
      }}, [isCurrentPath, isInCurrentPath, folderId, setOpenFolders]);
      const indentClass = level === 0 ? '' : 'ml-4';
      const currentPathClass = isCurrentPath
        ? darkMode
          ? 'bg-blue-900 hover:bg-blue-800'
          : 'bg-blue-100 hover:bg-blue-200'
        : isInCurrentPath
          ? darkMode
            ? 'bg-blue-800/50 hover:bg-blue-800'
            : 'bg-blue-50 hover:bg-blue-100'
          : darkMode
            ? 'bg-gray-800 hover:bg-gray-700'
            : 'bg-gray-50 hover:bg-gray-100';
      const searchMatchClass = matchesSearch
        ? darkMode
          ? 'ring-1 ring-yellow-500'
          : 'ring-1 ring-yellow-300'
        : '';
      return (
        <div className={{`w-full ${{indentClass}}`}} data-folder={{folderId}}>
          <div className={{`flex items-center justify-between p-2 mb-1 rounded-lg ${{currentPathClass}} ${{searchMatchClass}}`}}>
            <div className="flex items-center flex-grow cursor-pointer" onClick={{navigateToFolder}}>
              {{isOpen
                ? <FolderOpen className={{`w-5 h-5 mr-2 ${{isCurrentPath ? (darkMode ? 'text-yellow-300' : 'text-blue-600') : darkMode ? 'text-blue-400' : 'text-blue-500'}}`}} />
                : <Folder className={{`w-5 h-5 mr-2 ${{isCurrentPath ? (darkMode ? 'text-yellow-300' : 'text-blue-600') : darkMode ? 'text-blue-400' : 'text-blue-500'}}`}} />
              }}
              <span className={{`font-medium truncate ${{isCurrentPath ? (darkMode ? 'text-yellow-300' : 'text-blue-700') : ''}}`}}>
                {{searchTerm ? highlightMatch(name, searchTerm) : name}}
              </span>
              {{props.locCount !== undefined && showLoc && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full ${{isCurrentPath ?
                  (darkMode ? 'bg-blue-800 text-blue-200' : 'bg-blue-200 text-blue-700') :
                  (darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')}}`}}>
                  {{props.locCount}} lines
                </span>
              )}}
              {{props.sizeCount !== undefined && showSize && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full ${{isCurrentPath ?
                  (darkMode ? 'bg-teal-800 text-teal-200' : 'bg-teal-200 text-teal-700') :
                  (darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')}}`}}>
                  {{format_size(props.sizeCount)}}
                </span>
              )}}
              {{props.mtimeCount !== undefined && showMtime && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full ${{isCurrentPath ?
                  (darkMode ? 'bg-purple-800 text-purple-200' : 'bg-purple-200 text-purple-700') :
                  (darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')}}`}}>
                  {{format_timestamp(props.mtimeCount)}}
                </span>
              )}}
            </div>
            <button
              className={{`p-1 rounded-full ${{darkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-200'}}`}}
              onClick={{toggleFolder}}
              data-testid="folder-toggle"
            >
              {{isOpen ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}}
            </button>
          </div>
          {{isOpen && (
            <div className="py-1">
              {{children}}
            </div>
          )}}
        </div>
      );
    }};
    const FileItem = (props) => {{
      const {{
        searchTerm,
        darkMode,
        currentPath,
        setCurrentPath,
        selectedItem,
        setSelectedItem,
        showLoc,
        showSize,
        showMtime,
        showGitStatus
      }} = React.useContext(AppContext);
      const {{ name, displayPath, path = [] }} = props;
      const gitStatus = props.gitStatus || '';
      const isDeleted = gitStatus === 'D';
      const GIT_BADGE_COLORS = {{
        U: {{ bg: darkMode ? 'bg-gray-700' : 'bg-gray-200', text: darkMode ? 'text-gray-400' : 'text-gray-500' }},
        M: {{ bg: darkMode ? 'bg-yellow-900' : 'bg-yellow-100', text: darkMode ? 'text-yellow-300' : 'text-yellow-700' }},
        A: {{ bg: darkMode ? 'bg-green-900' : 'bg-green-100', text: darkMode ? 'text-green-300' : 'text-green-700' }},
        D: {{ bg: darkMode ? 'bg-red-900' : 'bg-red-100', text: darkMode ? 'text-red-300' : 'text-red-600' }},
      }};
      useEffect(() => {{
      }}, [currentPath, path]);
      const matchesSearch = searchTerm && name.toLowerCase().includes(searchTerm.toLowerCase());
      const isSelected = selectedItem &&
        selectedItem.path &&
        selectedItem.path.length === path.length &&
        selectedItem.path.every((segment, index) => segment === path[index]);
      const handleFileSelect = () => {{
        setCurrentPath(path.slice(0, -1));
        setSelectedItem({{
          type: 'file',
          name,
          displayPath,
          path
        }});
      }};
      const indentClass = 'ml-4';
      const selectedClass = isSelected
        ? darkMode
          ? 'bg-blue-900 hover:bg-blue-800'
          : 'bg-blue-100 hover:bg-blue-200'
        : darkMode
          ? 'bg-gray-800 hover:bg-gray-700'
          : 'bg-white hover:bg-gray-50';
      const searchMatchClass = matchesSearch
        ? darkMode
          ? 'ring-1 ring-yellow-500'
          : 'ring-1 ring-yellow-300'
        : '';
      return (
        <div className={{`w-full ${{indentClass}}`}}>
          <div
            className={{`flex items-center p-2 rounded-lg border cursor-pointer ${{selectedClass}} ${{searchMatchClass}} ${{darkMode ? 'border-gray-700' : 'border-gray-100'}} my-1`}}
            onClick={{handleFileSelect}}
          >
            <File className={{`w-5 h-5 mr-2 ${{isSelected ? (darkMode ? 'text-yellow-300' : 'text-blue-600') : darkMode ? 'text-blue-400/70' : 'text-blue-400'}}`}} />
            <div className="min-w-0 overflow-hidden">
              <span className={{`truncate block ${{isSelected ? (darkMode ? 'text-yellow-300 font-medium' : 'text-blue-700 font-medium') : ''}} ${{isDeleted ? 'line-through opacity-60' : ''}}`}}>
                {{searchTerm ? highlightMatch(displayPath, searchTerm) : displayPath}}
              </span>
              {{props.locCount !== undefined && showLoc && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full ${{isSelected ?
                  (darkMode ? 'bg-blue-800 text-blue-200' : 'bg-blue-200 text-blue-700') :
                  (darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')}}`}}>
                  {{props.locCount}} lines
                </span>
              )}}
              {{props.sizeCount !== undefined && showSize && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full ${{isSelected ?
                  (darkMode ? 'bg-teal-800 text-teal-200' : 'bg-teal-200 text-teal-700') :
                  (darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')}}`}}>
                  {{props.sizeFormatted}}
                </span>
              )}}
              {{props.mtimeCount !== undefined && showMtime && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full ${{isSelected ?
                  (darkMode ? 'bg-purple-800 text-purple-200' : 'bg-purple-200 text-purple-700') :
                  (darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700')}}`}}>
                  {{props.mtimeFormatted}}
                </span>
              )}}
              {{showGitStatus && gitStatus && GIT_BADGE_COLORS[gitStatus] && (
                <span className={{`ml-2 text-xs px-1.5 py-0.5 rounded-full font-mono font-bold ${{GIT_BADGE_COLORS[gitStatus].bg}} ${{GIT_BADGE_COLORS[gitStatus].text}}`}}>
                  [{html.escape("{")}gitStatus{html.escape("}")}]
                </span>
              )}}
            </div>
          </div>
        </div>
      );
    }};
    const SearchBar = () => {{
      const {{ searchTerm, setSearchTerm, darkMode }} = React.useContext(AppContext);
      return (
        <div className="relative mb-4">
          <div className={{`flex items-center border rounded-lg overflow-hidden ${{
            darkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'
          }}`}}>
            <div className="p-2">
              <Search className={{`w-5 h-5 ${{darkMode ? 'text-gray-400' : 'text-gray-500'}}`}} />
            </div>
            <input
              type="text"
              value={{searchTerm}}
              onChange={{(e) => setSearchTerm(e.target.value)}}
              placeholder="Search files and folders..."
              className={{`flex-grow p-2 outline-none ${{
                darkMode ? 'bg-gray-700 text-white placeholder-gray-400' : 'bg-white text-gray-800 placeholder-gray-400'
              }}`}}
            />
            {{searchTerm && (
              <button
                onClick={{() => setSearchTerm('')}}
                className={{`p-2 ${{darkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-100'}}`}}
              >
                <X className={{`w-4 h-4 ${{darkMode ? 'text-gray-400' : 'text-gray-500'}}`}} />
              </button>
            )}}
          </div>
        </div>
      );
    }};
    const DirectoryViewer = () => {{
      const [openFolders, setOpenFolders] = useState(new Set(['{
        html.escape(root_name)
    }']));
      const [searchTerm, setSearchTerm] = useState('');
      const [darkMode, setDarkMode] = useState(false);
      const [currentPath, setCurrentPath] = useState(['{html.escape(root_name)}']);
      const [selectedItem, setSelectedItem] = useState(null);
      const [expandAll, setExpandAll] = useState(false);
      const [collapseAll, setCollapseAll] = useState(false);
      {loc_state}
      {loc_sort_state}
      {size_state}
      {size_sort_state}
      {mtime_state}
      {mtime_sort_state}
      {git_status_state}
      const handleExpandAll = () => {{
        setExpandAll(true);
        setTimeout(() => setExpandAll(false), 100);
      }};
      const handleCollapseAll = () => {{
        setCollapseAll(true);
        setTimeout(() => setCollapseAll(false), 100);
      }};
      const toggleDarkMode = () => {{
        setDarkMode(!darkMode);
      }};
      {loc_toggle_function}
      {size_toggle_function}
      {mtime_toggle_function}
      {
        format_size_function
        if format_size_function
        else '''
  const format_size = () => {
    return '0 B';
  };'''
    }

      {
        format_timestamp_function
        if format_timestamp_function
        else '''
  const format_timestamp = () => {
    return '';
  };'''
    }

      useEffect(() => {{
        if (darkMode) {{
          document.body.classList.add('dark-mode');
        }} else {{
          document.body.classList.remove('dark-mode');
        }}
      }}, [darkMode]);
      return (
        <AppContext.Provider value={{{{
          openFolders,
          setOpenFolders,
          searchTerm,
          setSearchTerm,
          darkMode,
          expandAll,
          collapseAll,
          currentPath,
          setCurrentPath,
          selectedItem,
          setSelectedItem,
          showLoc,
          sortByLoc,
          showSize,
          sortBySize,
          showMtime,
          sortByMtime,
          showGitStatus,
          format_size,
          format_timestamp
        }}}}>
          <div className={{`min-h-screen ${{darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-50 text-gray-900'}}`}}>
            <style>{{`
              body.dark-mode {{
                background-color: rgb(17, 24, 39);
                color: rgb(243, 244, 246);
              }}
              .overflow-x-auto {{
                overflow-x: auto;
                white-space: nowrap;
              }}
            `}}</style>
            <Breadcrumbs />
            <div className="container mx-auto max-w-5xl p-4">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6">
                <div>
                  <h1 className="text-xl font-bold flex items-center">
                    <FolderOpen className={{`w-6 h-6 mr-2 ${{darkMode ? 'text-blue-400' : 'text-blue-500'}}`}} />
                    Directory Structure: {html.escape(root_name)}
                  </h1>
                  <p className={{`mt-1 text-sm ${{darkMode ? 'text-gray-400' : 'text-gray-500'}}`}}>
                    Explore and navigate through the directory structure
                  </p>
                </div>
                <div className="flex mt-4 sm:mt-0 space-x-2">
                  <button
                    onClick={{handleExpandAll}}
                    className={{`flex items-center px-3 py-1.5 text-sm rounded-md ${{
                      darkMode ? 'bg-gray-800 hover:bg-gray-700 text-blue-400' : 'bg-blue-100 hover:bg-blue-200 text-blue-700'
                    }}`}}
                  >
                    <Maximize2 className="w-4 h-4 mr-1" />
                    <span className="hidden sm:inline">Expand All</span>
                  </button>
                  <button
                    onClick={{handleCollapseAll}}
                    className={{`flex items-center px-3 py-1.5 text-sm rounded-md ${{
                      darkMode ? 'bg-gray-800 hover:bg-gray-700' : 'bg-gray-200 hover:bg-gray-300'
                    }}`}}
                  >
                    <Minimize2 className="w-4 h-4 mr-1" />
                    <span className="hidden sm:inline">Collapse All</span>
                  </button>{loc_toggle_button}{size_toggle_button}{mtime_toggle_button}
                  <button
                    onClick={{toggleDarkMode}}
                    className={{`px-3 py-1.5 text-sm rounded-md ${{
                      darkMode ? 'bg-gray-800 hover:bg-gray-700' : 'bg-gray-200 hover:bg-gray-300'
                    }}`}}
                  >
                    {{darkMode ? 'Light' : 'Dark'}}
                  </button>
                </div>
              </div>
              <SearchBar />
              <div className={{`p-4 rounded-lg shadow ${{darkMode ? 'bg-gray-800' : 'bg-white'}}`}}>
                <DirectoryItem
                  name="{html.escape(root_name)}"
                  level={{0}}
                  path={{["{html.escape(root_name)}"]}}{root_loc_prop}{root_size_prop}{
        root_mtime_prop
    }
                >
    {_build_structure_jsx(structure, 1, root_name if show_full_path else "")}
                </DirectoryItem>
                {{/* Empty state for search */}}
                {{searchTerm && openFolders.size <= 1 && (
                  <div className="py-8 text-center">
                    <Info className={{`w-12 h-12 mx-auto mb-3 ${{darkMode ? 'text-gray-600' : 'text-gray-300'}}`}} />
                    <h3 className="text-lg font-medium">No matching files or folders</h3>
                    <p className={{`mt-1 text-sm ${{darkMode ? 'text-gray-400' : 'text-gray-500'}}`}}>
                      Try a different search term or check spelling
                    </p>
                  </div>
                )}}
              </div>
            </div>
          </div>
        </AppContext.Provider>
      );
    }};
    DirectoryItem.propTypes = {{
      name: PropTypes.string.isRequired,
      children: PropTypes.node,
      level: PropTypes.number,
      path: PropTypes.arrayOf(PropTypes.string),
      locCount: PropTypes.number,
      sizeCount: PropTypes.number,
      mtimeCount: PropTypes.number
    }};
    FileItem.propTypes = {{
      name: PropTypes.string.isRequired,
      displayPath: PropTypes.string.isRequired,
      path: PropTypes.arrayOf(PropTypes.string),
      level: PropTypes.number,
      locCount: PropTypes.number,
      sizeCount: PropTypes.number,
      sizeFormatted: PropTypes.string,
      mtimeCount: PropTypes.number,
      mtimeFormatted: PropTypes.string,
      gitStatus: PropTypes.string
    }};
    export default DirectoryViewer;
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(component_template)
        logger.info(f"Successfully exported to React component: {output_path}")
    except Exception as e:
        logger.error(f"Error exporting to React component: {e}")
        raise
