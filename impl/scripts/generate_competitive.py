#!/usr/bin/env python3
"""
Competitive test case generation script.

This module implements competitive/adversarial test generation where multiple
agents compete to generate better test cases. This follows principles from
adversarial testing, competitive fuzzing, and multi-agent systems research.

Architecture:
- Agent 1 generates initial test suite using standard test generation
- Agent 2 reviews Agent 1's tests and generates competing tests based on
  competition mode (adversarial, diversity, coverage)
- Tests are merged and deduplicated to create a comprehensive competitive test suite

Competition Modes:
- adversarial: Agent 2 finds bugs/edge cases Agent 1 missed (gap analysis)
- diversity: Agent 2 generates tests that maximize diversity from Agent 1's tests
- coverage: Agent 2 targets uncovered code paths and branches

Research Context:
- Implements competitive LLM agent workflow for test generation
- Explores adversarial testing patterns and methodologies
- Compares competitive vs collaborative vs single-agent approaches
- Aligns with research on multi-agent systems and competitive test generation
- Supports evaluation of collaboration patterns for test quality
"""

import argparse
import ast
import importlib
import inspect
import re
from pathlib import Path
from typing import List, Tuple, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.src.llm import call_local_llm


def load_cut_module(cut_module_name: str):
    """
    Dynamically load a Code Under Test (CUT) module from impl.cut.
    
    Args:
        cut_module_name: Name of the module (without .py extension)
        
    Returns:
        The imported module object
        
    Raises:
        ImportError: If the module cannot be imported
    """
    try:
        module = importlib.import_module(f"impl.cut.{cut_module_name}")
        return module
    except ImportError as e:
        raise ImportError(
            f"Failed to import module 'impl.cut.{cut_module_name}'. "
            f"Make sure the file exists at impl/cut/{cut_module_name}.py. Error: {e}"
        )


def get_module_source_code(module) -> str:
    """
    Extract source code from a module.
    
    Args:
        module: The imported module object
        
    Returns:
        String containing the module's complete source code
        
    Raises:
        ValueError: If source code cannot be extracted
    """
    try:
        source = inspect.getsource(module)
        return source
    except OSError:
        if hasattr(module, '__file__') and module.__file__:
            try:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    return f.read()
            except (OSError, IOError) as e:
                raise ValueError(f"Cannot read source file for module {module}: {e}")
        raise ValueError(f"Cannot get source code for module {module}")


def load_competitive_template(competition_mode: str) -> Path:
    """
    Get the path to the competitive template for the given mode.
    
    Args:
        competition_mode: Mode of competition ('adversarial', 'diversity', 'coverage')
        
    Returns:
        Path to the template file
        
    Raises:
        ValueError: If competition_mode is invalid
        FileNotFoundError: If template file doesn't exist
    """
    script_dir = Path(__file__).parent
    template_path = script_dir.parent / "prompts" / "competitive" / f"{competition_mode}.txt"
    
    if not template_path.exists():
        raise FileNotFoundError(
            f"Competitive template not found: {template_path}. "
            f"Available modes: adversarial, diversity, coverage"
        )
    
    return template_path


def load_template(template_path: Path) -> str:
    """
    Load a template from file.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        Template string
        
    Raises:
        IOError: If the file cannot be read
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Error reading template {template_path}: {e}")


def extract_python_code_from_response(response: str) -> str:
    """
    Extract Python code from LLM response.
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Extracted Python code string
    """
    # Try to find code blocks
    code_block_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # If no code blocks, assume the entire response is code
    lines = response.split('\n')
    code_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(('```', '---', '===')):
            code_lines.append(line)
    
    return '\n'.join(code_lines).strip()


def extract_test_functions(code: str) -> List[ast.FunctionDef]:
    """
    Extract top-level test function definitions from Python code.
    
    Args:
        code: Python code string
        
    Returns:
        List of AST FunctionDef nodes for test functions (top-level only)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    test_functions = []
    
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                test_functions.append(node)
    
    return test_functions


