from impl.cut import humaneval_subset

def test_has_close_elements_normal_case():
    """Test normal use case with valid inputs."""
    result = humaneval_subset.has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])
    assert result is True

def test_has_close_elements_no_close_elements():
    """Test case where no two elements are close."""
    result = humaneval_subset.has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result is False

def test_has_close_elements_identical_elements():
    """Test case with identical elements."""
    result = humaneval_subset.has_close_elements([2.0, 2.0, 3.0, 4.0, 5.0])
    assert result is True

def test_find_closest_elements_normal_case():
    """Test normal use case with valid inputs."""
    result = humaneval_subset.find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])
    assert result == (2.0, 2.2)

def test_find_closest_elements_identical_elements():
    """Test case with identical elements."""
    result = humaneval_subset.find_closest_elements([2.0, 2.0, 3.0, 4.0, 5.0])
    assert result == (2.0, 2.0)

def test_find_closest_elements_large_numbers():
    """Test case with large numbers."""
    result = humaneval_subset.find_closest_elements([1e6, 1e6 + 1e-3, 1e7])
    assert result == (1e6, 1e6 + 1e-3)

def test_rescale_to_unit_normal_case():
    """Test normal use case with valid inputs."""
    result = humaneval_subset.rescale_to_unit([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result == [0.0, 0.25, 0.5, 0.75, 1.0]

def test_rescale_to_unit_identical_elements():
    """Test case with identical elements."""
    result = humaneval_subset.rescale_to_unit([3.0, 3.0, 3.0])
    assert result == [0.0, 0.0, 0.0]

def test_count_distinct_characters_normal_case():
    """Test normal use case with valid inputs."""
    result = humaneval_subset.count_distinct_characters('xyzXYZ')
    assert result == 3

def test_count_distinct_characters_empty_string():
    """Test edge case with empty string."""
    result = humaneval_subset.count_distinct_characters('')
    assert result == 0

def test_has_close_elements_with_negative_numbers():
    """Test case with negative numbers."""
    result = humaneval_subset.has_close_elements([-1.0, -2.0, -3.0, -4.0, -5.0, -2.2])
    assert result is True

def test_has_close_elements_with_mixed_signs():
    """Test case with mixed positive and negative numbers."""
    result = humaneval_subset.has_close_elements([-1.0, 2.0, -3.0, 4.0, -5.0, 2.2])
    assert result is True

def test_has_close_elements_with_zero():
    """Test case with zero included."""
    result = humaneval_subset.has_close_elements([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 0.1])
    assert result is True

def test_find_closest_elements_with_negative_numbers():
    """Test case with negative numbers."""
    result = humaneval_subset.find_closest_elements([-1.0, -2.0, -3.0, -4.0, -5.0, -2.2])
    assert result == (-2.0, -2.2)

def test_find_closest_elements_with_mixed_signs():
    """Test case with mixed positive and negative numbers."""
    result = humaneval_subset.find_closest_elements([-1.0, 2.0, -3.0, 4.0, -5.0, 2.2])
    assert result == (-1.0, 2.0)

def test_find_closest_elements_with_zero():
    """Test case with zero included."""
    result = humaneval_subset.find_closest_elements([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 0.1])
    assert result == (0.0, 0.1)

def test_rescale_to_unit_with_negative_numbers():
    """Test case with negative numbers."""
    result = humaneval_subset.rescale_to_unit([-1.0, -2.0, -3.0, -4.0, -5.0])
    assert result == [1.0, 0.75, 0.5, 0.25, 0.0]

def test_rescale_to_unit_with_mixed_signs():
    """Test case with mixed positive and negative numbers."""
    result = humaneval_subset.rescale_to_unit([-1.0, 2.0, -3.0, 4.0, -5.0])
    assert result == [0.6, 0.8, 0.4, 1.0, 0.2]

def test_count_distinct_characters_with_special_characters():
    """Test case with special characters."""
    result = humaneval_subset.count_distinct_characters('xyzXYZ!@#')
    assert result == 6

def test_sort_numbers_with_large_numbers():
    """Test case with large numbers represented as words."""
    result = humaneval_subset.sort_numbers('eight seven six five four three two one zero nine eight')
    assert result == 'zero one two three four five six seven eight eight nine'