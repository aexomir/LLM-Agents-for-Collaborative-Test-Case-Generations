from impl.cut import calculator
import pytest


def test_add():
    """Test adding two numbers."""
    assert calculator.add(2.0, 3.0) == 5.0
    assert calculator.add(-1.0, -2.0) == -3.0
    assert calculator.add(0.0, 0.0) == 0.0


def test_subtract():
    """Test subtracting a number from another."""
    assert calculator.subtract(10.0, 5.0) == 5.0
    assert calculator.subtract(-1.0, -2.0) == 1.0
    assert calculator.subtract(0.0, 0.0) == 0.0


def test_multiply():
    """Test multiplying two numbers."""
    assert calculator.multiply(4.0, 6.0) == 24.0
    assert calculator.multiply(-2.0, -3.0) == 6.0
    assert calculator.multiply(0.0, 0.0) == 0.0


def test_divide():
    """Test dividing by zero."""
    with pytest.raises(ValueError):
        calculator.divide(10.0, 0.0)
    # Test normal division
    assert calculator.divide(10.0, 2.0) == 5.0


def test_power():
    """Test raising to a power."""
    assert calculator.power(2.0, 3) == 8.0
    assert calculator.power(2.0, -3) == 0.125
    assert calculator.power(0.0, 5.0) == 0.0


def test_factorial():
    """Test calculating factorial."""
    assert calculator.factorial(5) == 120
    assert calculator.factorial(0) == 1
    assert calculator.factorial(1) == 1


def test_divide_by_zero():
    """Test division by zero raises error."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(10.0, 0.0)


def test_factorial_negative():
    """Test factorial with negative number raises error."""
    with pytest.raises(ValueError, match="Factorial is not defined for negative numbers"):
        calculator.factorial(-1)


def test_negative_numbers():
    """Test negative numbers."""
    assert calculator.add(-1.0, -2.0) == -3.0
    assert calculator.subtract(10.0, -5.0) == 15.0
    assert calculator.multiply(-2.0, 3.0) == -6.0


def test_boundary_values():
    """Test edge case: boundary values."""
    assert calculator.divide(100.0, 2.0) == 50.0
    assert calculator.power(5.0, 3) == 125.0
    assert calculator.add(0.0, 0.0) == 0.0


def test_zero_operations():
    """Test operations with zero."""
    assert calculator.multiply(5.0, 0.0) == 0.0
    assert calculator.add(5.0, 0.0) == 5.0
    assert calculator.subtract(5.0, 0.0) == 5.0