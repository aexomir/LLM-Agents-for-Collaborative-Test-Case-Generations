#!/usr/bin/env python3
"""Evaluate diversity of generated test cases."""

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import List, Set, Dict, Any
import sys

from impl.scripts.test_run_utils import get_run_id_from_path


class TestFunctionAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze test function characteristics."""
    
    def __init__(self):
        self.test_functions = []
        self.current_function = None
    
    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            # Extract function info
            func_info = {
                'name': node.name,
                'ast_dump': ast.dump(node),
                'assertions': [],
                'calls': [],
                'literals': [],
                'num_lines': len(node.body),
            }
            
            # Analyze function body
            self.current_function = func_info
            self.generic_visit(node)
            self.test_functions.append(func_info)
            self.current_function = None
        else:
            self.generic_visit(node)
    
    def visit_Assert(self, node):
        if self.current_function is not None:
            # Record assertion pattern
            assertion_pattern = ast.dump(node.test)
            self.current_function['assertions'].append(assertion_pattern)
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if self.current_function is not None:
            # Record function calls
            if isinstance(node.func, ast.Name):
                self.current_function['calls'].append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                self.current_function['calls'].append(node.func.attr)
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        if self.current_function is not None:
            # Record literal values (test inputs)
            self.current_function['literals'].append(node.value)
        self.generic_visit(node)


def parse_test_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a test file and extract test function information."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        analyzer = TestFunctionAnalyzer()
        analyzer.visit(tree)
        return analyzer.test_functions
    except Exception as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
        return []


def calculate_syntactic_diversity(all_tests: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate syntactic diversity based on AST patterns."""
    if not all_tests:
        return {"diversity_score": 0.0, "unique_patterns": 0}
    
    # Count unique AST patterns
    ast_patterns = set()
    assertion_patterns = set()
    call_patterns = set()
    
    for test in all_tests:
        ast_patterns.add(test['ast_dump'])
        for assertion in test['assertions']:
            assertion_patterns.add(assertion)
        for call in test['calls']:
            call_patterns.add(call)
    
    # Calculate diversity score (unique patterns / total tests)
    diversity_score = len(ast_patterns) / len(all_tests)
    
    return {
        "diversity_score": diversity_score,
        "unique_ast_patterns": len(ast_patterns),
        "unique_assertions": len(assertion_patterns),
        "unique_calls": len(call_patterns),
        "total_tests": len(all_tests),
    }


