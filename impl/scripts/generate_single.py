#!/usr/bin/env python3
"""Single-agent test case generation script."""

import argparse
import ast
import importlib
import inspect
import re
from pathlib import Path
from typing import Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.src.llm import call_local_llm


def load_cut_module(cut_module_name: str):
    """
    Dynamically load a CUT module from impl.cut.
    
    Args:
        cut_module_name: Name of the module (without .py extension)
        
    Returns:
        The imported module
    """
    try:
        module = importlib.import_module(f"impl.cut.{cut_module_name}")
        return module
    except ImportError as e:
        raise ImportError(
            f"Failed to import module 'impl.cut.{cut_module_name}'. "
            f"Make sure the file exists at impl/cut/{cut_module_name}.py. Error: {e}"
        )


def get_module_source_code(module):
    """
    Extract source code from a module.
    
    Args:
        module: The imported module
        
    Returns:
        String containing the module's source code
    """
    try:
        source = inspect.getsource(module)
        return source
    except OSError:
        # If source is not available, try to get it from file
        if hasattr(module, '__file__') and module.__file__:
            with open(module.__file__, 'r') as f:
                return f.read()
        raise ValueError(f"Cannot get source code for module {module}")


def load_prompt_template(template_path: Path = None) -> str:
    """
    Load prompt template from file.
    
    Args:
        template_path: Optional custom path to template. If None, uses default.
        
    Returns:
        Template string
    """
    if template_path is None:
        # Use default template
        script_dir = Path(__file__).parent
        template_path = script_dir.parent / "prompts" / "patterns" / "single_agent.txt"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    
    with open(template_path, 'r') as f:
        return f.read()


def extract_python_code_from_response(response: str) -> str:
    """
    Extract Python code from LLM response.
    Handles code blocks marked with ```python or ```.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Extracted Python code
    """
    # Try to find code blocks
    code_block_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        # Use the first code block found
        return matches[0].strip()
    
    # If no code blocks, assume the entire response is code
    # Remove any markdown formatting that might be present
    lines = response.split('\n')
    code_lines = []
    
    for line in lines:
        # Skip markdown headers and other formatting
        if line.strip().startswith('#') or not line.strip().startswith(('```', '---', '===')):
            code_lines.append(line)
    
    return '\n'.join(code_lines).strip()


def validate_test_code(code: str) -> Tuple[bool, str]:
    """
    Validate generated test code.
    
    Args:
        code: Python code string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if code is valid Python
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


def generate_single_tests(
    cut_module: str,
    output_dir: Path,
    num_tests: int = 10,
    prompt_template: Path = None,
) -> None:
    """
    Generate test cases using a single agent.
    
    Args:
        cut_module: Name of the module in impl/cut/ to test.
        output_dir: Directory to save generated test files.
        num_tests: Number of test cases to generate.
        prompt_template: Optional path to custom prompt template.
    """
    print(f"Generating {num_tests} test(s) for module '{cut_module}'...")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load CUT module
    print(f"Loading CUT module: impl.cut.{cut_module}")
    cut_module_obj = load_cut_module(cut_module)
    
    # Get source code
    code_under_test = get_module_source_code(cut_module_obj)
    print(f"Loaded {len(code_under_test)} characters of source code")
    
    # Load prompt template
    template = load_prompt_template(prompt_template)
    
    # Format prompt with CUT code
    prompt = template.format(code_under_test=code_under_test)
    
    # Add instruction for number of tests
    if num_tests > 1:
        prompt += f"\n\nGenerate approximately {num_tests} test functions."
    
    # Call LLM to generate test code
    print("Calling LLM to generate test code...")
    try:
        response = call_local_llm(
            prompt=prompt,
            temperature=0.7,
            max_tokens=4000,
        )
    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise
    
    # Extract Python code from response
    print("Extracting Python code from LLM response...")
    test_code = extract_python_code_from_response(response)
    
    # Validate generated code
    print("Validating generated test code...")
    is_valid, message = validate_test_code(test_code)
    print(f"Validation: {message}")
    
    if not is_valid:
        print("Warning: Generated code validation failed, but saving anyway...")
        print(f"Error: {message}")
    
    # Save generated test file
    test_filename = f"test_{cut_module}.py"
    test_file_path = output_dir / test_filename
    
    # Add import statement if not present
    if f"from impl.cut.{cut_module}" not in test_code and f"import {cut_module}" not in test_code:
        # Try to add import at the beginning
        import_line = f"from impl.cut import {cut_module}\n\n"
        test_code = import_line + test_code
    
    with open(test_file_path, 'w') as f:
        f.write(test_code)
    
    print(f"✓ Saved generated tests to: {test_file_path}")
    print(f"  File size: {len(test_code)} characters")


def main():
    parser = argparse.ArgumentParser(
        description="Generate test cases using a single agent"
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
        default=Path(__file__).parent.parent / "tests_generated" / "single",
        help="Directory to save generated test files",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=10,
        help="Number of test cases to generate",
    )
    parser.add_argument(
        "--prompt-template",
        type=Path,
        default=None,
        help="Optional path to custom prompt template",
    )
    
    args = parser.parse_args()
    generate_single_tests(
        cut_module=args.cut_module,
        output_dir=args.output_dir,
        num_tests=args.num_tests,
        prompt_template=args.prompt_template,
    )


if __name__ == "__main__":
    main()

