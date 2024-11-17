from pathlib import Path
import pytest
from token_talkers.repo_expert.file_index import (
    SQLiteFileIndex,
    HardFileRecord,
    SoftFileRecord,
    populate_index,
)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_database.db"


@pytest.fixture
def file_index(db_path):
    index = SQLiteFileIndex(db_path)
    index.initialize_schema()
    yield index
    del index


@pytest.fixture
def demo_dir(tmp_path):
    tmp_path = tmp_path / "demo_dir"
    tmp_path.mkdir()
    return tmp_path


def test_initialize_schema(file_index):
    file_index._cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='hard_files'"
    )
    table = file_index._cursor.fetchone()
    assert table is not None
    assert table[0] == "hard_files"

    file_index._cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='soft_files'"
    )
    table = file_index._cursor.fetchone()
    assert table is not None
    assert table[0] == "soft_files"


def test_insert_hard_records(file_index):
    record = HardFileRecord(
        path="/path/to/file.txt", size=1234, is_binary=False, number_of_lines=100
    )
    assert file_index.insert_hard_records([record])
    result = file_index.query_hard_records("%file.txt")
    assert list(result) == [record]


def test_insert_soft_records(file_index):
    hard_record = HardFileRecord(
        path="/path/to/file.txt", size=1234, is_binary=False, number_of_lines=100
    )
    file_index.insert_hard_records([hard_record])
    soft_record = SoftFileRecord(path="/path/to/soft_link.txt", hard_path="/path/to/file.txt")
    assert file_index.insert_soft_records([soft_record])
    result = file_index.query_soft_records("%soft_link.txt")
    assert list(result) == [soft_record]


def test_wipe_data(file_index):
    record = HardFileRecord(
        path="/path/to/file.txt", size=1234, is_binary=False, number_of_lines=100
    )
    file_index.insert_hard_records([record])
    file_index.wipe_data()
    results = file_index.query_hard_records("%")
    assert list(results) == []


def test_query_hard_records(file_index):
    record1 = HardFileRecord(
        path="/path/to/file1.txt", size=1234, is_binary=False, number_of_lines=100
    )
    record2 = HardFileRecord(
        path="/path/to/file2.txt", size=5678, is_binary=True, number_of_lines=200
    )
    file_index.insert_hard_records([record1, record2])
    results = file_index.query_hard_records("%file1%")
    assert list(results) == [record1]
    results = file_index.query_hard_records("nonexistent")
    assert list(results) == []
    results = file_index.query_hard_records("%")
    assert list(results) == [record1, record2]


def test_query_soft_records(file_index):
    hard_record = HardFileRecord(
        path="/path/to/file.txt", size=1234, is_binary=False, number_of_lines=100
    )
    file_index.insert_hard_records([hard_record])
    soft_record1 = SoftFileRecord(path="/path/to/soft_link1.txt", hard_path="/path/to/file.txt")
    soft_record2 = SoftFileRecord(path="/path/to/soft_link2.txt", hard_path="/path/to/file.txt")
    file_index.insert_soft_records([soft_record1, soft_record2])
    results = file_index.query_soft_records("%soft_link1%")
    assert list(results) == [soft_record1]
    results = file_index.query_soft_records("nonexistent")
    assert list(results) == []
    results = file_index.query_soft_records("%")
    assert list(results) == [soft_record1, soft_record2]


def test_populate_index(file_index, tmp_path):
    # Create some test files
    tmp_path = tmp_path / "test_files"
    tmp_path.mkdir()
    file1 = tmp_path / "file1.txt"
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    file2 = dir1 / "file1.bin"
    file1.write_text("This is a test file.\nWith multiple lines.\n")
    file2.write_bytes(b"\x00\x01\x02\x03")

    # Populate the index
    populate_index(file_index, tmp_path, wipe=True)

    # Query the index
    results = list(file_index.query_hard_records("%"))

    # Check the results
    assert len(results) == 2

    file1_record = next((r for r in results if r.path == str(file1)), None)
    file2_record = next((r for r in results if r.path == str(file2)), None)

    assert file1_record == HardFileRecord(
        path=str(file1), size=file1.stat().st_size, is_binary=False, number_of_lines=2
    )
    assert file2_record == HardFileRecord(
        path=str(file2), size=file2.stat().st_size, is_binary=True, number_of_lines=0
    )


def test_populate_index_with_existing_data(file_index, tmp_path):
    # Create some test files
    tmp_path = tmp_path / "test_files"
    tmp_path.mkdir()
    file1 = tmp_path / "file1.txt"
    file1.write_text("This is a test file.\nWith multiple lines.\n")

    # Populate the index
    populate_index(file_index, tmp_path, wipe=True)

    # Try to populate again without wiping
    with pytest.raises(
        ValueError, match="There are existing records in the database. Set wipe=True."
    ):
        populate_index(file_index, tmp_path, wipe=False)

    file2 = tmp_path / "file2.txt"
    file2.write_text("This is another test file.\nWith multiple lines.\n")
    populate_index(file_index, tmp_path, wipe=True)
    assert len(list(file_index.query_hard_records("%"))) == 2


def test_populate_index_with_symlinks(file_index, demo_dir):
    # Create some test files and symlinks
    file1 = demo_dir / "file1.txt"
    file1.write_text("This is a test file.\nWith multiple lines.\n")
    symlink1 = demo_dir / "symlink1.txt"
    symlink1.symlink_to(file1)

    # Populate the index
    populate_index(file_index, demo_dir, wipe=True)

    # Query the index
    results = list(file_index.query_hard_records("%"))

    # Check the results
    assert len(results) == 1

    file1_record = next((r for r in results if r.path == str(file1)), None)
    assert file1_record == HardFileRecord(
        path=str(file1), size=file1.stat().st_size, is_binary=False, number_of_lines=2
    )

    # Check the soft records
    soft_results = list(file_index.query_soft_records("%"))
    assert set(soft_results) == {
        SoftFileRecord(path=str(symlink1), hard_path=str(file1)),
        SoftFileRecord(path=str(file1), hard_path=str(file1)),
    }


def test_populate_index_with_empty_directory(file_index, tmp_path):
    # Create an empty directory
    tmp_path = tmp_path / "empty_dir"
    tmp_path.mkdir()

    # Populate the index
    populate_index(file_index, tmp_path, wipe=True)

    # Query the index
    results = list(file_index.query_hard_records("%"))

    # Check the results
    assert len(results) == 0


def test_populate_index_with_nonexistent_directory(file_index, tmp_path):
    # Use a nonexistent directory path
    nonexistent_path = Path("/nonexistent_directory")
    tmp_file = tmp_path / "tmp_file.txt"

    # Populate the index
    with pytest.raises(ValueError, match="is not a directory or does not exist"):
        populate_index(file_index, nonexistent_path, wipe=True)

    # Populate the index
    with pytest.raises(ValueError, match="is not a directory or does not exist"):
        populate_index(file_index, tmp_file, wipe=True)
