#!/usr/bin/env python3
"""
Validation script for collaborative test generation.

This script validates the structure and functionality of the collaborative
test generation implementation without requiring an LLM connection.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the functions we want to test
from impl.scripts.generate_collab import (
    load_cut_module,
    get_module_source_code,
    load_role_template,
    get_default_role_templates,
    extract_python_code_from_response,
    extract_test_functions,
    validate_test_code,
    check_import_exists,
)


def test_load_cut_module():
    """Test CUT module loading."""
    print("Testing: load_cut_module()")
    try:
        module = load_cut_module("calculator")
        print(f"  [OK] Successfully loaded module: {module}")
        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_get_module_source_code():
    """Test source code extraction."""
    print("\nTesting: get_module_source_code()")
    try:
        module = load_cut_module("calculator")
        source = get_module_source_code(module)
        print(f"  [OK] Successfully extracted source code ({len(source)} chars)")
        print(f"  First 100 chars: {source[:100]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_load_role_templates():
    """Test role template loading."""
    print("\nTesting: load_role_template() and get_default_role_templates()")
    try:
        # Test getting default templates
        templates = get_default_role_templates(3)
        print(f"  [OK] Successfully got {len(templates)} default templates")
        
        # Test loading each template
        for template_path in templates:
            template = load_role_template(template_path)
            print(f"  [OK] Loaded template: {template_path.name} ({len(template)} chars)")
            # Check for required placeholders
            if "{code_under_test}" in template and "{num_tests}" in template:
                print(f"    [OK] Contains required placeholders")
            else:
                print(f"    [FAIL] Missing required placeholders")
                return False
        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_extract_python_code():
    """Test Python code extraction from responses."""
    print("\nTesting: extract_python_code_from_response()")
    
    test_cases = [
        ("```python\ndef test_something():\n    pass\n```", "def test_something():\n    pass"),
        ("```\ndef test_other():\n    pass\n```", "def test_other():\n    pass"),
        ("def test_plain():\n    pass", "def test_plain():\n    pass"),
    ]
    
    all_passed = True
    for input_text, expected_pattern in test_cases:
        try:
            result = extract_python_code_from_response(input_text)
            if expected_pattern in result or "def test" in result:
                print(f"  [OK] Extracted code from: {input_text[:50]}...")
            else:
                print(f"  [FAIL] Unexpected result for: {input_text[:50]}")
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            all_passed = False
    
    return all_passed


def test_extract_test_functions():
    """Test test function extraction."""
    print("\nTesting: extract_test_functions()")
    
    test_code = """
from impl.cut import calculator

def test_add():
    assert calculator.add(1, 2) == 3

def test_subtract():
    assert calculator.subtract(5, 2) == 3

def helper_function():
    pass
"""
    
    try:
        functions = extract_test_functions(test_code)
        print(f"  [OK] Extracted {len(functions)} test functions")
        for func in functions:
            print(f"    - {func.name}")
        
        if len(functions) == 2:  # Should find test_add and test_subtract
            print(f"  [OK] Correct number of test functions extracted")
            return True
        else:
            print(f"  [FAIL] Expected 2 functions, got {len(functions)}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_validate_test_code():
    """Test code validation."""
    print("\nTesting: validate_test_code()")
    
    valid_code = """
from impl.cut import calculator

def test_something():
    assert True
"""
    
    invalid_code = "def not_a_test(): pass"  # No test_ prefix
    syntax_error = "def test_error(:"  # Syntax error
    
    test_cases = [
        (valid_code, True, "Valid test code"),
        (invalid_code, False, "Code without test functions"),
        (syntax_error, False, "Syntax error"),
    ]
    
    all_passed = True
    for code, should_be_valid, description in test_cases:
        try:
            is_valid, message = validate_test_code(code)
            if is_valid == should_be_valid:
                print(f"  [OK] {description}: {message[:60]}")
            else:
                print(f"  [FAIL] {description}: Expected {should_be_valid}, got {is_valid}")
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] Error with {description}: {e}")
            all_passed = False
    
    return all_passed


def test_check_import_exists():
    """Test import checking."""
    print("\nTesting: check_import_exists()")
    
    test_cases = [
        ("from impl.cut import calculator", "calculator", True),
        ("import calculator", "calculator", True),
        ("import impl.cut.calculator", "calculator", True),
        ("def test(): pass", "calculator", False),
    ]
    
    all_passed = True
    for code, module, should_exist in test_cases:
        try:
            exists = check_import_exists(code, module)
            if exists == should_exist:
                print(f"  [OK] Correctly detected import in: {code[:50]}")
            else:
                print(f"  [FAIL] Expected {should_exist}, got {exists} for: {code[:50]}")
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Collaborative Test Generation - Validation Tests")
    print("=" * 70)
    
    tests = [
        ("CUT Module Loading", test_load_cut_module),
        ("Source Code Extraction", test_get_module_source_code),
        ("Role Template Loading", test_load_role_templates),
        ("Python Code Extraction", test_extract_python_code),
        ("Test Function Extraction", test_extract_test_functions),
        ("Code Validation", test_validate_test_code),
        ("Import Detection", test_check_import_exists),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] {test_name} raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n[SUCCESS] All validation tests passed! Implementation structure is correct.")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} test(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

