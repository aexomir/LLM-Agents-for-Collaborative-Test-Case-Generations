#!/usr/bin/env python3
"""Evaluate code coverage of generated tests."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
import sys

from impl.scripts.test_run_utils import get_run_id_from_path


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
    # Use the actual directory path for source, not module path
    cut_dir = impl_dir / "cut"
    coverage_cmd = [
        "coverage", "run",
        "--source", str(cut_dir),
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
            # If tests failed completely, coverage data might be empty
            if "No data to report" in result.stdout or "No data to report" in result.stderr:
                print("ERROR: No coverage data collected. Tests may have failed to run.")
                return {"line": 0.0, "branch": 0.0, "error": "Tests failed to run"}
        
        # Get coverage report in JSON format for parsing
        json_result = subprocess.run(
            ["coverage", "json", "-o", "-"],
            capture_output=True,
            text=True,
            cwd=impl_dir.parent,
        )
        
        # Extract run ID from test directory
        run_id = get_run_id_from_path(test_dir)
        
        metrics = {"line": 0.0, "branch": 0.0}
        if run_id:
            metrics["run_id"] = run_id
        
        if json_result.returncode == 0 and json_result.stdout.strip():
            try:
                coverage_data = json.loads(json_result.stdout)
                
                # Extract totals - coverage JSON format has 'totals' at root level
                totals = coverage_data.get("totals", {})
                
                # Line coverage - use percent_covered if available, otherwise calculate
                if "percent_covered" in totals:
                    metrics["line"] = totals["percent_covered"] / 100.0
                else:
                    # Fallback: calculate from covered_lines and num_statements
                    num_statements = totals.get("num_statements", 0)
                    covered_lines = totals.get("covered_lines", 0)
                    if num_statements > 0:
                        metrics["line"] = covered_lines / num_statements
                
                # Branch coverage
                if "percent_covered_branches" in totals:
                    metrics["branch"] = totals["percent_covered_branches"] / 100.0
                else:
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
                print(f"JSON output: {json_result.stdout[:500]}")
        
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
            
            # Always save metrics as JSON for aggregation, regardless of report_format
            # This ensures the aggregate script can find coverage results
            if output_file.suffix != '.json':
                json_output = output_file.with_suffix('.json')
            else:
                json_output = output_file
            
            # Only save JSON metrics if we haven't already saved JSON format
            if report_format != "json" or json_output != output_file:
                metrics_json = {
                    "line": metrics.get("line", 0.0),
                    "branch": metrics.get("branch"),
                    "error": metrics.get("error")
                }
                if "run_id" in metrics:
                    metrics_json["run_id"] = metrics["run_id"]
                with open(json_output, 'w') as f:
                    json.dump(metrics_json, f, indent=2)
                print(f"✓ Saved coverage metrics JSON to: {json_output}")
        
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

