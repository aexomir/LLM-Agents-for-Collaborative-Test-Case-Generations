#!/usr/bin/env python3
"""Evaluate mutation testing score of generated tests using a simple custom approach."""

import argparse
import ast
import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys
from typing import List, Tuple, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.scripts.test_run_utils import get_run_id_from_path


class SimpleMutator(ast.NodeTransformer):
    """Simple AST-based mutator for mutation testing."""
    
    def __init__(self, target_mutation_id=None):
        self.mutations = []
        self.mutation_id = 0
        self.target_mutation_id = target_mutation_id  # If set, only apply this mutation
        self.current_mutation_id = 0
    
    def visit_BinOp(self, node):
        """Mutate binary operators."""
        self.current_mutation_id += 1
        
        if isinstance(node.op, ast.Add):
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'operator',
                'original': '+',
                'mutated': '-',
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            
            # Only apply mutation if this is the target, or if no target specified (discovery mode)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.BinOp(left=self.visit(node.left), op=ast.Sub(), right=self.visit(node.right))
        elif isinstance(node.op, ast.Sub):
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'operator',
                'original': '-',
                'mutated': '+',
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.BinOp(left=self.visit(node.left), op=ast.Add(), right=self.visit(node.right))
        elif isinstance(node.op, ast.Mult):
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'operator',
                'original': '*',
                'mutated': '/',
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.BinOp(left=self.visit(node.left), op=ast.Div(), right=self.visit(node.right))
        elif isinstance(node.op, ast.Div):
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'operator',
                'original': '/',
                'mutated': '*',
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.BinOp(left=self.visit(node.left), op=ast.Mult(), right=self.visit(node.right))
        elif isinstance(node.op, ast.Eq):
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'comparison',
                'original': '==',
                'mutated': '!=',
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.Compare(left=self.visit(node.left), ops=[ast.NotEq()], comparators=[self.visit(node.right)])
        elif isinstance(node.op, ast.NotEq):
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'comparison',
                'original': '!=',
                'mutated': '==',
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.Compare(left=self.visit(node.left), ops=[ast.Eq()], comparators=[self.visit(node.right)])
        
        return self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Mutate comparison operators."""
        if len(node.ops) == 1:
            self.current_mutation_id += 1
            op = node.ops[0]
            if isinstance(op, ast.Lt):
                mutation_info = {
                    'id': self.current_mutation_id,
                    'type': 'comparison',
                    'original': '<',
                    'mutated': '>=',
                    'line': node.lineno
                }
                self.mutations.append(mutation_info)
                if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                    return ast.Compare(left=self.visit(node.left), ops=[ast.GtE()], comparators=[self.visit(c) for c in node.comparators])
            elif isinstance(op, ast.Gt):
                mutation_info = {
                    'id': self.current_mutation_id,
                    'type': 'comparison',
                    'original': '>',
                    'mutated': '<=',
                    'line': node.lineno
                }
                self.mutations.append(mutation_info)
                if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                    return ast.Compare(left=self.visit(node.left), ops=[ast.LtE()], comparators=[self.visit(c) for c in node.comparators])
            elif isinstance(op, ast.LtE):
                mutation_info = {
                    'id': self.current_mutation_id,
                    'type': 'comparison',
                    'original': '<=',
                    'mutated': '>',
                    'line': node.lineno
                }
                self.mutations.append(mutation_info)
                if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                    return ast.Compare(left=self.visit(node.left), ops=[ast.Gt()], comparators=[self.visit(c) for c in node.comparators])
            elif isinstance(op, ast.GtE):
                mutation_info = {
                    'id': self.current_mutation_id,
                    'type': 'comparison',
                    'original': '>=',
                    'mutated': '<',
                    'line': node.lineno
                }
                self.mutations.append(mutation_info)
                if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                    return ast.Compare(left=self.visit(node.left), ops=[ast.Lt()], comparators=[self.visit(c) for c in node.comparators])
        
        return self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Mutate constants (numbers)."""
        if isinstance(node.value, (int, float)) and node.value != 0:
            self.current_mutation_id += 1
            mutated_value = node.value + 1 if node.value > 0 else node.value - 1
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'constant',
                'original': str(node.value),
                'mutated': str(mutated_value),
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.Constant(value=mutated_value)
        return self.generic_visit(node)
    
    def visit_Num(self, node):  # Python < 3.8 compatibility
        """Mutate numbers (Python < 3.8)."""
        if isinstance(node.n, (int, float)) and node.n != 0:
            self.current_mutation_id += 1
            mutated_value = node.n + 1 if node.n > 0 else node.n - 1
            mutation_info = {
                'id': self.current_mutation_id,
                'type': 'constant',
                'original': str(node.n),
                'mutated': str(mutated_value),
                'line': node.lineno
            }
            self.mutations.append(mutation_info)
            if self.target_mutation_id is None or self.current_mutation_id == self.target_mutation_id:
                return ast.Num(n=mutated_value)
        return self.generic_visit(node)


