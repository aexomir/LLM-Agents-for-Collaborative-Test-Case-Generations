#!/usr/bin/env python3
"""Utility functions for managing test run IDs and timestamps."""

from datetime import datetime
from pathlib import Path
import json
from typing import Optional, Dict, Any, Tuple


def generate_run_id() -> str:
    """
    Generate a unique run ID based on timestamp.
    
    Returns:
        String in format: YYYYMMDD_HHMMSS (e.g., '20250126_143022')
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_run_id_from_path(test_dir: Path) -> Optional[str]:
    """
    Extract run ID from a test directory path.
    
    Looks for patterns like:
    - tests_generated/single/20250126_143022/
    - tests_generated/collab/20250126_143022/
    
    Args:
        test_dir: Path to test directory
        
    Returns:
        Run ID string if found, None otherwise
    """
    # Check if the directory name itself is a run ID
    dir_name = test_dir.name
    if _is_valid_run_id(dir_name):
        return dir_name
    
    # Check parent directory
    parent_name = test_dir.parent.name
    if _is_valid_run_id(parent_name):
        return parent_name
    
    # Check for metadata file
    metadata_file = test_dir / ".run_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                return metadata.get("run_id")
        except Exception:
            pass
    
    # Check parent directory for metadata
    parent_metadata = test_dir.parent / ".run_metadata.json"
    if parent_metadata.exists():
        try:
            with open(parent_metadata, 'r') as f:
                metadata = json.load(f)
                return metadata.get("run_id")
        except Exception:
            pass
    
    return None


def _is_valid_run_id(s: str) -> bool:
    """Check if a string matches the run ID format."""
    try:
        datetime.strptime(s, "%Y%m%d_%H%M%S")
        return True
    except ValueError:
        return False


def save_run_metadata(
    output_dir: Path,
    run_id: str,
    cut_module: str,
    mode: str,
    additional_info: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Save metadata about a test generation run.
    
    Args:
        output_dir: Directory where tests are saved
        run_id: Unique run ID
        cut_module: Name of the CUT module
        mode: Generation mode (single/collab/competitive)
        additional_info: Optional additional metadata
        
    Returns:
        Path to the metadata file
    """
    metadata = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "cut_module": cut_module,
        "mode": mode,
    }
    
    if additional_info:
        metadata.update(additional_info)
    
    metadata_file = output_dir / ".run_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_file


def create_timestamped_output_dir(base_dir: Path, mode: str) -> Tuple[Path, str]:
    """
    Create a timestamped output directory for test generation.
    
    Args:
        base_dir: Base directory (e.g., tests_generated)
        mode: Generation mode (single/collab/competitive)
        
    Returns:
        Tuple of (output_directory_path, run_id)
    """
    run_id = generate_run_id()
    output_dir = base_dir / mode / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir, run_id


def validate_test_directory(test_dir: Path) -> Tuple[list, int]:
    """
    Validate test directory and return test files and valid test count.
    
    Args:
        test_dir: Directory containing test files
        
    Returns:
        Tuple of (list of test file paths, count of valid test files)
    """
    import ast
    
    if not test_dir.exists():
        return [], 0
    
    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        return [], 0
    
    # Validate test files can be parsed
    valid_count = 0
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                ast.parse(f.read())
            valid_count += 1
        except SyntaxError:
            pass
    
    return test_files, valid_count
