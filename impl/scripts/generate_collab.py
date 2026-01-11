#!/usr/bin/env python3
"""
Collaborative test case generation script.

This module implements multi-agent collaborative test generation where multiple
specialized agents generate test cases from different perspectives, which are
then merged and deduplicated to create a comprehensive test suite.

Research Context:
- Implements collaborative LLM agent workflow for test generation
- Compares multi-agent vs single-agent approaches
- Explores patterns of collaboration for higher-quality test cases
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
        # If source is not available, try to get it from file
        if hasattr(module, '__file__') and module.__file__:
            try:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    return f.read()
            except (OSError, IOError) as e:
                raise ValueError(f"Cannot read source file for module {module}: {e}")
        raise ValueError(f"Cannot get source code for module {module}")


def load_role_template(role_path: Path) -> str:
    """
    Load a role template from file.
    
    Args:
        role_path: Path to the role template file
        
    Returns:
        Template string with placeholders
        
    Raises:
        FileNotFoundError: If the template file does not exist
        IOError: If the file cannot be read
    """
    if not role_path.exists():
        raise FileNotFoundError(f"Role template not found: {role_path}")
    
    try:
        with open(role_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Error reading role template {role_path}: {e}")


def get_default_role_templates(num_agents: int) -> List[Path]:
    """
    Get default role template paths based on number of agents.
    
    Args:
        num_agents: Number of agents (determines which roles to use)
        
    Returns:
        List of role template paths
        
    Raises:
        ValueError: If num_agents is invalid
        FileNotFoundError: If required role templates are missing
    """
    if num_agents < 1:
        raise ValueError(f"Number of agents must be at least 1, got {num_agents}")
    if num_agents > 3:
        raise ValueError(
            f"Maximum 3 default role templates available, requested {num_agents}. "
            "Use --prompt-roles to specify custom roles."
        )
    
    script_dir = Path(__file__).parent
    roles_dir = script_dir.parent / "prompts" / "roles"
    
    # Default roles in priority order (based on testing theory)
    default_roles = [
        "tester_edge_cases.txt",      # Edge case and exception testing
        "tester_boundary.txt",         # Boundary value analysis
        "tester_integration.txt",      # Integration and workflow testing
    ]
    
    # Use first num_agents roles
    role_paths = [roles_dir / role_name for role_name in default_roles[:num_agents]]
    
    # Verify all files exist
    for role_path in role_paths:
        if not role_path.exists():
            raise FileNotFoundError(
                f"Default role template not found: {role_path}. "
                f"Expected roles directory at: {roles_dir}"
            )
    
    return role_paths


def extract_python_code_from_response(response: str) -> str:
    """
    Extract Python code from LLM response, handling various response formats.
    
    Handles:
    - Code blocks marked with ```python or ```
    - Plain text responses
    - Multiple code blocks (uses the first one)
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Extracted Python code string
    """
    # Try to find code blocks (most common format)
    code_block_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        # Use the first code block found
        code = matches[0].strip()
        # Remove any leading/trailing whitespace that might cause issues
        return code
    
    # If no code blocks, assume the entire response is code
    # Remove any markdown formatting that might be present
    lines = response.split('\n')
    code_lines = []
    
    for line in lines:
        # Skip markdown headers and separators
        stripped = line.strip()
        if not stripped.startswith(('```', '---', '===')):
            code_lines.append(line)
    
    return '\n'.join(code_lines).strip()


def extract_test_functions(code: str) -> List[ast.FunctionDef]:
    """
    Extract top-level test function definitions from Python code.
    
    Only extracts functions at module level (not nested in classes or other functions).
    Functions must start with 'test_' prefix (pytest convention).
    
    Args:
        code: Python code string
        
    Returns:
        List of AST FunctionDef nodes for test functions (top-level only)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Invalid syntax - return empty list
        return []
    
    test_functions = []
    
    # Only extract top-level functions (direct children of module)
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
        Function source code as string (including decorators)
    """
    # Try to use ast.get_source_segment (Python 3.8+)
    if hasattr(ast, 'get_source_segment'):
        try:
            func_code = ast.get_source_segment(source_code, func_node)
            if func_code:
                return func_code
        except (AttributeError, ValueError):
            # Fall back to line-based extraction
            pass
    
    # Fallback: use line numbers
    lines = source_code.split('\n')
    start_line = func_node.lineno - 1
    
    # Find the actual start (might have decorators above)
    # Walk backwards to find decorators
    actual_start = start_line
    for i in range(start_line - 1, -1, -1):
        if i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith('@'):
                actual_start = i
            else:
                break
    
    # Try to get end_lineno (Python 3.8+)
    if hasattr(func_node, 'end_lineno') and func_node.end_lineno:
        end_line = func_node.end_lineno
    else:
        # Estimate end line (conservative fallback)
        # Count lines in function body as approximation
        body_lines = 0
        for node in ast.walk(func_node):
            if hasattr(node, 'lineno'):
                body_lines = max(body_lines, node.lineno - func_node.lineno)
        end_line = func_node.lineno + body_lines + 5  # Add buffer
    
    # Get function code including decorators
    func_lines = lines[actual_start:end_line]
    return '\n'.join(func_lines)


def deduplicate_test_functions(test_functions: List[Tuple[str, str]]) -> List[str]:
    """
    Deduplicate test functions by name and code similarity.
    
    Removes exact duplicates based on:
    1. Function name (exact match)
    2. Normalized code content (whitespace-insensitive comparison)
    
    Args:
        test_functions: List of (function_name, function_code) tuples
        
    Returns:
        List of unique function code strings (preserves order of first occurrence)
    """
    seen_names = set()
    unique_functions = []  # List of (name, code) tuples
    
    for func_name, func_code in test_functions:
        # Skip if we've seen this function name (basic deduplication)
        if func_name in seen_names:
            continue
        
        # Check for code similarity (normalized comparison)
        normalized_code = re.sub(r'\s+', ' ', func_code).strip()
        is_duplicate = False
        
        for existing_name, existing_code in unique_functions:
            normalized_existing = re.sub(r'\s+', ' ', existing_code).strip()
            # If codes are identical after normalization, consider duplicate
            if normalized_code == normalized_existing:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_names.add(func_name)
            unique_functions.append((func_name, func_code))
    
    # Return just the code strings (maintain order)
    return [code for _, code in unique_functions]


def validate_test_code(code: str) -> Tuple[bool, str]:
    """
    Validate generated test code for syntax and test function presence.
    
    Args:
        code: Python code string to validate
        
    Returns:
        Tuple of (is_valid, message) where message describes validation result
    """
    # Check if code is valid Python syntax
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Invalid Python syntax: {e}"
    
    # Check if there are any test functions
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
    # Check for various import patterns
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


def generate_collab_tests(
    cut_module: str,
    output_dir: Path,
    num_agents: int = 3,
    num_tests: int = 10,
    prompt_roles: Optional[Path] = None,
) -> None:
    """
    Generate test cases using multiple collaborating agents with specialized roles.
    
    This function coordinates multiple LLM agents, each with a specialized testing
    perspective (edge cases, boundary values, integration scenarios). The agents
    generate tests independently, and the results are merged and deduplicated.
    
    Args:
        cut_module: Name of the module in impl/cut/ to test (without .py extension)
        output_dir: Directory to save generated test files
        num_agents: Number of collaborating agents (1-3 for default roles)
        num_tests: Target number of test cases to generate per agent
        prompt_roles: Optional path to directory containing custom role definitions
        
    Raises:
        ValueError: If no valid test functions are generated
        FileNotFoundError: If role templates or CUT module are missing
        ImportError: If CUT module cannot be imported
    """
    # Input validation
    if num_agents < 1:
        raise ValueError(f"Number of agents must be at least 1, got {num_agents}")
    if num_tests < 1:
        raise ValueError(f"Number of tests must be at least 1, got {num_tests}")
    
    print(f"Generating collaborative tests with {num_agents} agent(s) for module '{cut_module}'...")
    
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
    
    # Load role templates
    if prompt_roles:
        # Custom roles directory provided
        if not prompt_roles.is_dir():
            raise ValueError(f"Prompt roles path must be a directory: {prompt_roles}")
        roles_dir = prompt_roles
        role_paths = sorted(list(roles_dir.glob("*.txt")))[:num_agents]
        if len(role_paths) < num_agents:
            raise ValueError(
                f"Not enough role templates found in {roles_dir}. "
                f"Found {len(role_paths)}, need {num_agents}"
            )
    else:
        # Use default roles
        try:
            role_paths = get_default_role_templates(num_agents)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}")
            raise
    
    print(f"Using {len(role_paths)} role template(s): {[p.stem for p in role_paths]}")
    
    # Collect test code from all agents
    all_test_functions = []
    agent_responses = []
    successful_agents = 0
    
    for i, role_path in enumerate(role_paths, 1):
        print(f"\n--- Agent {i}/{len(role_paths)} ({role_path.stem}) ---")
        
        # Load role template
        try:
            role_template = load_role_template(role_path)
        except (FileNotFoundError, IOError) as e:
            print(f"Error loading role template: {e}")
            continue
        
        # Format prompt with CUT code and number of tests
        try:
            prompt = role_template.format(
                code_under_test=code_under_test,
                num_tests=num_tests
            )
        except KeyError as e:
            print(f"Error: Role template missing required placeholder: {e}")
            continue
        
        # Call LLM to generate test code
        print(f"Calling LLM for agent {i}...")
        try:
            response = call_local_llm(
                prompt=prompt,
                temperature=0.7,
                max_tokens=4000,
            )
            agent_responses.append(response)
        except Exception as e:
            print(f"Error calling LLM for agent {i}: {e}")
            continue
        
        # Extract Python code from response
        print(f"Extracting Python code from agent {i} response...")
        test_code = extract_python_code_from_response(response)
        
        if not test_code:
            print(f"Warning: No code extracted from agent {i} response")
            continue
        
        # Validate generated code
        is_valid, message = validate_test_code(test_code)
        print(f"Agent {i} validation: {message}")
        
        if is_valid:
            # Extract test functions from the code
            test_funcs = extract_test_functions(test_code)
            print(f"Agent {i} generated {len(test_funcs)} test function(s)")
            
            if test_funcs:
                # Get source code for each function
                for func_node in test_funcs:
                    try:
                        func_code = get_function_source_code(func_node, test_code)
                        all_test_functions.append((func_node.name, func_code))
                    except Exception as e:
                        print(f"Warning: Failed to extract function {func_node.name}: {e}")
                successful_agents += 1
            else:
                print(f"Warning: Agent {i} generated valid code but no test functions found")
        else:
            print(f"Warning: Agent {i} generated invalid code, skipping...")
    
    # Verify at least one agent succeeded
    if not all_test_functions:
        raise ValueError(
            "No valid test functions were generated by any agent! "
            "Please check: (1) LLM connection, (2) role templates, (3) CUT module validity."
        )
    
    if successful_agents == 0:
        raise ValueError(
            "All agents failed to generate valid test code. "
            "Please check your LLM configuration and role templates."
        )
    
    print(f"\n--- Merging Test Functions ---")
    print(f"Total test functions collected: {len(all_test_functions)}")
    print(f"Successful agents: {successful_agents}/{len(role_paths)}")
    
    # Deduplicate test functions
    unique_test_functions = deduplicate_test_functions(all_test_functions)
    print(f"After deduplication: {len(unique_test_functions)} unique test function(s)")
    
    if not unique_test_functions:
        raise ValueError("After deduplication, no test functions remain!")
    
    # Combine all test functions into a single file
    combined_code_parts = []
    
    # Add import statement if not present (check first function for existing imports)
    if unique_test_functions and not check_import_exists(unique_test_functions[0], cut_module):
        import_line = f"from impl.cut import {cut_module}\n\n"
        combined_code_parts.append(import_line)
    
    # Add all test functions with proper spacing
    for i, func_code in enumerate(unique_test_functions):
        combined_code_parts.append(func_code)
        # Add spacing between functions (but not after the last one)
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
    
    print(f"\n✓ Saved collaborative tests to: {test_file_path}")
    print(f"  File size: {len(final_test_code)} characters")
    print(f"  Total unique test functions: {len(unique_test_functions)}")
    print(f"  Agents contributing: {successful_agents}/{len(role_paths)}")


def main():
    """Main entry point for the collaborative test generation script."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate test cases using multiple collaborating agents with specialized roles. "
            "Each agent generates tests from a different perspective (edge cases, boundaries, "
            "integration), and results are merged and deduplicated."
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
        default=Path(__file__).parent.parent / "tests_generated" / "collab",
        help="Directory to save generated test files (default: impl/tests_generated/collab)",
    )
    parser.add_argument(
        "--num-agents",
        type=int,
        default=3,
        help="Number of collaborating agents (1-3 for default roles, default: 3)",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=10,
        help="Target number of test cases to generate per agent (default: 10)",
    )
    parser.add_argument(
        "--prompt-roles",
        type=Path,
        default=None,
        help="Optional path to directory containing custom role definitions",
    )
    
    args = parser.parse_args()
    
    try:
        generate_collab_tests(
            cut_module=args.cut_module,
            output_dir=args.output_dir,
            num_agents=args.num_agents,
            num_tests=args.num_tests,
            prompt_roles=args.prompt_roles,
        )
    except (ValueError, FileNotFoundError, ImportError, IOError) as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