def create_mutation(source_code: str, mutator: SimpleMutator) -> Tuple[str, List[Dict]]:
    """Create a mutated version of the source code."""
    try:
        tree = ast.parse(source_code)
        mutated_tree = mutator.visit(tree)
        
        # Convert AST back to source code
        if hasattr(ast, 'unparse'):
            # Python 3.9+
            mutated_code = ast.unparse(mutated_tree)
        else:
            # Fallback for Python < 3.9: use compile and reconstruct
            # This is a simplified approach - for production, install astor
            try:
                import astor
                mutated_code = astor.to_source(mutated_tree)
            except ImportError:
                # Very simple fallback: use regex-based mutation on source
                print("Warning: Using simplified mutation (install astor for better results)")
                mutated_code = _simple_regex_mutation(source_code, mutator.mutations, mutator.target_mutation_id)
        
        return mutated_code, mutator.mutations
    except Exception as e:
        print(f"Warning: Failed to create AST mutation: {e}")
        # Fallback to regex-based mutation
        try:
            mutated_code = _simple_regex_mutation(source_code, mutator.mutations, mutator.target_mutation_id)
            return mutated_code, mutator.mutations
        except Exception as e2:
            print(f"Error: Both AST and regex mutation failed: {e2}")
            return source_code, mutator.mutations


def _simple_regex_mutation(source_code: str, mutations: List[Dict], target_id: int = None) -> str:
    """Simple regex-based mutation fallback."""
    if not mutations:
        return source_code
    
    lines = source_code.split('\n')
    mutated_lines = lines.copy()
    
    for mutation in mutations:
        if target_id is not None and mutation['id'] != target_id:
            continue
        
        line_idx = mutation['line'] - 1
        if 0 <= line_idx < len(mutated_lines):
            line = mutated_lines[line_idx]
            original = mutation['original']
            mutated = mutation['mutated']
            
            # Simple string replacement (not perfect but works for basic cases)
            if original in line:
                mutated_lines[line_idx] = line.replace(original, mutated, 1)
                if target_id is not None:
                    break  # Only apply one mutation
    
    return '\n'.join(mutated_lines)


