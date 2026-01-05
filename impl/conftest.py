"""Pytest configuration file.

This file automatically adds the parent directory to Python path
so that imports like 'from impl.cut import calculator' work
when running pytest from the impl directory.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