def calculate_semantic_diversity(all_tests: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate semantic diversity based on input values and edge cases."""
    if not all_tests:
        return {"diversity_score": 0.0, "unique_values": 0}
    
    # Collect all literal values used as test inputs
    all_literals = []
    unique_literals = set()
    
    for test in all_tests:
        for literal in test['literals']:
            all_literals.append(literal)
            # Convert to hashable type
            try:
                unique_literals.add(str(literal))
            except:
                pass
    
    # Identify edge case patterns
    edge_case_count = 0
    edge_case_values = [0, 0.0, -1, '', None, True, False]
    
    for literal in all_literals:
        if literal in edge_case_values or literal == [] or literal == {}:
            edge_case_count += 1
    
    # Calculate diversity score
    if all_literals:
        diversity_score = len(unique_literals) / len(all_literals)
    else:
        diversity_score = 0.0
    
    return {
        "diversity_score": diversity_score,
        "unique_values": len(unique_literals),
        "total_values": len(all_literals),
        "edge_case_count": edge_case_count,
    }


def calculate_coverage_diversity(all_tests: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate diversity based on function coverage patterns."""
    if not all_tests:
        return {"diversity_score": 0.0, "unique_patterns": 0}
    
    # Track which functions each test calls
    test_signatures = []
    
    for test in all_tests:
        # Create signature based on called functions
        signature = tuple(sorted(set(test['calls'])))
        test_signatures.append(signature)
    
    # Count unique signatures
    unique_signatures = len(set(test_signatures))
    
    # Calculate diversity score
    diversity_score = unique_signatures / len(all_tests) if all_tests else 0.0
    
    return {
        "diversity_score": diversity_score,
        "unique_patterns": unique_signatures,
        "total_tests": len(all_tests),
    }


def eval_diversity(
    test_dir: Path,
    output_file: Path = None,
    diversity_metric: str = "syntactic",
) -> dict:
    """
    Evaluate diversity of generated test cases.
    
    Args:
        test_dir: Directory containing test files.
        output_file: Optional file to save diversity analysis results.
        diversity_metric: Type of diversity to measure ('syntactic', 'semantic', 'coverage').
        
    Returns:
        Dictionary with diversity metrics (e.g., {'syntactic_similarity': 0.3, 'unique_patterns': 15}).
    """
    # Validate test directory exists
    if not test_dir.exists():
        print(f"Error: Test directory does not exist: {test_dir}")
        return {"diversity_score": 0.0, "unique_patterns": 0, "error": "Test directory not found"}
    
    print(f"Evaluating {diversity_metric} diversity for tests in {test_dir}...")
    
    # Find all test files
    test_files = list(test_dir.glob("test_*.py"))
    
    if not test_files:
        print(f"Warning: No test files found in {test_dir}")
        return {"diversity_score": 0.0, "unique_patterns": 0, "error": "No test files found"}
    
    print(f"Found {len(test_files)} test file(s)")
    
    # Parse all test files
    all_tests = []
    for test_file in test_files:
        print(f"  Parsing: {test_file.name}")
        tests = parse_test_file(test_file)
        all_tests.extend(tests)
    
    print(f"Found {len(all_tests)} test function(s)")
    
    # Extract run ID from test directory
    run_id = get_run_id_from_path(test_dir)
    
    # Calculate diversity based on metric type
    if diversity_metric == "syntactic":
        metrics = calculate_syntactic_diversity(all_tests)
        print(f"\n✓ Syntactic Diversity Results:")
        print(f"  Diversity Score: {metrics['diversity_score']:.2f}")
        print(f"  Unique AST Patterns: {metrics['unique_ast_patterns']}")
        print(f"  Unique Assertions: {metrics['unique_assertions']}")
        print(f"  Unique Function Calls: {metrics['unique_calls']}")
        
    elif diversity_metric == "semantic":
        metrics = calculate_semantic_diversity(all_tests)
        print(f"\n✓ Semantic Diversity Results:")
        print(f"  Diversity Score: {metrics['diversity_score']:.2f}")
        print(f"  Unique Values: {metrics['unique_values']}")
        print(f"  Total Values: {metrics['total_values']}")
        print(f"  Edge Cases: {metrics['edge_case_count']}")
        
    elif diversity_metric == "coverage":
        metrics = calculate_coverage_diversity(all_tests)
        print(f"\n✓ Coverage Diversity Results:")
        print(f"  Diversity Score: {metrics['diversity_score']:.2f}")
        print(f"  Unique Patterns: {metrics['unique_patterns']}")
        print(f"  Total Tests: {metrics['total_tests']}")
    else:
        print(f"Error: Unknown diversity metric: {diversity_metric}")
        return {"diversity_score": 0.0, "unique_patterns": 0, "error": "Unknown metric"}
    
    # Add run ID to metrics if found
    if run_id:
        metrics["run_id"] = run_id
    
    # Save results if output file specified
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✓ Saved diversity analysis to: {output_file}")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate diversity of generated test cases"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        required=True,
        help="Directory containing test files",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional file to save diversity analysis results",
    )
    parser.add_argument(
        "--diversity-metric",
        type=str,
        default="syntactic",
        choices=["syntactic", "semantic", "coverage"],
        help="Type of diversity to measure",
    )
    
    args = parser.parse_args()
    metrics = eval_diversity(
        test_dir=args.test_dir,
        output_file=args.output_file,
        diversity_metric=args.diversity_metric,
    )
    print(f"Diversity metrics: {metrics}")


if __name__ == "__main__":
    main()