def get_function_source_code(func_node: ast.FunctionDef, source_code: str) -> str:
    """
    Extract complete source code for a function including decorators.
    
    Args:
        func_node: AST FunctionDef node
        source_code: Original source code string
        
    Returns:
        Function source code as string
    """
    if hasattr(ast, 'get_source_segment'):
        try:
            func_code = ast.get_source_segment(source_code, func_node)
            if func_code:
                return func_code
        except (AttributeError, ValueError):
            pass
    
    # Fallback: use line numbers
    lines = source_code.split('\n')
    start_line = func_node.lineno - 1
    
    # Find decorators
    actual_start = start_line
    for i in range(start_line - 1, -1, -1):
        if i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith('@'):
                actual_start = i
            else:
                break
    
    if hasattr(func_node, 'end_lineno') and func_node.end_lineno:
        end_line = func_node.end_lineno
    else:
        body_lines = 0
        for node in ast.walk(func_node):
            if hasattr(node, 'lineno'):
                body_lines = max(body_lines, node.lineno - func_node.lineno)
        end_line = func_node.lineno + body_lines + 5
    
    func_lines = lines[actual_start:end_line]
    return '\n'.join(func_lines)


def format_existing_tests(test_functions: List[Tuple[str, str]]) -> str:
    """
    Format existing test functions as a string for inclusion in prompts.
    
    Args:
        test_functions: List of (function_name, function_code) tuples
        
    Returns:
        Formatted string of test code
    """
    if not test_functions:
        return "# No existing tests"
    
    code_parts = []
    for func_name, func_code in test_functions:
        code_parts.append(func_code)
        code_parts.append("\n\n")
    
    return ''.join(code_parts).strip()


def deduplicate_test_functions(test_functions: List[Tuple[str, str]]) -> List[str]:
    """
    Deduplicate test functions by name and code similarity.
    
    This function removes duplicate test functions based on:
    1. Function name (exact match) - prevents duplicate function names
    2. Normalized code content (whitespace-insensitive comparison) - removes code duplicates
    
    Note: This uses normalized string comparison. For more sophisticated similarity
    detection (AST-based or semantic similarity), see future enhancements. The current
    approach preserves diversity while removing exact duplicates.
    
    Args:
        test_functions: List of (function_name, function_code) tuples
        
    Returns:
        List of unique function code strings (preserves order of first occurrence)
    """
    seen_names = set()
    unique_functions = []
    
    for func_name, func_code in test_functions:
        if func_name in seen_names:
            continue
        
        normalized_code = re.sub(r'\s+', ' ', func_code).strip()
        is_duplicate = False
        
        for existing_name, existing_code in unique_functions:
            normalized_existing = re.sub(r'\s+', ' ', existing_code).strip()
            if normalized_code == normalized_existing:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_names.add(func_name)
            unique_functions.append((func_name, func_code))
    
    return [code for _, code in unique_functions]


