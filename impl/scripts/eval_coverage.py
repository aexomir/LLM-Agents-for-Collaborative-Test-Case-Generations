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
    
    # Validate test directory
    from impl.scripts.test_run_utils import validate_test_directory
    test_files, valid_count = validate_test_directory(test_dir)
    
    if not test_files:
        error_msg = f"No test files found in {test_dir}"
        print(f"Error: {error_msg}")
        return {"line": 0.0, "branch": 0.0, "error": error_msg}
    
    print(f"Found {len(test_files)} test file(s)")
    
    if valid_count == 0:
        error_msg = "No valid test files found"
        print(f"Error: {error_msg}")
        return {"line": 0.0, "branch": 0.0, "error": error_msg}
    
    # Prepare environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(impl_dir.parent)
    
    # Run coverage with pytest
    # Use module path format for --source (coverage.py expects module paths, not directory paths)
    coverage_cmd = [
        "coverage", "run",
        "--source", "impl.cut",  # Use module path, not directory path
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
        
        # Extract run ID from test directory
        run_id = get_run_id_from_path(test_dir)
        
        metrics = {"line": 0.0, "branch": 0.0}
        if run_id:
            metrics["run_id"] = run_id
        
        # Check if coverage data was collected
        if "No data to report" in result.stdout or "No data to report" in result.stderr:
            print("ERROR: No coverage data collected. Tests may not have run.")
            metrics["error"] = "No coverage data collected - tests may not have run"
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                metrics_json = {
                    "line": 0.0,
                    "branch": None,
                    "error": "No coverage data collected - tests may not have run"
                }
                if run_id:
                    metrics_json["run_id"] = run_id
                with open(output_file, 'w') as f:
                    json.dump(metrics_json, f, indent=2)
            return metrics
        
        # Generate report in specified format and extract metrics
        coverage_data = None
        
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if report_format == "json":
                # Save full coverage JSON to a detailed file
                detailed_output = output_file.parent / f"{output_file.stem}_detailed.json"
                json_save_result = subprocess.run(
                    ["coverage", "json", "-o", str(detailed_output)],
                    cwd=impl_dir.parent,
                    capture_output=True,
                    text=True,
                )
                print(f"✓ Saved detailed JSON coverage report to: {detailed_output}")
                
                # Read back the saved file to extract metrics
                try:
                    with open(detailed_output, 'r') as f:
                        coverage_data = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not read saved coverage JSON: {e}")
                    # Fallback: try to get from stdout
                    json_result = subprocess.run(
                        ["coverage", "json", "-o", "-"],
                        capture_output=True,
                        text=True,
                        cwd=impl_dir.parent,
                    )
                    if json_result.returncode == 0 and json_result.stdout.strip():
                        try:
                            coverage_data = json.loads(json_result.stdout)
                        except json.JSONDecodeError:
                            pass
                
            elif report_format == "html":
                # Generate HTML report
                html_dir = output_file.parent / f"{output_file.stem}_html"
                subprocess.run(
                    ["coverage", "html", "-d", str(html_dir)],
                    cwd=impl_dir.parent,
                )
                print(f"✓ Saved HTML coverage report to: {html_dir}/")
                
                # Get JSON for metrics extraction
                json_result = subprocess.run(
                    ["coverage", "json", "-o", "-"],
                    capture_output=True,
                    text=True,
                    cwd=impl_dir.parent,
                )
                if json_result.returncode == 0 and json_result.stdout.strip():
                    try:
                        coverage_data = json.loads(json_result.stdout)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing coverage JSON: {e}")
                
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
                
                # Get JSON for metrics extraction
                json_result = subprocess.run(
                    ["coverage", "json", "-o", "-"],
                    capture_output=True,
                    text=True,
                    cwd=impl_dir.parent,
                )
                if json_result.returncode == 0 and json_result.stdout.strip():
                    try:
                        coverage_data = json.loads(json_result.stdout)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing coverage JSON: {e}")
        else:
            # No output file specified, get JSON from stdout
            json_result = subprocess.run(
                ["coverage", "json", "-o", "-"],
                capture_output=True,
                text=True,
                cwd=impl_dir.parent,
            )
            if json_result.returncode == 0 and json_result.stdout.strip():
                try:
                    coverage_data = json.loads(json_result.stdout)
                except json.JSONDecodeError as e:
                    print(f"Error parsing coverage JSON: {e}")
        
        # Extract metrics from coverage data
        if coverage_data:
            # Validate that files were tracked
            if not coverage_data.get("files"):
                print("WARNING: No files tracked in coverage data")
                metrics["error"] = "No files tracked in coverage data"
            else:
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
        else:
            print("WARNING: Could not extract coverage data")
            metrics["error"] = "Could not extract coverage data"
        
        # Always save metrics JSON for aggregation
        # The aggregate script expects files with "line" and "branch" keys at root level
        # Save metrics to the main output_file (this is what aggregate.py will read)
        if output_file:
            metrics_json = {
                "line": metrics.get("line", 0.0),
                "branch": metrics.get("branch"),
            }
            if "error" in metrics:
                metrics_json["error"] = metrics["error"]
            if run_id:
                metrics_json["run_id"] = run_id
            
            # Save metrics JSON to the expected output file (for aggregation)
            # When report_format == "json", we've already saved detailed JSON to _detailed.json
            # Now save simple metrics to the main output_file
            with open(output_file, 'w') as f:
                json.dump(metrics_json, f, indent=2)
            print(f"✓ Saved coverage metrics JSON to: {output_file}")
        
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

