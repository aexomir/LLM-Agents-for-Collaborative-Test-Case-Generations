from impl.cut import calculator

def test_add_zero():
    """Test adding zero to a number."""
    assert add(0, 5) == 5

def test_add_out_of_range(a, b):
    """Test adding two numbers out of range."""
    with pytest.raises(ValueError):
        add(-1, a)

def test_subtract_zero():
    """Test subtracting zero from a number."""
    assert subtract(0, 5) == -5

def test_subtract_out_of_range(a, b):
    """Test subtracting two numbers out of range."""
    with pytest.raises(ValueError):
        subtract(-1, a)

def test_multiply_zero():
    """Test multiplying zero by a number."""
    assert multiply(0, 5) == 0

def test_multiply_out_of_range(a, b):
    """Test multiplying two numbers out of range."""
    with pytest.raises(ValueError):
        multiply(-1, a)

def test_divide_by_zero():
    """Test dividing by zero error."""
    with pytest.raises(ValueError):
        divide(0, 2)

def test_divide_out_of_range(a, b):
    """Test dividing two numbers out of range."""
    with pytest.raises(ValueError):
        divide(-1, a)

def test_power_zero():
    """Test raising ValueError when base is zero."""
    with pytest.raises(ValueError):
        power(0.5, 2)

def test_power_out_of_range(base, exponent):
    """Test raising ValueError when exponent is out of range."""
    with pytest.raises(ValueError):
        power(base, exponent)

def test_factorial_negative_number():
    """Test factorial for negative numbers."""
    assert factorial(-5) == 0

def test_factorial_zero_or_one(n):
    """Test factorial for zero or one."""
    assert factorial(n) == 1

def test_power_invalid_base():
    """Test raising ValueError when base is not a number."""
    with pytest.raises(ValueError):
        power(2.5, "a")

def test_power_invalid_exponent(base, exponent):
    """Test raising ValueError when exponent is not an integer."""
    with pytest.raises(ValueError):
        power(base, exponent)

def test_factorial_non_integer_input():
    """Test factorial for non-integer inputs."""
    assert factorial(1.5) == 0

def test_add_boundary():
    """Test boundary conditions of the add function."""
    assert add(1.0 + 2.0, 3.0) == 4.0

def test_add_boundary_plus(a, b):
    """Test boundary conditions of the add function with positive values."""
    assert add(a + 1.0, b) == a + b
    assert add(-a - 1.0, b) == a + b

def test_add_boundary_minus(a, b):
    """Test boundary conditions of the add function with negative values."""
    assert add(-a - 1.0, b) == a + b
    assert add(a + 1.0, -b) == a + b

def test_add_boundary_equivalent_class(a, b):
    """Test boundary conditions of the add function with equivalent class boundaries."""
    assert add(3.0, 4.0) == 7.0

def test_add_boundary_input_range_limit(a, b):
    """Test boundary conditions of the add function with input range limits."""
    assert add(-100.0 + 200.0, 3.0) == 205.0

def test_add_boundary_input_range_limit_edge(a, b):
    """Test boundary conditions of the add function with edge values at input range limits."""
    assert add(-100.0 + 1.0, 3.0) == -97.0
    assert add(200.0 + 2.0, 3.0) == 202.0

def test_subtract_boundary():
    """Test boundary conditions of the subtract function."""
    assert subtract(10.0 - 5.0, 15.0) == -20.0

def test_subtract_boundary_plus(a, b):
    """Test boundary conditions of the subtract function with positive values."""
    assert subtract(10.0 + 1.0, b) == 9.0
    assert subtract(-a - 1.0, b) == a + b

def test_subtract_boundary_minus(a, b):
    """Test boundary conditions of the subtract function with negative values."""
    assert subtract(-a - 1.0, b) == a + b
    assert subtract(10.0 + 1.0, -b) == a + b

def test_subtract_boundary_equivalent_class(a, b):
    """Test boundary conditions of the subtract function with equivalent class boundaries."""
    assert subtract(3.0 - 4.0, 5.0) == -1.0

def test_subtract_boundary_input_range_limit(a, b):
    """Test boundary conditions of the subtract function with input range limits."""
    assert subtract(-100.0 - 200.0, 3.0) == -203.0

def test_subtract_boundary_input_range_limit_edge(a, b):
    """Test boundary conditions of the subtract function with edge values at input range limits."""
    assert subtract(-100.0 - 1.0, 3.0) == -99.0
    assert subtract(200.0 + 2.0, 3.0) == 198.0

def test_multiply_boundary():
    """Test boundary conditions of the multiply function."""
    assert multiply(10.0 * 5.0, 2.0) == 50.0

def test_multiply_boundary_plus(a, b):
    """Test boundary conditions of the multiply function with positive values."""
    assert multiply(5.0 + 3.0, a) == 8.0
    assert multiply(-a - 1.0, b) == a + b

def test_multiply_boundary_minus(a, b):
    """Test boundary conditions of the multiply function with negative values."""
    assert multiply(-5.0 * 3.0, a) == -15.0
    assert multiply(10.0 + 1.0, -b) == a + b

