from impl.cut import calculator

import pytest
from impl.cut.calculator import add, subtract, multiply, divide, power, factorial

def test_add_normal():
    """Test normal use case."""
    assert add(2.0, 3.0) == 5.0
    assert add(-1.0, 2.0) == -1.0
    assert add(0.0, 0.0) == 0.0

def test_add_edge_cases():
    """Test edge cases (empty inputs, boundary values, None values)."""
    with pytest.raises(ValueError):
        add(None, 3.0)
    with pytest.raises(ValueError):
        add(1.0, None)

def test_add_invalid_inputs():
    """Test error case (invalid input types)."""
    with pytest.raises(TypeError):
        add("hello", 3.0)

def test_add_negative_numbers():
    """Test normal use case with negative numbers."""
    assert add(-2.0, -3.0) == -5.0
    assert add(1.0, -4.0) == -3.0

def test_subtract_normal():
    """Test normal use case."""
    assert subtract(10.0, 2.0) == 8.0
    assert subtract(-7.0, 3.0) == -10.0
    assert subtract(0.0, 0.0) == 0.0

def test_subtract_edge_cases():
    """Test edge cases (empty inputs, boundary values, None values)."""
    with pytest.raises(ValueError):
        subtract(None, 2.0)
    with pytest.raises(ValueError):
        subtract(1.0, None)

def test_subtract_invalid_inputs():
    """Test error case (invalid input types)."""
    with pytest.raises(TypeError):
        subtract("hello", 3.0)

def test_multiply_normal():
    """Test normal use case."""
    assert multiply(2.0, 3.0) == 6.0
    assert multiply(-1.0, 2.0) == -2.0
    assert multiply(0.0, 0.0) == 0.0

def test_multiply_edge_cases():
    """Test edge cases (empty inputs, boundary values, None values)."""
    with pytest.raises(ValueError):
        multiply(None, 3.0)
    with pytest.raises(ValueError):
        multiply(1.0, None)

def test_multiply_invalid_inputs():
    """Test error case (invalid input types)."""
    with pytest.raises(TypeError):
        multiply("hello", 3.0)

def test_divide_normal():
    """Test normal use case."""
    assert divide(10.0, 2.0) == 5.0
    assert divide(-7.0, 3.0) == -2.3333333333333335
    assert divide(0.0, 0.0) == float('inf')

def test_divide_edge_cases():
    """Test edge cases (empty inputs, boundary values, None values)."""
    with pytest.raises(ValueError):
        divide(None, 3.0)
    with pytest.raises(ValueError):
        divide(1.0, None)

def test_divide_invalid_inputs():
    """Test error case (invalid input types)."""
    with pytest.raises(TypeError):
        divide("hello", 3.0)

def test_power_normal():
    """Test normal use case."""
    assert power(2.0, 3.0) == 8.0
    assert power(-1.0, 4.0) == -1.0

def test_power_edge_cases():
    """Test edge cases (empty inputs, boundary values, None values)."""
    with pytest.raises(ValueError):
        power(1.0, 3.0)
    with pytest.raises(ValueError):
        power(-2.0, 5.0)

def test_power_invalid_inputs():
    """Test error case (invalid input types)."""
    with pytest.raises(TypeError):
        power("hello", 3.0)

def test_factorial_normal():
    """Test normal use case."""
    assert factorial(5) == 120
    assert factorial(-1) == float('inf')
    assert factorial(0) == 1

def test_factorial_edge_cases():
    """Test edge cases (empty inputs, boundary values, None values)."""
    with pytest.raises(ValueError):
        factorial(None)
    with pytest.raises(ValueError):
        factorial(1.0)

def test_factorial_invalid_inputs():
    """Test error case (invalid input types)."""
    with pytest.raises(TypeError):
        factorial("hello")