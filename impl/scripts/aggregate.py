#!/usr/bin/env python3
"""Aggregate evaluation results from multiple test generation runs."""

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Dict, Any, List

import pandas as pd


def _infer_mode(name: str) -> str:
    """Infer generation mode (single/collab/competitive/unknown) from filename."""
    lowered = name.lower()
    if "single" in lowered:
        return "single"
    if "collab" in lowered or "collaborative" in lowered:
        return "collab"
    if "competitive" in lowered or "comp" in lowered:
        return "competitive"
    return "unknown"


def _infer_cut(name: str) -> str:
    """
    Infer CUT name from filename.
    
    We expect names like:
    - coverage_calculator_single.json
    - mutation_calculator_collab.json
    - diversity_calculator_competitive.json
    Fallback: 'unknown'.
    """
    m = re.search(r"(coverage|mutation|diversity)_([^_.]+)", name.lower())
    if m:
        return m.group(2)
    return "unknown"


def _classify_json_metrics(data: Dict[str, Any]) -> str:
    """Classify a JSON result file as coverage/mutation/diversity based on keys."""
    keys = set(data.keys())
    if {"line", "branch"} & keys:
        return "coverage"
    if {"score", "killed", "survived"} <= keys:
        return "mutation"
    if {"diversity_score"} <= keys:
        return "diversity"
    # Fallback: unknown metrics
    return "unknown"


def aggregate_results(
    results_dir: Path,
    output_file: Path = None,
    output_format: str = "csv",
) -> None:
    """
    Aggregate evaluation results from multiple test generation runs.
    
    This function scans a results directory for JSON result files produced by:
    - eval_coverage.py  (coverage metrics)
    - eval_mutation.py  (mutation testing metrics)
    - eval_diversity.py (diversity metrics)
    
    It combines them into a single table with one row per
    (CUT, mode, metric_type) trio and writes the table in the requested format.
    
    Expected filenames (flexible in practice):
    - coverage_<cut>_<mode>.json
    - mutation_<cut>_<mode>.json
    - diversity_<cut>_<mode>.json
    where <mode> is one of: single, collab, competitive.
    """
    if not results_dir.exists() or not results_dir.is_dir():
        print(f"Error: results directory does not exist: {results_dir}", file=sys.stderr)
        sys.exit(1)
    
    rows: List[Dict[str, Any]] = []
    
    for path in sorted(results_dir.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: failed to read JSON from {path}: {e}", file=sys.stderr)
            continue
        
        metric_type = _classify_json_metrics(data)
        mode = _infer_mode(path.name)
        cut = _infer_cut(path.name)
        
        row: Dict[str, Any] = {
            "file": path.name,
            "cut": cut,
            "mode": mode,
            "metric_type": metric_type,
        }
        
        # Extract run_id if present
        if "run_id" in data:
            row["run_id"] = data.get("run_id")
        
        if metric_type == "coverage":
            row["coverage_line"] = data.get("line")
            row["coverage_branch"] = data.get("branch")
            # Handle error field if present
            if "error" in data:
                row["coverage_error"] = data.get("error")
        elif metric_type == "mutation":
            row["mutation_score"] = data.get("score")
            row["mutation_killed"] = data.get("killed")
            row["mutation_survived"] = data.get("survived")
            row["mutation_timeout"] = data.get("timeout")
            row["mutation_suspicious"] = data.get("suspicious")
            row["mutation_skipped"] = data.get("skipped")
            # Handle error field if present
            if "error" in data:
                row["mutation_error"] = data.get("error")
        elif metric_type == "diversity":
            # We don't know which diversity metric was used (syntactic/semantic/coverage),
            # so record all common fields and let the filename disambiguate.
            row["diversity_score"] = data.get("diversity_score")
            row["diversity_unique_patterns"] = data.get("unique_patterns")
            row["diversity_unique_ast_patterns"] = data.get("unique_ast_patterns")
            row["diversity_unique_assertions"] = data.get("unique_assertions")
            row["diversity_unique_calls"] = data.get("unique_calls")
            row["diversity_unique_values"] = data.get("unique_values")
            row["diversity_total_values"] = data.get("total_values")
            row["diversity_edge_case_count"] = data.get("edge_case_count")
            row["diversity_total_tests"] = data.get("total_tests")
            # Handle error field if present
            if "error" in data:
                row["diversity_error"] = data.get("error")
        else:
            # Unknown metrics: keep raw keys so nothing is lost
            for k, v in data.items():
                row[f"raw_{k}"] = v
        
        rows.append(row)
    
    if not rows:
        print(f"No JSON result files found in {results_dir}", file=sys.stderr)
        print(f"Looking for files matching: coverage_*.json, mutation_*.json, diversity_*.json", file=sys.stderr)
        return
    
    # Print summary of what was found
    metric_counts = {}
    for row in rows:
        metric_type = row.get("metric_type", "unknown")
        metric_counts[metric_type] = metric_counts.get(metric_type, 0) + 1
    
    print(f"Found {len(rows)} result file(s):", file=sys.stderr)
    for metric_type, count in sorted(metric_counts.items()):
        print(f"  {metric_type}: {count} file(s)", file=sys.stderr)
    
    df = pd.DataFrame(rows)
    # Sort for a stable, readable table
    # Include run_id in sort if it exists
    sort_columns = ["cut", "mode", "metric_type"]
    if "run_id" in df.columns:
        sort_columns.insert(1, "run_id")  # Insert after cut, before mode
    sort_columns.append("file")
    df = df.sort_values(by=sort_columns)
    
    # Replace None with empty string for better CSV readability (pandas will use NaN which is fine)
    # But for CSV output, we'll let pandas handle it naturally
    
    if output_file is None:
        # Fallback: print to stdout in a simple CSV-like format
        print(df.to_csv(index=False))
        return
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if output_format == "csv":
        # Use na_rep to make missing values more readable
        df.to_csv(output_file, index=False, na_rep="")
    elif output_format == "json":
        df.to_json(output_file, orient="records", indent=2)
    elif output_format == "html":
        df.to_html(output_file, index=False)
    else:
        print(f"Error: unsupported output format: {output_format}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ Aggregated results written to {output_file} ({output_format})")


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate evaluation results from multiple test generation runs"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Directory containing evaluation result files",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="File to save aggregated results",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="csv",
        choices=["csv", "json", "html"],
        help="Format for aggregated output",
    )
    
    args = parser.parse_args()
    aggregate_results(
        results_dir=args.results_dir,
        output_file=args.output_file,
        output_format=args.output_format,
    )


if __name__ == "__main__":
    main()

