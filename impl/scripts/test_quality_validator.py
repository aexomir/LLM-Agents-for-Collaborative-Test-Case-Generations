#!/usr/bin/env python3
"""Enhanced test quality validation and checking."""

import ast
import re
from typing import List, Tuple, Dict, Any, Set
from pathlib import Path
import importlib.util


class TestQualityValidator:
    """Validates test code quality beyond basic syntax checking."""
    
    def __init__(self, cut_module_name: str, cut_module_path: Path = None):
        """
        Initialize validator.
        
        Args:
            cut_module_name: Name of the CUT module (e.g., 'calculator')
            cut_module_path: Optional path to CUT module file
        """
        self.cut_module_name = cut_module_name
        self.cut_module_path = cut_module_path
        self.cut_functions = self._extract_cut_functions()
    
    def _extract_cut_functions(self) -> Set[str]:
        """Extract function names from CUT module."""
        functions = set()
        
        if self.cut_module_path and self.cut_module_path.exists():
            try:
                with open(self.cut_module_path, 'r') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.add(node.name)
            except Exception:
                pass
        
        return functions
    
    def validate_test_quality(
        self, 
        test_code: str, 
        strict: bool = True
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Comprehensive test quality validation.
        
        Args:
            test_code: Python test code to validate
            strict: If True, enforce stricter quality requirements
            
        Returns:
            Tuple of (is_valid, list_of_warnings, quality_metrics)
        """
        warnings = []
        metrics = {
            "num_test_functions": 0,
            "num_assertions": 0,
            "functions_tested": set(),
            "has_imports": False,
            "has_docstrings": 0,
            "duplicate_tests": [],
            "empty_tests": [],
            "tests_without_assertions": [],
        }
        
        try:
            tree = ast.parse(test_code)
        except SyntaxError as e:
            return False, [f"Invalid Python syntax: {e}"], metrics
        
        # Check for imports
        has_cut_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and self.cut_module_name in node.module:
                    has_cut_import = True
                    metrics["has_imports"] = True
                elif any(alias.name == self.cut_module_name for alias in node.names):
                    has_cut_import = True
                    metrics["has_imports"] = True
            elif isinstance(node, ast.Import):
                if any(alias.name == self.cut_module_name for alias in node.names):
                    has_cut_import = True
                    metrics["has_imports"] = True
        
        if not has_cut_import and strict:
            warnings.append(
                f"Missing import for CUT module '{self.cut_module_name}'. "
                f"Tests should import from 'impl.cut.{self.cut_module_name}'"
            )
        
        # Analyze test functions
        test_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions.append(node)
                    metrics["num_test_functions"] += 1
                    
                    # Check for docstring
                    if (ast.get_docstring(node) or 
                        (node.body and isinstance(node.body[0], ast.Expr) and 
                         isinstance(node.body[0].value, ast.Str))):
                        metrics["has_docstrings"] += 1
                    
                    # Check if test function is empty or has no assertions
                    has_assertion = False
                    has_meaningful_code = False
                    function_calls = []
                    
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Assert):
                            has_assertion = True
                            metrics["num_assertions"] += 1
                        elif isinstance(stmt, ast.Call):
                            has_meaningful_code = True
                            if isinstance(stmt.func, ast.Name):
                                function_calls.append(stmt.func.id)
                            elif isinstance(stmt.func, ast.Attribute):
                                function_calls.append(stmt.func.attr)
                    
                    if not has_meaningful_code:
                        metrics["empty_tests"].append(node.name)
                        warnings.append(f"Test '{node.name}' appears to be empty or has no meaningful code")
                    
                    if not has_assertion:
                        metrics["tests_without_assertions"].append(node.name)
                        if strict:
                            warnings.append(
                                f"Test '{node.name}' has no assertions. "
                                "Tests should verify expected behavior with assert statements."
                            )
                    
                    # Track which CUT functions are being tested
                    for func_name in function_calls:
                        if func_name in self.cut_functions:
                            metrics["functions_tested"].add(func_name)
        
        if metrics["num_test_functions"] == 0:
            return False, ["No test functions found (functions must start with 'test_')"], metrics
        
        # Check for duplicate test logic (simple heuristic)
        test_signatures = []
        for test_func in test_functions:
            # Create a simple signature based on function calls and assertions
            calls = []
            assertions = []
            for node in ast.walk(test_func):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
                elif isinstance(node, ast.Assert):
                    # Extract assertion pattern
                    if isinstance(node.test, ast.Compare):
                        assertions.append("compare")
                    elif isinstance(node.test, ast.Call):
                        assertions.append("call")
            
            signature = (tuple(sorted(calls)), tuple(sorted(assertions)))
            if signature in test_signatures:
                metrics["duplicate_tests"].append(test_func.name)
            else:
                test_signatures.append(signature)
        
        if metrics["duplicate_tests"]:
            warnings.append(
                f"Potential duplicate tests detected: {', '.join(metrics['duplicate_tests'])}"
            )
        
        # Check coverage of CUT functions
        if self.cut_functions:
            untested = self.cut_functions - metrics["functions_tested"]
            if untested and strict:
                warnings.append(
                    f"Functions not tested: {', '.join(sorted(untested))}. "
                    "Consider adding tests for all public functions."
                )
        
        # Quality score calculation
        quality_score = 0.0
        max_score = 10.0
        
        if metrics["num_test_functions"] > 0:
            quality_score += 2.0  # Has test functions
        if metrics["has_imports"]:
            quality_score += 1.0  # Has imports
        if metrics["num_assertions"] > 0:
            quality_score += min(2.0, metrics["num_assertions"] / metrics["num_test_functions"])  # Assertions per test
        if metrics["has_docstrings"] / max(1, metrics["num_test_functions"]) > 0.5:
            quality_score += 1.0  # Most tests have docstrings
        if len(metrics["functions_tested"]) > 0:
            quality_score += min(2.0, len(metrics["functions_tested"]) / max(1, len(self.cut_functions)))  # Function coverage
        if len(metrics["empty_tests"]) == 0:
            quality_score += 1.0  # No empty tests
        if len(metrics["tests_without_assertions"]) == 0:
            quality_score += 1.0  # All tests have assertions
        
        metrics["quality_score"] = quality_score
        metrics["quality_percentage"] = (quality_score / max_score) * 100
        
        # Convert set to list for JSON serialization
        metrics["functions_tested"] = list(metrics["functions_tested"])
        
        is_valid = len(warnings) == 0 or not strict
        
        return is_valid, warnings, metrics
    
    def suggest_improvements(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate suggestions for improving test quality."""
        suggestions = []
        
        if metrics["num_test_functions"] == 0:
            suggestions.append("Add test functions with 'test_' prefix")
        
        if not metrics["has_imports"]:
            suggestions.append(
                f"Add import statement: 'from impl.cut import {self.cut_module_name}'"
            )
        
        if metrics["num_assertions"] == 0:
            suggestions.append("Add assert statements to verify expected behavior")
        
        if metrics["tests_without_assertions"]:
            suggestions.append(
                f"Add assertions to tests: {', '.join(metrics['tests_without_assertions'])}"
            )
        
        if metrics["empty_tests"]:
            suggestions.append(
                f"Implement test logic for: {', '.join(metrics['empty_tests'])}"
            )
        
        if self.cut_functions:
            untested = set(self.cut_functions) - set(metrics["functions_tested"])
            if untested:
                suggestions.append(
                    f"Add tests for functions: {', '.join(sorted(untested))}"
                )
        
        if metrics["has_docstrings"] / max(1, metrics["num_test_functions"]) < 0.5:
            suggestions.append("Add docstrings to test functions explaining what they test")
        
        return suggestions
