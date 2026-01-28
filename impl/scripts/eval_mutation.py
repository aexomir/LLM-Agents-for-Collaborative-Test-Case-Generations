#!/usr/bin/env python3
"""Evaluate mutation testing score of generated tests."""

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
import sys

from impl.scripts.test_run_utils import get_run_id_from_path


def eval_mutation(
    test_dir: Path,
    cut_module: str,
    output_file: Path = None,
    mutation_target: Path = None,
) -> dict:
    """
    Evaluate mutation testing score of generated tests.
    
    Args:
        test_dir: Directory containing test files.
        cut_module: Name of the CUT module to run mutation testing on.
        output_file: Optional file to save mutation testing results.
        mutation_target: Optional specific file to mutate (defaults to cut_module).
        
    Returns:
        Dictionary with mutation testing metrics (e.g., {'score': 0.75, 'killed': 15, 'survived': 5}).
    """
    # Validate test directory exists
    if not test_dir.exists():
        print(f"Error: Test directory does not exist: {test_dir}")
        return {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": "Test directory not found"}
    
    # Get the impl directory
    impl_dir = Path(__file__).parent.parent
    
    # Determine mutation target
    if mutation_target is None:
        mutation_target = impl_dir / "cut" / f"{cut_module}.py"
    
    if not mutation_target.exists():
        print(f"Error: Mutation target not found: {mutation_target}")
        return {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": "Mutation target not found"}
    
    print(f"Evaluating mutation testing for {cut_module} using tests in {test_dir}...")
    print(f"Mutation target: {mutation_target}")
    
    # Prepare environment
    env = os.environ.copy()
    # Make sure project root is on PYTHONPATH so tests can import impl.*
    env['PYTHONPATH'] = str(impl_dir.parent)
    # Tell mutmut to only run the specific test directory
    # Use absolute path to avoid any path resolution issues
    test_dir_abs = test_dir.resolve()
    env['MUTMUT_TEST_COMMAND'] = f"python -m pytest {test_dir_abs} -q"
    
    # Use a unique cache directory per test_dir to avoid cross-contamination
    # Use the impl_dir's .mutmut-cache but with a subdirectory for this specific test
    cache_base = impl_dir / ".mutmut-cache"
    cache_subdir = test_dir.name if test_dir.name else "default"
    cache_dir = cache_base / cache_subdir
    cache_dir.mkdir(parents=True, exist_ok=True)
    env['MUTMUT_CACHE_DIR'] = str(cache_dir)
    
    # Run mutmut
    # We rely on MUTMUT_TEST_COMMAND to define the pytest command,
    # so we don't pass --runner/--tests-dir here to avoid conflicts.
    # Use absolute path for mutation target
    mutation_target_abs = mutation_target.resolve()
    mutmut_run_cmd = [
        "mutmut", "run",
        "--paths-to-mutate", str(mutation_target_abs),
        "--no-progress",  # Disable progress bar for cleaner output
    ]
    
        print(f"Running: {' '.join(mutmut_run_cmd)}")
        print(f"Test command: {env.get('MUTMUT_TEST_COMMAND')}")
        print(f"Cache directory: {env.get('MUTMUT_CACHE_DIR')}")
        
        # First, verify that tests can run at all
        print("\nVerifying tests can run...")
        test_check_cmd = env['MUTMUT_TEST_COMMAND'].split()
        test_check_result = subprocess.run(
            test_check_cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=impl_dir.parent,
            timeout=60,
        )
        if test_check_result.returncode != 0:
            print(f"WARNING: Tests failed to run!")
            print(f"Test output: {test_check_result.stdout}")
            print(f"Test errors: {test_check_result.stderr}")
            print("Mutation testing may not work correctly if tests don't pass.")
        else:
            print("✓ Tests run successfully")
    
    try:
        # Run mutmut (it returns non-zero if mutations survived)
        result = subprocess.run(
            mutmut_run_cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=impl_dir.parent,  # Run from project root, not impl_dir
            timeout=300,  # 5 minute timeout
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Get mutmut results summary
        results_cmd = ["mutmut", "results"]
        results_result = subprocess.run(
            results_cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=impl_dir.parent,  # Run from project root
        )
        
            # Extract run ID from test directory
            run_id = get_run_id_from_path(test_dir)
            
            # Parse mutmut results
            metrics = {
                "score": 0.0,
                "killed": 0,
                "survived": 0,
                "timeout": 0,
                "suspicious": 0,
                "skipped": 0,
            }
            if run_id:
                metrics["run_id"] = run_id
        
        output = results_result.stdout
        print(output)
        
        # Parse results using regex.
        # Support both older "Label: X" format and newer
        # "Label 🙁 (X)" style lines that mutmut prints.
        killed_match = re.search(
            r'Killed(?:\s*[^\d(]+)?[:(]\s*(\d+)', output, re.IGNORECASE
        )
        survived_match = re.search(
            r'Survived(?:\s*[^\d(]+)?[:(]\s*(\d+)', output, re.IGNORECASE
        )
        timeout_match = re.search(
            r'Timeout(?:\s*[^\d(]+)?[:(]\s*(\d+)', output, re.IGNORECASE
        )
        suspicious_match = re.search(
            r'Suspicious(?:\s*[^\d(]+)?[:(]\s*(\d+)', output, re.IGNORECASE
        )
        skipped_match = re.search(
            r'Skipped(?:\s*[^\d(]+)?[:(]\s*(\d+)', output, re.IGNORECASE
        )
        
        if killed_match:
            metrics["killed"] = int(killed_match.group(1))
        if survived_match:
            metrics["survived"] = int(survived_match.group(1))
        if timeout_match:
            metrics["timeout"] = int(timeout_match.group(1))
        if suspicious_match:
            metrics["suspicious"] = int(suspicious_match.group(1))
        if skipped_match:
            metrics["skipped"] = int(skipped_match.group(1))
        
        # Calculate mutation score
        total_tested = metrics["killed"] + metrics["survived"]
        if total_tested > 0:
            metrics["score"] = metrics["killed"] / total_tested
        
        print(f"\n✓ Mutation Testing Results:")
        print(f"  Killed: {metrics['killed']}")
        print(f"  Survived: {metrics['survived']}")
        print(f"  Timeout: {metrics['timeout']}")
        print(f"  Suspicious: {metrics['suspicious']}")
        print(f"  Skipped: {metrics['skipped']}")
        print(f"  Score: {metrics['score']:.1%}")
        
        # Save results if output file specified
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"\n✓ Saved mutation testing results to: {output_file}")
        
        return metrics
        
    except subprocess.TimeoutExpired:
        print("Error: Mutation testing timed out after 5 minutes")
        return {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": "Timeout"}
    except FileNotFoundError:
        print("Error: mutmut not found. Install it with: pip install mutmut")
        return {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": "mutmut not installed"}
    except Exception as e:
        print(f"Error running mutation testing: {e}")
        return {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate mutation testing score of generated tests"
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
        help="Name of the CUT module to run mutation testing on",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional file to save mutation testing results",
    )
    parser.add_argument(
        "--mutation-target",
        type=Path,
        default=None,
        help="Optional specific file to mutate (defaults to cut_module)",
    )
    
    args = parser.parse_args()
    metrics = eval_mutation(
        test_dir=args.test_dir,
        cut_module=args.cut_module,
        output_file=args.output_file,
        mutation_target=args.mutation_target,
    )
    print(f"Mutation testing metrics: {metrics}")


if __name__ == "__main__":
    main()

