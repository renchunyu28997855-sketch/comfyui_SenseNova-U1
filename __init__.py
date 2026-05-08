from __future__ import annotations

import sys
from pathlib import Path

# Add the bundled src directory to sys.path so sensenova_u1 can be imported
# without needing to pip install the package.
_src_dir = Path(__file__).resolve().parent / "src"
if _src_dir.is_dir() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except ImportError:  # pragma: no cover - supports direct imports during tests
    from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# ComfyUI auto-loads every JS file under this directory as a frontend extension.
# Used to render `ui.text` produced by SenseNovaInterleavePreview, which the
# stock frontend does not display on the node itself.
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]