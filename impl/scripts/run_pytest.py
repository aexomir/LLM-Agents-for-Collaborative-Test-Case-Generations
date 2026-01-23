#!/usr/bin/env python3
"""Run pytest on generated test files."""

import argparse
import subprocess
from pathlib import Path
import sys


def run_pytest(
    test_dir: Path,
    cut_module_path: Path = None,
    output_file: Path = None,
    verbose: bool = False,
) -> int:
    """
    Run pytest on generated test files.
    
    Args:
        test_dir: Directory containing test files to run.
        cut_module_path: Path to CUT module for pytest to import.
        output_file: Optional file to save pytest output.
        verbose: Whether to run pytest in verbose mode.
        
    Returns:
        Exit code from pytest (0 for success, non-zero for failure).
    """
    import os
    
    # Validate test directory exists
    if not test_dir.exists():
        print(f"Error: Test directory does not exist: {test_dir}")
        return 1
    
    # Prepare environment with CUT module path
    env = os.environ.copy()
    if cut_module_path:
        cut_module_path = cut_module_path.resolve()
        pythonpath = env.get('PYTHONPATH', '')
        if pythonpath:
            env['PYTHONPATH'] = f"{cut_module_path}:{pythonpath}"
        else:
            env['PYTHONPATH'] = str(cut_module_path)
        print(f"Added to PYTHONPATH: {cut_module_path}")
    
    # Construct pytest command
    pytest_cmd = ["pytest", str(test_dir)]
    
    if verbose:
        pytest_cmd.append("-v")
    
    # Add additional useful flags
    pytest_cmd.extend([
        "--tb=short",  # Short traceback format
        "-ra",  # Show summary of all test outcomes
    ])
    
    print(f"Running: {' '.join(pytest_cmd)}")
    
    # Run pytest and capture output
    try:
        result = subprocess.run(
            pytest_cmd,
            env=env,
            capture_output=True,
            text=True,
        )
        
        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        
        # Print output to console
        print(output)
        
        # Save output to file if specified
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(f"Command: {' '.join(pytest_cmd)}\n")
                f.write(f"Exit code: {result.returncode}\n")
                f.write("=" * 80 + "\n")
                f.write(output)
            print(f"✓ Saved pytest output to: {output_file}")
        
        return result.returncode
        
    except FileNotFoundError:
        print("Error: pytest not found. Install it with: pip install pytest")
        return 127
    except Exception as e:
        print(f"Error running pytest: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Run pytest on generated test files"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        required=True,
        help="Directory containing test files to run",
    )
    parser.add_argument(
        "--cut-module-path",
        type=Path,
        default=None,
        help="Path to CUT module directory (impl/cut/)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional file to save pytest output",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Run pytest in verbose mode",
    )
    
    args = parser.parse_args()
    exit_code = run_pytest(
        test_dir=args.test_dir,
        cut_module_path=args.cut_module_path,
        output_file=args.output_file,
        verbose=args.verbose,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

