#!/usr/bin/env python3
"""Evaluate code coverage of generated tests."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
import sys


def eval_coverage(
    test_dir: Path,
    cut_module: str,
    output_file: Path = None,
    report_format: str = "text",
) -> dict:
    """
    Evaluate code coverage of generated tests.
    
    Args:
        test_dir: Directory containing test files.
        cut_module: Name of the CUT module to measure coverage for.
        output_file: Optional file to save coverage report.
        report_format: Format of coverage report ('text', 'html', 'json').
        
    Returns:
        Dictionary with coverage metrics (e.g., {'line': 0.85, 'branch': 0.72}).
    """
    # Validate test directory exists
    if not test_dir.exists():
        print(f"Error: Test directory does not exist: {test_dir}")
        return {"line": 0.0, "branch": 0.0, "error": "Test directory not found"}
    
    # Get the impl directory (parent of scripts)
    impl_dir = Path(__file__).parent.parent
    cut_module_file = impl_dir / "cut" / f"{cut_module}.py"
    
    if not cut_module_file.exists():
        print(f"Error: CUT module not found: {cut_module_file}")
        return {"line": 0.0, "branch": 0.0, "error": "CUT module not found"}
    
    print(f"Evaluating coverage for {cut_module} using tests in {test_dir}...")
    
    # Prepare environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(impl_dir.parent)
    
    # Run coverage with pytest
    coverage_cmd = [
        "coverage", "run",
        "--source", f"impl.cut.{cut_module}",
        "--branch",  # Enable branch coverage
        "-m", "pytest",
        str(test_dir),
        "-v"
    ]
    
    print(f"Running: {' '.join(coverage_cmd)}")
    
    try:
        # Run coverage
        result = subprocess.run(
            coverage_cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=impl_dir.parent,
        )
        
        if result.returncode not in [0, 1]:  # 0 = all pass, 1 = some tests failed but coverage ran
            print(f"Warning: Coverage run returned exit code {result.returncode}")
            print(result.stdout)
            print(result.stderr)
        
        # Get coverage report in JSON format for parsing
        json_result = subprocess.run(
            ["coverage", "json", "-o", "-"],
            capture_output=True,
            text=True,
            cwd=impl_dir.parent,
        )
        
        metrics = {"line": 0.0, "branch": 0.0}
        
        if json_result.returncode == 0:
            try:
                coverage_data = json.loads(json_result.stdout)
                
                # Extract totals
                totals = coverage_data.get("totals", {})
                
                # Line coverage
                num_statements = totals.get("num_statements", 0)
                covered_lines = totals.get("covered_lines", 0)
                if num_statements > 0:
                    metrics["line"] = covered_lines / num_statements
                
                # Branch coverage
                num_branches = totals.get("num_branches", 0)
                covered_branches = totals.get("covered_branches", 0)
                if num_branches > 0:
                    metrics["branch"] = covered_branches / num_branches
                else:
                    metrics["branch"] = None  # No branches to measure
                
                print(f"✓ Line coverage: {metrics['line']:.1%}")
                if metrics['branch'] is not None:
                    print(f"✓ Branch coverage: {metrics['branch']:.1%}")
                else:
                    print(f"✓ Branch coverage: N/A (no branches)")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing coverage JSON: {e}")
        
        # Generate report in specified format
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if report_format == "json":
                # Save JSON report
                subprocess.run(
                    ["coverage", "json", "-o", str(output_file)],
                    cwd=impl_dir.parent,
                )
                print(f"✓ Saved JSON coverage report to: {output_file}")
                
            elif report_format == "html":
                # Generate HTML report
                html_dir = output_file.parent / f"{output_file.stem}_html"
                subprocess.run(
                    ["coverage", "html", "-d", str(html_dir)],
                    cwd=impl_dir.parent,
                )
                print(f"✓ Saved HTML coverage report to: {html_dir}/")
                
            else:  # text format
                # Get text report
                text_result = subprocess.run(
                    ["coverage", "report"],
                    capture_output=True,
                    text=True,
                    cwd=impl_dir.parent,
                )
                with open(output_file, 'w') as f:
                    f.write(text_result.stdout)
                print(f"✓ Saved text coverage report to: {output_file}")
        
        return metrics
        
    except FileNotFoundError:
        print("Error: coverage not found. Install it with: pip install coverage")
        return {"line": 0.0, "branch": 0.0, "error": "coverage not installed"}
    except Exception as e:
        print(f"Error running coverage: {e}")
        return {"line": 0.0, "branch": 0.0, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate code coverage of generated tests"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        required=True,
        help="Directory containing test files",
    )
    parser.add_argument(
        "--cut-module",
        type=str,
        required=True,
        help="Name of the CUT module to measure coverage for",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional file to save coverage report",
    )
    parser.add_argument(
        "--report-format",
        type=str,
        default="text",
        choices=["text", "html", "json"],
        help="Format of coverage report",
    )
    
    args = parser.parse_args()
    metrics = eval_coverage(
        test_dir=args.test_dir,
        cut_module=args.cut_module,
        output_file=args.output_file,
        report_format=args.report_format,
    )
    print(f"Coverage metrics: {metrics}")


if __name__ == "__main__":
    main()

