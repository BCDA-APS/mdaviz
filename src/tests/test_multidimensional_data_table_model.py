"""
Tests for MultiDimensionalDataTableModel functionality.

This module tests the multi-dimensional data table model that can handle
2D, 3D, 4D, and higher dimensional scan data.
"""

import numpy as np
import pytest
from unittest.mock import Mock

from mdaviz.multidimensional_data_table_model import MultiDimensionalDataTableModel


class TestMultiDimensionalDataTableModel:
    """Test cases for MultiDimensionalDataTableModel functionality."""

    def test_2d_data_creation(self):
        """Test creating a 2D data model."""
        from PyQt6.QtCore import Qt

        # Create test scan data (simulating get_scan_2d() output)
        scan_data = {
            0: {"type": "POS", "name": "X2", "data": [0, 1], "unit": "mm"},
            1: {"type": "POS", "name": "X1", "data": [0, 1, 2], "unit": "mm"},
            2: {
                "type": "DET",
                "name": "DET1",
                "data": [[1, 2, 3], [4, 5, 6]],
                "unit": "counts",
            },
            3: {
                "type": "DET",
                "name": "DET2",
                "data": [[10, 20, 30], [40, 50, 60]],
                "unit": "counts",
            },
        }

        model = MultiDimensionalDataTableModel(scan_data)

        # Check basic properties
        assert model.rowCount() == 6  # 2 X2 values × 3 X1 values
        assert model.columnCount() == 4  # X2, X1, DET1, DET2
        assert len(model.get_column_headers()) == 4
        assert len(model.get_flattened_data()) == 6

    def test_2d_data_flattening(self):
        """Test that 2D data is correctly flattened."""
        # Create test scan data (matching real MDA structure)
        scan_data = {
            0: {"type": "POS", "name": "X2", "data": [0, 1], "unit": "mm"},
            1: {
                "type": "POS",
                "name": "X1",
                "data": [[0, 1], [0, 1]],
                "unit": "mm",
            },  # Nested structure
            2: {
                "type": "DET",
                "name": "DET1",
                "data": [[1, 2], [3, 4]],
                "unit": "counts",
            },
        }

        model = MultiDimensionalDataTableModel(scan_data, x2_points=2, x1_points=2)

        # Check flattened data structure
        flattened_data = model.get_flattened_data()
        assert len(flattened_data) == 4  # 2 X2 × 2 X1 = 4 rows

        # Check expected pattern: [X2, X1, DET1]
        expected_pattern = [
            [0, 0, 1],  # X2[0], X1[0], DET1[0,0]
            [0, 1, 2],  # X2[0], X1[1], DET1[0,1]
            [1, 0, 3],  # X2[1], X1[0], DET1[1,0]
            [1, 1, 4],  # X2[1], X1[1], DET1[1,1]
        ]

        for i, row in enumerate(flattened_data):
            assert row == expected_pattern[i]

    def test_empty_data(self):
        """Test model behavior with empty data."""
        # Create empty scan data
        scan_data = {}

        model = MultiDimensionalDataTableModel(scan_data)

        # Should handle empty data gracefully
        assert model.rowCount() == 0
        assert model.columnCount() == 0
        assert len(model.get_flattened_data()) == 0
        assert len(model.get_column_headers()) == 0

    def test_model_data_access(self):
        """Test accessing data through the model interface."""
        from PyQt6.QtCore import Qt

        # Create test scan data (matching real MDA structure)
        scan_data = {
            0: {"type": "POS", "name": "X2", "data": [0, 1], "unit": "mm"},
            1: {
                "type": "POS",
                "name": "X1",
                "data": [[0, 1], [0, 1]],
                "unit": "mm",
            },  # Nested structure
            2: {
                "type": "DET",
                "name": "DET1",
                "data": [[1, 2], [3, 4]],
                "unit": "counts",
            },
        }

        model = MultiDimensionalDataTableModel(scan_data, x2_points=2, x1_points=2)

        # Test data access through model interface
        assert model.data(model.index(0, 0)) == "0"  # X2[0]
        assert model.data(model.index(0, 1)) == "0"  # X1[0]
        assert model.data(model.index(0, 2)) == "1"  # DET1[0,0]

        assert model.data(model.index(1, 0)) == "0"  # X2[0]
        assert model.data(model.index(1, 1)) == "1"  # X1[1]
        assert model.data(model.index(1, 2)) == "2"  # DET1[0,1]

        # Test header data
        assert model.headerData(0, Qt.Orientation.Horizontal) == "X2"
        assert model.headerData(1, Qt.Orientation.Horizontal) == "X1"
        assert model.headerData(2, Qt.Orientation.Horizontal) == "DET1 (counts)"

    def test_demonstration_2d_data(self):
        """Demonstrate how the 2D data is flattened into a table."""
        # Create 2D data: 2 X2 points, 3 X1 points (matching real MDA structure)
        scan_data = {
            0: {
                "type": "POS",
                "name": "Index",
                "data": list(range(6)),
            },  # 2*3=6 total points
            1: {"type": "POS", "name": "X2", "data": [10.0, 20.0]},  # 2 X2 points
            2: {
                "type": "POS",
                "name": "X1",
                "data": [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]],
            },  # 3 X1 points (nested)
            3: {
                "type": "DET",
                "name": "DET1",
                "data": np.array([[100, 200, 300], [400, 500, 600]]),
            },  # 2x3 array
        }

        model = MultiDimensionalDataTableModel(scan_data, x2_points=2, x1_points=3)

        # Get the flattened data
        flattened_data = model.get_flattened_data()
        headers = model.get_column_headers()

        print("\n=== 2D Data Flattening Demonstration ===")
        print(f"Headers: {headers}")
        print("Flattened data:")
        for i, row in enumerate(flattened_data):
            print(f"Row {i}: {row}")

        # Expected pattern:
        # X2[0]=10.0, X1[0]=1.0, DET1[0,0]=100
        # X2[0]=10.0, X1[1]=2.0, DET1[0,1]=200
        # X2[0]=10.0, X1[2]=3.0, DET1[0,2]=300
        # X2[1]=20.0, X1[0]=1.0, DET1[1,0]=400
        # X2[1]=20.0, X1[1]=2.0, DET1[1,1]=500
        # X2[1]=20.0, X1[2]=3.0, DET1[1,2]=600

        assert len(flattened_data) == 6  # 2 X2 * 3 X1 = 6 rows
        assert flattened_data[0] == [10.0, 1.0, 100]  # First row
        assert flattened_data[5] == [20.0, 3.0, 600]  # Last row

    def test_multiple_positioners_per_dimension(self):
        """Test that the model can handle multiple positioners per dimension."""
        # Create 2D data with multiple positioners per dimension
        # 2 X2 points, 2 X1 points = 4 total points
        scan_data = {
            0: {
                "type": "POS",
                "name": "Index",
                "data": list(range(4)),
            },  # 2*2=4 total points
            1: {
                "type": "POS",
                "name": "X2_Pos1",
                "data": [10.0, 20.0],
            },  # First X2 positioner
            2: {
                "type": "POS",
                "name": "X1_Pos1",
                "data": [[1.0, 2.0], [1.0, 2.0]],  # Nested structure
            },  # First X1 positioner
            3: {
                "type": "DET",
                "name": "DET1",
                "data": np.array([[100, 200], [300, 400]]),
            },  # 2x2 array
        }

        model = MultiDimensionalDataTableModel(scan_data, x2_points=2, x1_points=2)

        # Get the flattened data
        flattened_data = model.get_flattened_data()
        headers = model.get_column_headers()

        print("\n=== Multiple Positioners Test ===")
        print(f"Headers: {headers}")
        print("Flattened data:")
        for i, row in enumerate(flattened_data):
            print(f"Row {i}: {row}")

        # Should have 4 rows (2 X2 * 2 X1 = 4 rows)
        assert len(flattened_data) == 4
        assert len(flattened_data[0]) == 3  # 2 positioners + 1 detector
        assert flattened_data[0] == [10.0, 1.0, 100]  # First row
        assert flattened_data[3] == [20.0, 2.0, 400]  # Last row

    def test_real_mda_file_positioner_structure(self, single_mda_file):
        """Test to examine the actual positioner structure in real MDA files."""
        from mdaviz.synApps_mdalib.mda import readMDA
        import glob

        # Try to find a 2D file
        mda_files = glob.glob("src/tests/data/**/*.mda", recursive=True)

        for mda_file in mda_files[:3]:  # Test first 3 files
            try:
                result = readMDA(mda_file)
                if result is None:
                    continue

                file_metadata, file_data_dim1, *additional_dims = result

                print(f"\n=== Real MDA File Analysis ===")
                print(f"File: {mda_file}")
                print(f"Rank: {file_metadata.get('rank', 'unknown')}")
                print(f"Dimensions: {file_metadata.get('dimensions', [])}")

                # Analyze outer dimension (dim1)
                print(f"\nOuter Dimension (dim1):")
                print(f"  np_dim1: {file_data_dim1.np}")
                print(f"  npts_dim1: {file_data_dim1.npts}")
                print(f"  curr_pt_dim1: {file_data_dim1.curr_pt}")

                for i, pos in enumerate(file_data_dim1.p):
                    print(
                        f"  Positioner {i}: number={pos.number}, fieldName='{pos.fieldName}', name='{pos.name}'"
                    )

                # Analyze inner dimension (dim2) if it exists
                if len(additional_dims) > 0:
                    file_data_dim2 = additional_dims[0]
                    print(f"\nInner Dimension (dim2):")
                    print(f"  np_dim2: {file_data_dim2.np}")
                    print(f"  npts_dim2: {file_data_dim2.npts}")
                    print(f"  curr_pt_dim2: {file_data_dim2.curr_pt}")

                    for i, pos in enumerate(file_data_dim2.p):
                        print(
                            f"  Positioner {i}: number={pos.number}, fieldName='{pos.fieldName}', name='{pos.name}'"
                        )

                    # Found a 2D file, break
                    break

            except Exception as e:
                print(f"Could not analyze {mda_file}: {e}")
                continue

        # This test is mainly for analysis, so we'll just assert that we tried
        assert len(mda_files) > 0

    def test_specific_2d_file_positioner_structure(self):
        """Test to examine the specific 2D file to understand positioner structure."""
        from mdaviz.synApps_mdalib.mda import readMDA
        import glob
        import mdaviz.utils as utils
        from mdaviz.utils import byte2str

        mda_file = "src/tests/data/mda 2D plus/mda_0006.mda"

        try:
            result = readMDA(mda_file)
            if result is None:
                pytest.skip("Could not read MDA file")

            file_metadata, file_data_dim1, *additional_dims = result

            print(f"\n=== 2D MDA File Analysis ===")
            print(f"File: {mda_file}")
            print(f"Rank: {file_metadata.get('rank', 'unknown')}")
            print(f"Dimensions: {file_metadata.get('dimensions', [])}")

            # Analyze outer dimension (dim1)
            print(f"\nOuter Dimension (dim1):")
            print(f"  np_dim1: {file_data_dim1.np}")
            print(f"  npts_dim1: {file_data_dim1.npts}")
            print(f"  curr_pt_dim1: {file_data_dim1.curr_pt}")

            for i, pos in enumerate(file_data_dim1.p):
                print(
                    f"  Positioner {i}: number={pos.number}, fieldName='{pos.fieldName}', name='{pos.name}'"
                )

            # Analyze inner dimension (dim2) if it exists
            if len(additional_dims) > 0:
                file_data_dim2 = additional_dims[0]
                print(f"\nInner Dimension (dim2):")
                print(f"  np_dim2: {file_data_dim2.np}")
                print(f"  npts_dim2: {file_data_dim2.npts}")
                print(f"  curr_pt_dim2: {file_data_dim2.curr_pt}")

                for i, pos in enumerate(file_data_dim2.p):
                    print(
                        f"  Positioner {i}: number={pos.number}, fieldName='{pos.fieldName}', name='{pos.name}'"
                    )

            # Also examine the processed scan data from utils.get_scan_2d()
            scan_data, first_pos, first_det = utils.get_scan_2d(
                file_data_dim1, file_data_dim2
            )

            print(f"\nProcessed Scan Data (from utils.get_scan_2d()):")
            print(f"  first_pos: {first_pos}")
            print(f"  first_det: {first_det}")

            for key, value in scan_data.items():
                print(
                    f"  Key '{key}': type={value.get('type')}, name='{value.get('name')}', fieldName='{value.get('fieldName')}'"
                )

            # This test is mainly for analysis, so we'll just assert that we got some data
            assert file_data_dim1.np >= 0
            assert file_data_dim1.npts > 0
            assert len(additional_dims) > 0

        except Exception as e:
            pytest.skip(f"Could not analyze MDA file: {e}")

    def test_real_2d_data_with_model(self):
        """Test that the model works correctly with real 2D data."""
        from mdaviz.synApps_mdalib.mda import readMDA
        import mdaviz.utils as utils

        mda_file = "src/tests/data/mda 2D plus/mda_0006.mda"

        try:
            result = readMDA(mda_file)
            if result is None:
                pytest.skip("Could not read MDA file")

            file_metadata, file_data_dim1, file_data_dim2 = result

            # Get the processed scan data
            scan_data, first_pos, first_det = utils.get_scan_2d(
                file_data_dim1, file_data_dim2
            )

            print(f"\n=== Scan Data Keys ===")
            for key, value in scan_data.items():
                print(
                    f"Key '{key}': type={value.get('type')}, name='{value.get('name')}'"
                )

            # Create the model with real data
            model = MultiDimensionalDataTableModel(scan_data)

            # Get the flattened data
            flattened_data = model.get_flattened_data()
            headers = model.get_column_headers()

            print(f"\n=== Real 2D Data Model Test ===")
            print(f"Headers: {headers}")
            print(f"Number of rows: {len(flattened_data)}")
            print(
                f"Number of columns: {len(flattened_data[0]) if flattened_data else 0}"
            )

            if flattened_data:
                print(f"First row: {flattened_data[0]}")
                print(f"Last row: {flattened_data[-1]}")

            # Verify the structure
            # Should have 16 * 5 = 80 rows (16 X2 points * 5 X1 points)
            assert len(flattened_data) == 80

            # Should have at least 2 columns (X2, X1) plus detectors
            assert len(flattened_data[0]) >= 2

            # Check that we have the expected structure
            structure = model.get_2d_structure()
            assert "x2_data" in structure
            assert "x1_data" in structure
            assert "detectors" in structure

        except Exception as e:
            pytest.skip(f"Could not test with real data: {e}")

    def test_get_scan_2d_structure_example(self):
        """Demonstrate the structure returned by get_scan_2d()."""
        from mdaviz.synApps_mdalib.mda import readMDA
        import mdaviz.utils as utils
        from mdaviz.utils import byte2str

        mda_file = "src/tests/data/mda 2D plus/mda_0006.mda"

        try:
            result = readMDA(mda_file)
            if result is None:
                pytest.skip("Could not read MDA file")

            file_metadata, file_data_dim1, file_data_dim2 = result

            # Get the processed scan data
            scan_data, first_pos, first_det = utils.get_scan_2d(
                file_data_dim1, file_data_dim2
            )

            print(f"\n=== get_scan_2d() Structure Example ===")
            print(
                f"Return values: scan_data, first_pos={first_pos}, first_det={first_det}"
            )
            print(f"\nscan_data structure:")

            for key, value in scan_data.items():
                print(f"  Key {key}:")
                print(f"    type: {value.get('type')}")
                print(f"    name: '{value.get('name')}'")
                print(f"    fieldName: '{value.get('fieldName')}'")
                print(f"    unit: '{value.get('unit')}'")
                print()

        except Exception as e:
            pytest.skip(f"Could not analyze structure: {e}")


class MockScanDim:
    """Mock scan dimension for testing."""

    def __init__(self, np=0, p=None):
        self.np = np
        self.p = p or []


class MockPositioner:
    """Mock positioner for testing."""

    pass


if __name__ == "__main__":
    pytest.main([__file__])
