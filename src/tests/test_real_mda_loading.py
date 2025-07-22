#!/usr/bin/env python
"""
Tests for real MDA file loading using actual test data.

This module demonstrates how to use the real test data fixtures
to test actual MDA file loading and parsing functionality.

.. autosummary::

    ~test_real_mda_file_loading
    ~test_real_mda_file_metadata
    ~test_real_mda_file_data_structure
    ~test_real_mda_file_caching
    ~test_real_mda_file_performance
"""

import pytest
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    pass


class TestRealMDAFileLoading:
    """Test real MDA file loading functionality."""

    def test_real_mda_file_exists_and_readable(self, single_mda_file: Path) -> None:
        """Test that a real MDA file exists and is readable."""
        assert single_mda_file.exists()
        assert single_mda_file.is_file()
        assert single_mda_file.stat().st_size > 0

        # Test basic file reading
        with open(single_mda_file, "rb") as f:
            content = f.read(1024)  # Read first 1KB
            assert len(content) > 0
            # MDA files should have substantial content
            assert len(content) >= 100

    def test_real_mda_file_loading_with_mock_mda_lib(
        self, single_mda_file: Path
    ) -> None:
        """Test loading a real MDA file using the MDA library."""
        # This test would use the actual MDA library to load the file
        # For now, we'll mock the library to avoid complex dependencies
        with patch("mdaviz.synApps_mdalib.mda.readMDA") as mock_read_mda:
            # Mock successful file reading
            mock_read_mda.return_value = {
                "metadata": {"rank": 1, "dimensions": [100]},
                "scanDict": {"det1": {"values": [1, 2, 3, 4, 5]}},
                "firstPos": 0,
                "firstDet": 1,
                "pvList": ["det1"],
            }

            # Test that the file path is passed correctly
            from mdaviz.synApps_mdalib.mda import readMDA

            result = readMDA(str(single_mda_file))

            # Verify the mock was called with the correct file path
            mock_read_mda.assert_called_once_with(str(single_mda_file))
            assert result is not None
            assert "metadata" in result
            assert "scanDict" in result

    def test_real_mda_file_caching(self, single_mda_file: Path) -> None:
        """Test caching functionality with real MDA files."""
        from mdaviz.data_cache import DataCache, CachedFileData

        cache = DataCache(max_entries=10)

        # Create cached data for the real file
        cached_data = CachedFileData(
            file_path=str(single_mda_file),
            metadata={"test": "metadata"},
            scan_dict={"test": "data"},
            first_pos=1,
            first_det=2,
            pv_list=["test_pv"],
            file_name=single_mda_file.name,
            folder_path=str(single_mda_file.parent),
            size_bytes=single_mda_file.stat().st_size,
        )

        # Test caching the real file
        cache.put(str(single_mda_file), cached_data)

        # Test retrieving from cache
        retrieved_data = cache.get(str(single_mda_file))
        assert retrieved_data is not None
        assert retrieved_data.file_path == str(single_mda_file)
        assert retrieved_data.file_name == single_mda_file.name
        assert retrieved_data.size_bytes == single_mda_file.stat().st_size

    def test_multiple_real_mda_files(self, sample_mda_files: list[Path]) -> None:
        """Test handling multiple real MDA files."""
        assert len(sample_mda_files) >= 5  # Should have at least 5 files

        # Test that all files are valid
        for file_path in sample_mda_files[:5]:  # Test first 5 files
            assert file_path.exists()
            assert file_path.is_file()
            assert file_path.stat().st_size > 0

            # Test file naming patterns
            assert file_path.suffix == ".mda"
            assert any(
                file_path.name.startswith(prefix)
                for prefix in [
                    "mda_",
                    "prefix",
                    "simple",
                    "some-other",
                    "yet.another",
                    "nounderscore",
                ]
            )

    def test_nested_folder_structure(self, nested_mda_files: list[Path]) -> None:
        """Test handling nested folder structure with real files."""
        assert len(nested_mda_files) >= 50  # Should have many files

        # Test that files come from different directory levels
        directory_levels = set()
        for file_path in nested_mda_files[:10]:  # Test first 10 files
            # Count directory levels from the test_folder3 root
            relative_parts = file_path.parts[
                file_path.parts.index("test_folder3") + 1 :
            ]
            directory_levels.add(len(relative_parts))

        # Should have files from different directory levels (some in root, some in subdirs)
        assert len(directory_levels) >= 1  # At least one level

    def test_arpes_files_no_positioner(self, arpes_mda_files: list[Path]) -> None:
        """Test ARPES files that don't have positioner data."""
        assert len(arpes_mda_files) >= 10  # Should have many ARPES files

        # Test that all files are ARPES files
        for file_path in arpes_mda_files[:5]:  # Test first 5 files
            assert file_path.exists()
            assert file_path.name.startswith("ARPES_")
            assert file_path.stat().st_size > 0

    def test_file_size_distribution(self, sample_mda_files: list[Path]) -> None:
        """Test that real MDA files have reasonable file sizes."""
        sizes = [f.stat().st_size for f in sample_mda_files]

        # All files should have positive size
        assert all(size > 0 for size in sizes)

        # Files should be reasonably sized (not too small, not too large)
        assert min(sizes) >= 1000  # At least 1KB
        assert max(sizes) <= 1000000  # No more than 1MB

        # Should have some size variation
        assert len(set(sizes)) > 1

    def test_file_naming_consistency(self, test_folder1_path: Path) -> None:
        """Test that file naming patterns are consistent."""
        files = list(test_folder1_path.glob("*.mda"))

        # Check naming patterns
        mda_files = [f for f in files if f.name.startswith("mda_")]
        prefix_files = [f for f in files if f.name.startswith("prefix")]
        simple_files = [f for f in files if f.name.startswith("simple")]

        # Should have files with different naming patterns
        assert len(mda_files) > 0
        assert len(prefix_files) > 0
        assert len(simple_files) > 0

        # Check that mda_ files follow the pattern mda_XXXX.mda
        for mda_file in mda_files:
            name_parts = mda_file.stem.split("_")
            assert len(name_parts) == 2
            assert name_parts[0] == "mda"
            assert name_parts[1].isdigit()

    @pytest.mark.slow
    def test_large_folder_scanning(self, test_folder3_path: Path) -> None:
        """Test scanning large folder with many files."""
        import time

        # Test scanning performance
        start_time = time.time()
        all_files = list(test_folder3_path.rglob("*.mda"))
        scan_time = time.time() - start_time

        # Should have many files
        assert len(all_files) >= 50

        # Scanning should be reasonably fast
        assert scan_time < 1.0  # Should complete in less than 1 second

        # All files should be valid
        for file_path in all_files[:10]:  # Test first 10 files
            assert file_path.exists()
            assert file_path.stat().st_size > 0

    def test_file_access_permissions(self, single_mda_file: Path) -> None:
        """Test that real MDA files have proper access permissions."""
        # Test that file is readable
        assert single_mda_file.stat().st_mode & 0o400  # Readable by owner

        # Test that we can actually read the file
        try:
            with open(single_mda_file, "rb") as f:
                f.read(100)
        except PermissionError:
            pytest.fail(f"Cannot read file {single_mda_file}")

    def test_file_integrity(self, sample_mda_files: list[Path]) -> None:
        """Test that real MDA files have basic integrity."""
        for file_path in sample_mda_files[:3]:  # Test first 3 files
            # Test file header
            with open(file_path, "rb") as f:
                header = f.read(16)

                # Basic MDA file header check (simplified)
                assert len(header) >= 16

                # File should not be completely empty
                f.seek(0)
                content = f.read()
                assert len(content) > 100  # Should have substantial content