def run_tests(test_dir: Path, env: Dict[str, str], timeout: int = 30) -> Tuple[int, str, str]:
    """Run pytest tests and return exit code, stdout, stderr."""
    python_exe = sys.executable
    test_cmd = [python_exe, "-m", "pytest", str(test_dir.resolve()), "-q", "--tb=short"]
    
    try:
        result = subprocess.run(
            test_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=test_dir.parent.parent.parent,  # Project root
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Test execution timed out"
    except Exception as e:
        return -1, "", str(e)


def eval_mutation(
    test_dir: Path,
    cut_module: str,
    output_file: Path = None,
    mutation_target: Path = None,
    max_mutations: int = 20,
) -> dict:
    """
    Evaluate mutation testing score using a simple custom approach.
    
    Args:
        test_dir: Directory containing test files.
        cut_module: Name of the CUT module to run mutation testing on.
        output_file: Optional file to save mutation testing results.
        mutation_target: Optional specific file to mutate (defaults to cut_module).
        max_mutations: Maximum number of mutations to test (default: 20).
        
    Returns:
        Dictionary with mutation testing metrics.
    """
    # Validate test directory exists
    if not test_dir.exists():
        error_msg = f"Test directory does not exist: {test_dir}"
        print(f"Error: {error_msg}")
        result = {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": error_msg}
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        return result
    
    # Get the impl directory
    impl_dir = Path(__file__).parent.parent
    
    # Determine mutation target
    if mutation_target is None:
        mutation_target = impl_dir / "cut" / f"{cut_module}.py"
    
    if not mutation_target.exists():
        error_msg = f"Mutation target not found: {mutation_target}"
        print(f"Error: {error_msg}")
        result = {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": error_msg}
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        return result
    
    print(f"Evaluating mutation testing for {cut_module}")
    print(f"Mutation target: {mutation_target}")
    print(f"Test directory: {test_dir}")
    
    # Validate test directory
    from impl.scripts.test_run_utils import validate_test_directory
    test_files, valid_count = validate_test_directory(test_dir)
    
    if not test_files or valid_count == 0:
        error_msg = "No valid test files found"
        print(f"Error: {error_msg}")
        result = {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": error_msg}
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        return result
    
    print(f"Found {len(test_files)} test file(s), {valid_count} valid")
    
    # Prepare environment
    env = os.environ.copy()
    pythonpath = str(impl_dir.parent)
    env['PYTHONPATH'] = pythonpath
    
    # First, verify that original tests can run
    print("\nStep 1: Verifying original tests can run...")
    exit_code, stdout, stderr = run_tests(test_dir, env)
    
    if exit_code == -1:
        error_msg = f"Tests failed to run: {stderr}"
        print(f"ERROR: {error_msg}")
        print(f"stdout: {stdout}")
        result = {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": error_msg}
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        return result
    
    if exit_code == 0:
        print("✓ Original tests pass")
    else:
        print(f"⚠ Original tests have failures (exit code: {exit_code})")
        print("This is OK - we'll still test mutations")
    
    # Read the original source code
    print("\nStep 2: Reading source code...")
    try:
        with open(mutation_target, 'r') as f:
            original_source = f.read()
    except Exception as e:
        error_msg = f"Failed to read mutation target: {e}"
        print(f"ERROR: {error_msg}")
        result = {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": error_msg}
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        return result
    
    # Discover all possible mutations first
    print("\nStep 3: Discovering mutations...")
    discovery_mutator = SimpleMutator(target_mutation_id=None)  # Discovery mode
    _, all_mutations = create_mutation(original_source, discovery_mutator)
    
    if not all_mutations:
        error_msg = "No mutations could be generated - code may be too simple"
        print(f"WARNING: {error_msg}")
        result = {"score": 0.0, "killed": 0, "survived": 0, "timeout": 0, "error": error_msg}
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        return result
    
    # Limit number of mutations to test
    mutations_to_test = all_mutations[:max_mutations]
    print(f"Discovered {len(all_mutations)} mutations, testing {len(mutations_to_test)}")
    
    # Test each mutation
    print("\nStep 4: Testing mutations...")
    killed = 0
    survived = 0
    timeout_count = 0
    error_count = 0
    
    backup_file = mutation_target.with_suffix('.py.backup')
    
    try:
        # Test mutations one at a time
        for i, mutation_info in enumerate(mutations_to_test, 1):
            print(f"\nTesting mutation {i}/{len(mutations_to_test)}: {mutation_info['type']} at line {mutation_info['line']} ({mutation_info['original']} -> {mutation_info['mutated']})")
            
            # Create mutator for this specific mutation
            single_mutator = SimpleMutator(target_mutation_id=mutation_info['id'])
            
            # Create mutation (only this one will be applied)
            mutated_code, _ = create_mutation(original_source, single_mutator)
            
            # Backup original if first mutation
            if i == 1:
                shutil.copy2(mutation_target, backup_file)
            
            try:
                # Replace with mutated version
                mutation_target.write_text(mutated_code)
                
                # Run tests
                exit_code, stdout, stderr = run_tests(test_dir, env, timeout=15)
                
                if exit_code == -1:
                    timeout_count += 1
                    print(f"  ⏱ Timeout")
                elif exit_code != 0:
                    killed += 1
                    print(f"  ✓ Killed (tests failed)")
                else:
                    survived += 1
                    print(f"  ✗ Survived (tests passed)")
                
            except Exception as e:
                error_count += 1
                print(f"  ⚠ Error: {e}")
            finally:
                # Restore original file after each test
                if backup_file.exists():
                    shutil.copy2(backup_file, mutation_target)
        
    finally:
        # Final cleanup
        if backup_file.exists():
            backup_file.unlink()
    
    # Calculate metrics
    total_tested = killed + survived
    score = killed / total_tested if total_tested > 0 else 0.0
    
    run_id = get_run_id_from_path(test_dir)
    
    metrics = {
        "score": score,
        "killed": killed,
        "survived": survived,
        "timeout": timeout_count,
        "suspicious": 0,
        "skipped": len(mutations) - len(mutations_to_test),
    }
    
    if run_id:
        metrics["run_id"] = run_id
    
    print(f"\n{'='*60}")
    print(f"Mutation Testing Results:")
    print(f"  Killed: {killed}")
    print(f"  Survived: {survived}")
    print(f"  Timeout: {timeout_count}")
    print(f"  Skipped: {metrics['skipped']}")
    print(f"  Total Tested: {total_tested}")
    if total_tested > 0:
        print(f"  Score: {score:.1%}")
    print(f"{'='*60}")
    
    # Save results
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✓ Saved results to: {output_file}")
    
    return metrics


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
    parser.add_argument(
        "--max-mutations",
        type=int,
        default=20,
        help="Maximum number of mutations to test (default: 20)",
    )
    
    args = parser.parse_args()
    metrics = eval_mutation(
        test_dir=args.test_dir,
        cut_module=args.cut_module,
        output_file=args.output_file,
        mutation_target=args.mutation_target,
        max_mutations=args.max_mutations,
    )
    print(f"\nFinal metrics: {json.dumps(metrics, indent=2)}")


if __name__ == "__main__":
    main()
