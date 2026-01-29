#!/usr/bin/env python3
"""Single-agent test case generation script."""

import argparse
import ast
import importlib
import inspect
import os
import re
from pathlib import Path
from typing import Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.src.llm import call_llm
from impl.scripts.test_run_utils import (
    create_timestamped_output_dir,
    save_run_metadata,
)
from impl.scripts.test_quality_validator import TestQualityValidator


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
    use_timestamp: bool = True,
) -> Tuple[Path, str]:
    """
    Generate test cases using a single agent.
    
    Args:
        cut_module: Name of the module in impl/cut/ to test.
        output_dir: Base directory to save generated test files.
        num_tests: Number of test cases to generate.
        prompt_template: Optional path to custom prompt template.
        use_timestamp: If True, create timestamped subdirectory. If False, use output_dir directly.
        
    Returns:
        Tuple of (actual_output_directory, run_id)
    """
    print(f"Generating {num_tests} test(s) for module '{cut_module}'...")
    
    # Create timestamped output directory if requested
    if use_timestamp:
        base_dir = output_dir.parent if output_dir.name == "single" else output_dir.parent.parent
        actual_output_dir, run_id = create_timestamped_output_dir(base_dir, "single")
        print(f"Created timestamped directory: {actual_output_dir}")
        print(f"Run ID: {run_id}")
    else:
        actual_output_dir = output_dir
        run_id = None
        actual_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load CUT module
    print(f"Loading CUT module: impl.cut.{cut_module}")
    cut_module_obj = load_cut_module(cut_module)
    
    # Get source code
    code_under_test = get_module_source_code(cut_module_obj)
    print(f"Loaded {len(code_under_test)} characters of source code")
    
    # Get CUT module path for quality validation
    impl_dir = Path(__file__).parent.parent
    cut_module_path = impl_dir / "cut" / f"{cut_module}.py"
    
    # Load prompt template
    template = load_prompt_template(prompt_template)
    
    # Format prompt with CUT code and module name
    try:
        prompt = template.format(
            code_under_test=code_under_test,
            cut_module_name=cut_module,
            num_tests=num_tests
        )
    except KeyError:
        # Fallback for old template format
        prompt = template.format(code_under_test=code_under_test)
        if num_tests > 1:
            prompt += f"\n\nGenerate approximately {num_tests} test functions."
    
    # Initialize quality validator
    quality_validator = TestQualityValidator(cut_module, cut_module_path)
    
    # Generate test code with quality checks and retry logic
    max_retries = 2
    test_code = None
    best_quality = 0.0
    best_code = None
    
    for attempt in range(max_retries + 1):
        if attempt > 0:
            print(f"\nRetry attempt {attempt}/{max_retries} to improve test quality...")
            # Add feedback to prompt for retry
            if best_code:
                prompt += f"\n\nIMPORTANT: Previous attempt had quality issues. "
                prompt += "Ensure all tests have assertions, proper imports, and test actual function behavior."
        
        # Call LLM to generate test code
        provider = os.getenv("LLM_PROVIDER", "local" if not os.getenv("OPENAI_API_KEY") else "openai")
        if provider == "openai":
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b-instruct")
        
        print("Calling LLM to generate test code...")
        print(f"Provider: {provider}")
        print(f"Model: {model_name}")
        print(f"Prompt length: {len(prompt)} characters")
        
        try:
            response = call_llm(
                prompt=prompt,
                provider=provider,
                temperature=0.7 if attempt == 0 else 0.5,  # Lower temperature for retries
                max_tokens=3000,  # Reduced from 4000 to speed up generation
            )
        except Exception as e:
            error_msg = str(e)
            print(f"Error calling LLM: {e}")
            
            # If quota exceeded and we have retries left, suggest switching to local
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                if attempt < max_retries:
                    print("\n⚠️  OpenAI quota exceeded. Consider switching to local model:")
                    print("   unset OPENAI_API_KEY")
                    print("   export LLM_PROVIDER=local")
                    print("   Then re-run this script.\n")
            
            if attempt == max_retries:
                raise
            continue
        
        # Extract Python code from response
        print("Extracting Python code from LLM response...")
        test_code = extract_python_code_from_response(response)
        
        # Basic syntax validation
        is_valid, message = validate_test_code(test_code)
        if not is_valid:
            print(f"Syntax validation failed: {message}")
            if attempt < max_retries:
                continue
            else:
                print("Warning: Generated code validation failed, but saving anyway...")
        
        # Quality validation
        print("Running quality validation...")
        quality_valid, quality_warnings, quality_metrics = quality_validator.validate_test_quality(
            test_code, 
            strict=(attempt == max_retries)  # Only strict on final attempt
        )
        
        quality_score = quality_metrics.get("quality_percentage", 0.0)
        print(f"Quality score: {quality_score:.1f}%")
        
        if quality_warnings:
            print("Quality warnings:")
            for warning in quality_warnings[:5]:  # Show first 5 warnings
                print(f"  - {warning}")
        
        # Keep best attempt
        if quality_score > best_quality:
            best_quality = quality_score
            best_code = test_code
        
        # If quality is acceptable or this is the last attempt, use this code
        if quality_score >= 60.0 or attempt == max_retries:
            test_code = best_code if best_code else test_code
            break
    
    # Final quality report
    if best_code:
        final_valid, final_warnings, final_metrics = quality_validator.validate_test_quality(
            test_code, strict=False
        )
        print(f"\n✓ Final quality score: {final_metrics.get('quality_percentage', 0.0):.1f}%")
        print(f"  Test functions: {final_metrics.get('num_test_functions', 0)}")
        print(f"  Assertions: {final_metrics.get('num_assertions', 0)}")
        print(f"  Functions tested: {len(final_metrics.get('functions_tested', []))}")
        
        if final_warnings:
            suggestions = quality_validator.suggest_improvements(final_metrics)
            if suggestions:
                print("\nSuggestions for improvement:")
                for suggestion in suggestions[:3]:
                    print(f"  - {suggestion}")
    
    # Save generated test file under tests_generated
    test_filename = f"test_{cut_module}.py"
    test_file_path = actual_output_dir / test_filename
    
    # Add import statement if not present
    if f"from impl.cut.{cut_module}" not in test_code and f"import {cut_module}" not in test_code:
        # Try to add import at the beginning
        import_line = f"from impl.cut import {cut_module}\n\n"
        test_code = import_line + test_code
    
    with open(test_file_path, 'w') as f:
        f.write(test_code)
    
    print(f"✓ Saved generated tests to: {test_file_path}")
    print(f"  File size: {len(test_code)} characters")
    
    # Save run metadata
    if run_id:
        metadata_file = save_run_metadata(
            actual_output_dir,
            run_id,
            cut_module,
            "single",
            additional_info={
                "num_tests": num_tests,
                "test_file": test_filename,
            }
        )
        print(f"✓ Saved run metadata to: {metadata_file}")

    # Also create/overwrite a wrapper file in impl/tests so tools like
    # pytest can discover this suite automatically.
    # Use the actual output directory for the import path
    tests_dir = actual_output_dir.parent.parent / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create wrapper that imports from the timestamped directory
    # Calculate relative import path from impl/tests to the test file
    if run_id:
        # Path: impl/tests_generated/single/20250126_143022/test_calculator.py
        # Import: from impl.tests_generated.single.20250126_143022.test_calculator import *
        import_path = f"impl.tests_generated.single.{run_id}.test_{cut_module}"
    else:
        import_path = f"impl.tests_generated.single.test_{cut_module}"
    
    wrapper_path = tests_dir / f"test_{cut_module}_single.py"
    wrapper_code = (
        "\"\"\"Auto-generated wrapper for single-agent tests.\n"
        "Imports the generated tests so pytest see them under 'tests/'.\n"
        "\"\"\"\n\n"
        f"from {import_path} import *  # noqa: F401,F403\n"
    )
    with open(wrapper_path, "w") as f:
        f.write(wrapper_code)
    print(f"✓ Created test wrapper: {wrapper_path}")
    
    return actual_output_dir, run_id or "unknown"


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
        help="Base directory to save generated test files (will create timestamped subdirectory)",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Disable timestamped subdirectories (use output-dir directly)",
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
    output_dir, run_id = generate_single_tests(
        cut_module=args.cut_module,
        output_dir=args.output_dir,
        num_tests=args.num_tests,
        prompt_template=args.prompt_template,
        use_timestamp=not args.no_timestamp,
    )
    print(f"\n✓ Test generation complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Run ID: {run_id}")


if __name__ == "__main__":
    main()