def test_multiply_boundary_equivalent_class(a, b):
    """Test boundary conditions of the multiply function with equivalent class boundaries."""
    assert multiply(5.0 * 4.0, a) == 20.0

def test_multiply_boundary_input_range_limit(a, b):
    """Test boundary conditions of the multiply function with input range limits."""
    assert multiply(9.0 * 5.0, a) == 45.0

def test_multiply_boundary_input_range_limit_edge(a, b):
    """Test boundary conditions of the multiply function with edge values at input range limits."""
    assert multiply(9.0 * -5.0, a) == -45.0
    assert multiply(-1.0 + 2.0, a) == 3.0

def test_divide_boundary():
    """Test boundary conditions of the divide function."""
    with pytest.raises(ValueError):
        divide(10.0 / 2.0, 3.0)

def test_divide_boundary_plus(a, b):
    """Test boundary conditions of the divide function with positive values."""
    assert divide(5.0 + 3.0, a) == 2.0
    assert divide(-a - 1.0, b) == a + b

def test_divide_boundary_minus(a, b):
    """Test boundary conditions of the divide function with negative values."""
    assert divide(-5.0 - 3.0, a) == a + b
    assert divide(10.0 + 1.0, -b) == a + b

def test_divide_boundary_equivalent_class(a, b):
    """Test boundary conditions of the divide function with equivalent class boundaries."""
    assert divide(5.0 / 4.0, a) == 1.25

def test_divide_boundary_input_range_limit(a, b):
    """Test boundary conditions of the divide function with input range limits."""
    assert divide(4.0 / 3.0, a) == 1.3333333333333335

def test_divide_boundary_input_range_limit_edge(a, b):
    """Test boundary conditions of the divide function with edge values at input range limits."""
    assert divide(4.0 / -3.0, a) == -1.3333333333333335
    assert divide(-1.0 + 2.0, a) == 0.25

def test_power_boundary():
    """Test boundary conditions of the power function."""
    assert power(10.0 ** 5.0, 2.0) == 10000000.0

def test_power_boundary_plus(a, b):
    """Test boundary conditions of the power function with positive values."""
    assert power(5.0 + 3.0, a) == 125.0
    assert power(-a - 1.0, b) == a + b

def test_power_boundary_minus(a, b):
    """Test boundary conditions of the power function with negative values."""
    assert power(-5.0 * 3.0, a) == -125.0
    assert power(10.0 + 1.0, -b) == a + b

def test_power_boundary_equivalent_class(a, b):
    """Test boundary conditions of the power function with equivalent class boundaries."""
    assert power(5.0 ** 4.0, a) == 625.0

def test_power_boundary_input_range_limit(a, b):
    """Test boundary conditions of the power function with input range limits."""
    assert power(9.0 ** 5.0, a) == 59049.0

def test_power_boundary_input_range_limit_edge(a, b):
    """Test boundary conditions of the power function with edge values at input range limits."""
    assert power(9.0 ** -5.0, a) == 1/59049.0
    assert power(-1.0 + 2.0, a) == 1.25

def test_factorial_boundary():
    """Test boundary conditions of the factorial function."""
    assert factorial(10.0) == 3628800.0

def test_factorial_boundary_plus(a, b):
    """Test boundary conditions of the factorial function with positive values."""
    assert factorial(5.0 + 3.0) == 600
    assert factorial(-a - 1.0) == 0

def test_factorial_boundary_minus(a, b):
    """Test boundary conditions of the factorial function with negative values."""
    assert factorial(-5.0 - 3.0) == 0
    assert factorial(10.0 + 1.0) == 3628800.0

def test_factorial_boundary_equivalent_class(a, b):
    """Test boundary conditions of the factorial function with equivalent class boundaries."""
    assert factorial(5.0) == 120

def test_addition():
    """Test simple addition function."""
    assert add(2.5, 3.5) == 6

def test_subtraction():
    """Test subtraction function with positive and negative numbers."""
    assert subtract(10, 5) == 5
    with pytest.raises(ValueError):
        subtract(-1, 0)

def test_multiplication():
    """Test multiplication function with two positive numbers."""
    assert multiply(4.2, 3.8) == 15.56

def test_division():
    """Test division function with non-zero divisor and floating point numbers."""
    assert divide(12.5, 2.1) == 6.023

def test_powering():
    """Test raising base to the power of exponent."""
    assert power(3.14, 2) == 100.737

def test_factorial_non_negative_integer():
    """Test factorial function for non-negative integer input."""
    assert factorial(5) == 120

def test_factorial_zero_divisor():
    """Test factorial function with zero divisor."""
    with pytest.raises(ValueError):
        factorial(0)

def test_factorial_negative_integer():
    """Test factorial function for negative integer input."""
    with pytest.raises(ValueError):
        factorial(-1)

def test_addition_complex_input():
    """Test complex addition scenario using real numbers and decimals."""
    assert add(2.5, 3.8) == 6

def test_subtraction_complex_input():
    """Test subtraction scenario using real numbers and decimals."""
    with pytest.raises(ValueError):
        subtract(-1, 0)

def test_multiplication_complex_input():
    """Test complex multiplication scenario using floating point numbers."""
    assert multiply(4.2, 3.8) == 16.56