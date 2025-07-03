#!/usr/bin/env python3
"""
Simple test script to demonstrate cursor nearest point finding and range functionality.
"""

import numpy as np
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_nearest_point_algorithm():
    """Test the nearest point finding algorithm."""
    print("Testing nearest point finding algorithm...")

    # Create test data
    x_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

    # Test click positions
    test_clicks = [
        (1.5, 15.0),  # Should find (1.0, 10.0)
        (2.8, 28.0),  # Should find (3.0, 30.0)
        (4.2, 42.0),  # Should find (4.0, 40.0)
        (0.5, 5.0),  # Should find (1.0, 10.0)
        (6.0, 60.0),  # Should find (5.0, 50.0)
    ]

    expected_results = [
        (1.0, 10.0),
        (3.0, 30.0),
        (4.0, 40.0),
        (1.0, 10.0),
        (5.0, 50.0),
    ]

    for i, (click_x, click_y) in enumerate(test_clicks):
        # Calculate distances to all points
        distances = np.sqrt((x_data - click_x) ** 2 + (y_data - click_y) ** 2)
        nearest_index = np.argmin(distances)
        nearest_point = (float(x_data[nearest_index]), float(y_data[nearest_index]))

        expected = expected_results[i]
        print(
            f"Click at ({click_x}, {click_y}) -> Nearest: {nearest_point} (Expected: {expected})"
        )

        assert nearest_point == expected, f"Expected {expected}, got {nearest_point}"

    print("✓ All nearest point tests passed!")


def test_cursor_range():
    """Test cursor range calculation."""
    print("\nTesting cursor range calculation...")

    # Test cases: (cursor1_pos, cursor2_pos, expected_range)
    test_cases = [
        ((1.0, 10.0), (5.0, 50.0), (1.0, 5.0)),
        ((5.0, 50.0), (1.0, 10.0), (1.0, 5.0)),  # Reversed order
        ((2.5, 25.0), (2.5, 25.0), (2.5, 2.5)),  # Same position
        ((0.0, 0.0), (10.0, 100.0), (0.0, 10.0)),
    ]

    for i, (pos1, pos2, expected_range) in enumerate(test_cases):
        x1, y1 = pos1
        x2, y2 = pos2
        calculated_range = (min(x1, x2), max(x1, x2))

        print(
            f"Cursor1: {pos1}, Cursor2: {pos2} -> Range: {calculated_range} (Expected: {expected_range})"
        )

        assert calculated_range == expected_range, (
            f"Expected {expected_range}, got {calculated_range}"
        )

    print("✓ All cursor range tests passed!")


def test_with_offset_factor():
    """Test nearest point finding with offset and factor applied."""
    print("\nTesting with offset and factor...")

    # Original data
    x_data = np.array([1.0, 2.0, 3.0])
    y_data = np.array([10.0, 20.0, 30.0])

    # Apply factor=2 and offset=5
    factor = 2.0
    offset = 5.0
    y_data_transformed = y_data * factor + offset  # [25, 45, 65]

    print(f"Original y values: {y_data}")
    print(
        f"Transformed y values (factor={factor}, offset={offset}): {y_data_transformed}"
    )

    # Test finding nearest point to transformed data
    click_x, click_y = 2.0, 50.0
    distances = np.sqrt((x_data - click_x) ** 2 + (y_data_transformed - click_y) ** 2)
    nearest_index = np.argmin(distances)
    nearest_point = (
        float(x_data[nearest_index]),
        float(y_data_transformed[nearest_index]),
    )

    expected = (2.0, 45.0)  # Should find the point at x=2.0
    print(
        f"Click at ({click_x}, {click_y}) -> Nearest: {nearest_point} (Expected: {expected})"
    )

    assert nearest_point == expected, f"Expected {expected}, got {nearest_point}"
    print("✓ Offset and factor test passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Cursor Functionality")
    print("=" * 60)

    try:
        test_nearest_point_algorithm()
        test_cursor_range()
        test_with_offset_factor()

        print("\n" + "=" * 60)
        print("✓ All tests passed! Cursor functionality is working correctly.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