def validate_test_code(code: str) -> Tuple[bool, str]:
    """
    Validate generated test code.
    
    Args:
        code: Python code string to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Invalid Python syntax: {e}"
    
    test_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                test_functions.append(node.name)
    
    if not test_functions:
        return False, "No test functions found (functions should start with 'test_')"
    
    return True, f"Valid code with {len(test_functions)} test function(s): {', '.join(test_functions)}"


def check_import_exists(code: str, cut_module: str) -> bool:
    """
    Check if the code already contains an import statement for the CUT module.
    
    Args:
        code: Python code string
        cut_module: Name of the module to check for
        
    Returns:
        True if import exists, False otherwise
    """
    patterns = [
        f"from impl.cut import {cut_module}",
        f"from impl.cut.{cut_module} import",
        f"import {cut_module}",
        f"import impl.cut.{cut_module}",
    ]
    
    for pattern in patterns:
        if pattern in code:
            return True
    
    return False


def generate_competitive_tests(
    cut_module: str,
    output_dir: Path,
    num_agents: int = 2,
    num_tests: int = 10,
    competition_mode: str = "adversarial",
    max_iterations: int = 2,
) -> None:
    """
    Generate test cases using competitive/adversarial agents.
    
    This function implements a competitive workflow based on adversarial testing
    and competitive multi-agent systems. The workflow consists of:
    
    1. Agent 1 generates initial test suite using standard test generation
    2. Agent 2 reviews Agent 1's tests and generates competing tests based on
       the competition mode
    3. Tests from both agents are merged and deduplicated
    
    Competition Modes (based on testing research):
    - adversarial: Agent 2 performs gap analysis to find bugs/edge cases Agent 1 missed
      (follows adversarial testing and fault-based testing principles)
    - diversity: Agent 2 generates tests that maximize diversity from Agent 1's tests
      (follows test suite diversity optimization principles)
    - coverage: Agent 2 targets uncovered code paths and branches
      (follows coverage-guided test generation principles)
    
    Note on Iterations: The current implementation performs one competitive round
    (Agent 1 -> Agent 2). The max_iterations parameter is included for future
    enhancement where multiple competitive rounds could be implemented with
    convergence detection.
    
    Args:
        cut_module: Name of the module in impl/cut/ to test (without .py extension)
        output_dir: Directory to save generated test files
        num_agents: Number of competing agents (default: 2, minimum: 2)
        num_tests: Target number of test cases to generate per agent
        competition_mode: Mode of competition ('adversarial', 'diversity', 'coverage')
        max_iterations: Maximum number of competitive iterations (default: 2, reserved for future use)
        
    Raises:
        ValueError: If no valid test functions are generated or parameters are invalid
        FileNotFoundError: If templates or CUT module are missing
        ImportError: If CUT module cannot be imported
        IOError: If test file cannot be written
    """
    # Input validation
    if num_agents < 2:
        raise ValueError(f"Competitive generation requires at least 2 agents, got {num_agents}")
    if num_tests < 1:
        raise ValueError(f"Number of tests must be at least 1, got {num_tests}")
    if competition_mode not in ['adversarial', 'diversity', 'coverage']:
        raise ValueError(f"Invalid competition_mode: {competition_mode}. Must be one of: adversarial, diversity, coverage")
    
    print(f"Generating competitive tests with {num_agents} agent(s) in '{competition_mode}' mode for module '{cut_module}'...")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load CUT module
    print(f"Loading CUT module: impl.cut.{cut_module}")
    try:
        cut_module_obj = load_cut_module(cut_module)
    except ImportError as e:
        print(f"Error: {e}")
        raise
    
    # Get source code
    try:
        code_under_test = get_module_source_code(cut_module_obj)
        print(f"Loaded {len(code_under_test)} characters of source code")
    except ValueError as e:
        print(f"Error: {e}")
        raise
    
    # Load competitive template
    try:
        template_path = load_competitive_template(competition_mode)
        competitive_template = load_template(template_path)
        print(f"Loaded competitive template: {competition_mode}")
    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"Error: {e}")
        raise
    
    # Load initial prompt template (use single agent template for Agent 1)
    script_dir = Path(__file__).parent
    initial_template_path = script_dir.parent / "prompts" / "patterns" / "single_agent.txt"
    
    if not initial_template_path.exists():
        raise FileNotFoundError(f"Initial template not found: {initial_template_path}")
    
    initial_template = load_template(initial_template_path)
    
    # Collect all test functions
    all_test_functions = []
    
    # Agent 1: Generate initial tests
    print(f"\n--- Agent 1: Initial Test Generation ---")
    try:
        prompt = initial_template.format(code_under_test=code_under_test)
        prompt += f"\n\nGenerate approximately {num_tests} test functions."
        
        print("Calling LLM for Agent 1...")
        response = call_local_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=4000,
        )
        
        test_code = extract_python_code_from_response(response)
        is_valid, message = validate_test_code(test_code)
        print(f"Agent 1 validation: {message}")
        
        if is_valid:
            test_funcs = extract_test_functions(test_code)
            print(f"Agent 1 generated {len(test_funcs)} test function(s)")
            
            for func_node in test_funcs:
                func_code = get_function_source_code(func_node, test_code)
                all_test_functions.append((func_node.name, func_code))
        else:
            print(f"Warning: Agent 1 generated invalid code, skipping...")
            raise ValueError("Agent 1 failed to generate valid test code")
    except Exception as e:
        print(f"Error with Agent 1: {e}")
        raise ValueError(f"Agent 1 failed: {e}")
    
    if not all_test_functions:
        raise ValueError("Agent 1 failed to generate any test functions!")
    
    # Agent 2: Generate competing tests
    print(f"\n--- Agent 2: Competitive Test Generation ({competition_mode} mode) ---")
    
    # Format existing tests for the competitive prompt
    existing_tests_str = format_existing_tests(all_test_functions)
    
    try:
        prompt = competitive_template.format(
            code_under_test=code_under_test,
            existing_tests=existing_tests_str,
            num_tests=num_tests
        )
        
        print("Calling LLM for Agent 2...")
        response = call_local_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=4000,
        )
        
        test_code = extract_python_code_from_response(response)
        is_valid, message = validate_test_code(test_code)
        print(f"Agent 2 validation: {message}")
        
        if is_valid:
            test_funcs = extract_test_functions(test_code)
            print(f"Agent 2 generated {len(test_funcs)} test function(s)")
            
            for func_node in test_funcs:
                func_code = get_function_source_code(func_node, test_code)
                all_test_functions.append((func_node.name, func_code))
        else:
            print(f"Warning: Agent 2 generated invalid code, skipping...")
    except Exception as e:
        print(f"Error with Agent 2: {e}")
        # Continue even if Agent 2 fails - we still have Agent 1's tests
    
    if not all_test_functions:
        raise ValueError("No valid test functions were generated by any agent!")
    
    # Deduplicate test functions
    print(f"\n--- Merging and Deduplicating Test Functions ---")
    print(f"Total test functions collected: {len(all_test_functions)}")
    
    unique_test_functions = deduplicate_test_functions(all_test_functions)
    print(f"After deduplication: {len(unique_test_functions)} unique test function(s)")
    
    if not unique_test_functions:
        raise ValueError("After deduplication, no test functions remain!")
    
    # Combine all test functions into a single file
    combined_code_parts = []
    
    # Add import statement if not present
    if unique_test_functions and not check_import_exists(unique_test_functions[0], cut_module):
        import_line = f"from impl.cut import {cut_module}\n\n"
        combined_code_parts.append(import_line)
    
    # Add all test functions with proper spacing
    for i, func_code in enumerate(unique_test_functions):
        combined_code_parts.append(func_code)
        if i < len(unique_test_functions) - 1:
            combined_code_parts.append("\n\n")
    
    final_test_code = ''.join(combined_code_parts).strip()
    
    # Validate the combined code
    print("\nValidating combined test code...")
    is_valid, message = validate_test_code(final_test_code)
    print(f"Combined code validation: {message}")
    
    if not is_valid:
        print("Warning: Combined code validation failed, but saving anyway...")
        print(f"Error details: {message}")
    
    # Save generated test file
    test_filename = f"test_{cut_module}.py"
    test_file_path = output_dir / test_filename
    
    try:
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(final_test_code)
    except IOError as e:
        raise IOError(f"Failed to write test file to {test_file_path}: {e}")
    
    print(f"\n[OK] Saved competitive tests to: {test_file_path}")
    print(f"  File size: {len(final_test_code)} characters")
    print(f"  Total unique test functions: {len(unique_test_functions)}")
    print(f"  Competition mode: {competition_mode}")


def main():
    """Main entry point for the competitive test generation script."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate test cases using competitive/adversarial agents. "
            "Agents compete to generate better tests through different strategies "
            "(adversarial, diversity, coverage)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--cut-module",
        type=str,
        required=True,
        help="Name of the module in impl/cut/ to test (e.g., 'calculator')",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "tests_generated" / "competitive",
        help="Directory to save generated test files (default: impl/tests_generated/competitive)",
    )
    parser.add_argument(
        "--num-agents",
        type=int,
        default=2,
        help="Number of competing agents (default: 2, minimum: 2)",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=10,
        help="Target number of test cases to generate per agent (default: 10)",
    )
    parser.add_argument(
        "--competition-mode",
        type=str,
        default="adversarial",
        choices=["adversarial", "diversity", "coverage"],
        help="Mode of competition between agents (default: adversarial)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum number of competitive iterations (default: 2, currently not used)",
    )
    
    args = parser.parse_args()
    
    try:
        generate_competitive_tests(
            cut_module=args.cut_module,
            output_dir=args.output_dir,
            num_agents=args.num_agents,
            num_tests=args.num_tests,
            competition_mode=args.competition_mode,
            max_iterations=args.max_iterations,
        )
    except (ValueError, FileNotFoundError, ImportError, IOError) as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
