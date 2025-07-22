#!/usr/bin/env python
"""
Tests for real test data fixtures.

This module verifies that the real test data fixtures work correctly
and can access the actual MDA files in the test data directory.

.. autosummary::

    ~test_test_data_path_exists
    ~test_test_folder_paths_exist
    ~test_mda_files_exist
    ~test_file_counts
    ~test_file_accessibility
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TestRealDataFixtures:
    """Test that real test data fixtures work correctly."""

    def test_test_data_path_exists(self, test_data_path: Path) -> None:
        """Test that test data path exists and is a directory."""
        assert test_data_path.exists()
        assert test_data_path.is_dir()
        assert test_data_path.name == "data"

    def test_test_folder1_path_exists(self, test_folder1_path: Path) -> None:
        """Test that test_folder1 path exists and contains MDA files."""
        assert test_folder1_path.exists()
        assert test_folder1_path.is_dir()

        # Check that it contains MDA files (main directory only)
        mda_files = list(test_folder1_path.glob("*.mda"))
        assert len(mda_files) > 0
        assert len(mda_files) == 16  # Should have 16 files in main directory

        # Check total files including subdirectories
        all_mda_files = list(test_folder1_path.rglob("*.mda"))
        assert len(all_mda_files) == 20  # Should have 20 files total

    def test_test_folder2_path_exists(self, test_folder2_path: Path) -> None:
        """Test that test_folder2 path exists and contains MDA files."""
        assert test_folder2_path.exists()
        assert test_folder2_path.is_dir()

        # Check that it contains MDA files
        mda_files = list(test_folder2_path.glob("*.mda"))
        assert len(mda_files) > 0
        assert len(mda_files) == 16  # Should have 16 files

    def test_test_folder3_path_exists(self, test_folder3_path: Path) -> None:
        """Test that test_folder3 path exists and contains MDA files."""
        assert test_folder3_path.exists()
        assert test_folder3_path.is_dir()

        # Check that it contains MDA files (including nested)
        mda_files = list(test_folder3_path.rglob("*.mda"))
        assert len(mda_files) > 0
        assert len(mda_files) == 76  # Should have 76 files total

    def test_test_no_positioner_path_exists(
        self, test_no_positioner_path: Path
    ) -> None:
        """Test that test_no_positioner path exists and contains ARPES files."""
        assert test_no_positioner_path.exists()
        assert test_no_positioner_path.is_dir()

        # Check that it contains ARPES MDA files
        mda_files = list(test_no_positioner_path.glob("*.mda"))
        assert len(mda_files) > 0
        assert len(mda_files) == 28  # Should have 28 ARPES files

    def test_sample_mda_files_fixture(self, sample_mda_files: list[Path]) -> None:
        """Test that sample_mda_files fixture returns valid files."""
        assert len(sample_mda_files) == 16  # Only files in main directory

        for file_path in sample_mda_files:
            assert file_path.exists()
            assert file_path.is_file()
            assert file_path.suffix == ".mda"
            assert file_path.name.startswith(
                (
                    "mda_",
                    "prefix",
                    "simple",
                    "some-other",
                    "yet.another",
                    "nounderscore",
                )
            )

    def test_nested_mda_files_fixture(self, nested_mda_files: list[Path]) -> None:
        """Test that nested_mda_files fixture returns valid files including subfolders."""
        assert len(nested_mda_files) == 76

        for file_path in nested_mda_files:
            assert file_path.exists()
            assert file_path.is_file()
            assert file_path.suffix == ".mda"
            assert file_path.name.startswith("mda_")

    def test_arpes_mda_files_fixture(self, arpes_mda_files: list[Path]) -> None:
        """Test that arpes_mda_files fixture returns valid ARPES files."""
        assert len(arpes_mda_files) == 28

        for file_path in arpes_mda_files:
            assert file_path.exists()
            assert file_path.is_file()
            assert file_path.suffix == ".mda"
            assert file_path.name.startswith("ARPES_")

    def test_single_mda_file_fixture(self, single_mda_file: Path) -> None:
        """Test that single_mda_file fixture returns a valid file."""
        assert single_mda_file.exists()
        assert single_mda_file.is_file()
        assert single_mda_file.suffix == ".mda"

    def test_file_accessibility(self, single_mda_file: Path) -> None:
        """Test that MDA files can be read."""
        # Test that file is readable
        assert single_mda_file.stat().st_size > 0

        # Test that we can read the file (basic file access)
        with open(single_mda_file, "rb") as f:
            content = f.read(100)  # Read first 100 bytes
            assert len(content) > 0

    def test_folder_structure(self, test_folder3_path: Path) -> None:
        """Test that test_folder3 has the expected nested structure."""
        # Check for subfolders
        subfolders = [d for d in test_folder3_path.iterdir() if d.is_dir()]
        assert len(subfolders) > 0

        # Check that subfolders contain files
        for subfolder in subfolders:
            if subfolder.name.startswith("subfolder"):
                files = list(subfolder.glob("*.mda"))
                assert len(files) > 0

    def test_file_naming_patterns(self, test_folder1_path: Path) -> None:
        """Test that test_folder1 contains files with various naming patterns."""
        files = list(test_folder1_path.glob("*.mda"))

        # Check for different naming patterns
        patterns = {
            "mda_": 0,  # Standard mda_ prefix
            "prefix": 0,  # prefix prefix
            "simple": 0,  # simple prefix
            "some-other": 0,  # some-other-prefix
            "yet.another": 0,  # yet.anotherprefix
            "nounderscore": 0,  # nounderscoreprefix
        }

        for file_path in files:
            for pattern in patterns:
                if file_path.name.startswith(pattern):
                    patterns[pattern] += 1
                    break

        # Verify we have files with different patterns
        assert sum(patterns.values()) == len(files)
        assert patterns["mda_"] > 0  # Should have standard mda_ files


class TestMockSettingsGetKey:
    """Test the mock_settings_get_key fixture."""

    def test_mock_settings_get_key_returns_correct_values(
        self, mock_settings_get_key
    ) -> None:
        """Test that mock_settings_get_key returns appropriate values for different keys."""
        # Test recentFolders
        result = mock_settings_get_key("recentFolders")
        assert result == "test_folder1,test_folder2"

        # Test windowGeometry
        result = mock_settings_get_key("windowGeometry")
        assert result == "800x600+100+100"

        # Test windowState
        result = mock_settings_get_key("windowState")
        assert result == "normal"

        # Test windowHeight
        result = mock_settings_get_key("windowHeight")
        assert result == 800

        # Test windowWidth
        result = mock_settings_get_key("windowWidth")
        assert result == 1200

        # Test unknown key
        result = mock_settings_get_key("unknownKey")
        assert result == "default_value"

    def test_mock_settings_get_key_called_multiple_times(
        self, mock_settings_get_key
    ) -> None:
        """Test that mock_settings_get_key can be called multiple times."""
        # Call multiple times with different keys
        assert mock_settings_get_key("recentFolders") == "test_folder1,test_folder2"
        assert mock_settings_get_key("windowGeometry") == "800x600+100+100"
        assert mock_settings_get_key("recentFolders") == "test_folder1,test_folder2"

        # Verify it was called 3 times
        assert mock_settings_get_key.call_count == 3
