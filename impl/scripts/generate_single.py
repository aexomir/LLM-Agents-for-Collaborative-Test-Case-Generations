#!/usr/bin/env python3
"""Single-agent test case generation script."""

import argparse
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from impl.src.llm import call_local_llm


def generate_single_tests(
    cut_module: str,
    output_dir: Path,
    num_tests: int = 10,
    prompt_template: str = None,
) -> None:
    """
    Generate test cases using a single agent.
    
    Args:
        cut_module: Name of the module in impl/cut/ to test.
        output_dir: Directory to save generated test files.
        num_tests: Number of test cases to generate.
        prompt_template: Optional path to custom prompt template.
        
    TODO:
        - Import the CUT module dynamically
        - Load prompt template (from prompts/patterns/ or custom)
        - Call LLM to generate test code
        - Parse and validate generated test code
        - Save as valid pytest file(s) to output_dir
        - Ensure test functions are prefixed with 'test_'
    """
    # TODO: Implement single-agent test generation
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"TODO: Generate {num_tests} tests for {cut_module} -> {output_dir}")


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

