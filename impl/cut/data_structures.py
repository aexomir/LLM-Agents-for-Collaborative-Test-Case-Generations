"""Basic data structure operations for testing."""


class Stack:
    """Simple stack implementation."""
    
    def __init__(self):
        """Initialize an empty stack."""
        self._items = []
    
    def push(self, item):
        """Push an item onto the stack."""
        self._items.append(item)
    
    def pop(self):
        """Pop and return the top item from the stack."""
        if self.is_empty():
            raise IndexError("Cannot pop from empty stack")
        return self._items.pop()
    
    def peek(self):
        """Return the top item without removing it."""
        if self.is_empty():
            raise IndexError("Cannot peek at empty stack")
        return self._items[-1]
    
    def is_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self._items) == 0
    
    def size(self) -> int:
        """Return the number of items in the stack."""
        return len(self._items)


class Queue:
    """Simple queue implementation."""
    
    def __init__(self):
        """Initialize an empty queue."""
        self._items = []
    
    def enqueue(self, item):
        """Add an item to the rear of the queue."""
        self._items.append(item)
    
    def dequeue(self):
        """Remove and return the front item from the queue."""
        if self.is_empty():
            raise IndexError("Cannot dequeue from empty queue")
        return self._items.pop(0)
    
    def front(self):
        """Return the front item without removing it."""
        if self.is_empty():
            raise IndexError("Cannot access front of empty queue")
        return self._items[0]
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self._items) == 0
    
    def size(self) -> int:
        """Return the number of items in the queue."""
        return len(self._items)


def find_max(numbers: list) -> float:
    """Find the maximum value in a list of numbers."""
    if not numbers:
        raise ValueError("Cannot find max of empty list")
    return max(numbers)


def find_min(numbers: list) -> float:
    """Find the minimum value in a list of numbers."""
    if not numbers:
        raise ValueError("Cannot find min of empty list")
    return min(numbers)


def reverse_list(items: list) -> list:
    """Return a reversed copy of the list."""
    return items[::-1]


def remove_duplicates(items: list) -> list:
    """Remove duplicates from a list while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def merge_sorted_lists(list1: list, list2: list) -> list:
    """Merge two sorted lists into a single sorted list."""
    result = []
    i, j = 0, 0
    
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    
    # Add remaining elements
    result.extend(list1[i:])
    result.extend(list2[j:])
    
    return result


def count_occurrences(items: list, target) -> int:
    """Count occurrences of target in the list."""
    return items.count(target)


def flatten_nested_list(nested: list) -> list:
    """Flatten a nested list one level deep."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result
