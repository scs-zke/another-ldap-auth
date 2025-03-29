# pylint: disable=missing-docstring

import pytest

from src.main import UpdatedReloader

test_extra_files = ["file1.txt", "file2.txt"]
length = len(test_extra_files)

@pytest.fixture
def updatedreloader() -> UpdatedReloader:
    """Pytest fixture to create a User instance for testing."""
    return UpdatedReloader(["file1.txt", "file2.txt"], 5, None)

def test_updatereloader_creation(updatedreloader: UpdatedReloader) -> None:
    """Test the creation of a User instance."""
    assert updatedreloader._extra_files == set(test_extra_files)
    assert len(updatedreloader._extra_files) == length
    assert isinstance(updatedreloader._extra_files, set)
    assert updatedreloader._interval == 5
    assert updatedreloader._callback == None

def test_get_files(updatedreloader: UpdatedReloader) -> None:
    files: list = updatedreloader.get_files()
    assert sorted(files) == sorted(test_extra_files)
    assert len(files) == length
    assert isinstance(files, list)
