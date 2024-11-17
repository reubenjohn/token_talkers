import pytest
from token_talkers.repo_expert.file_index import SQLiteFileIndex, FileRecord, populate_index


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_database.db"


@pytest.fixture
def file_index(db_path):
    index = SQLiteFileIndex(db_path)
    index.initialize_schema()
    yield index
    del index


def test_initialize_schema(file_index):
    file_index._cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
    table = file_index._cursor.fetchone()
    assert table is not None
    assert table[0] == "files"


def test_insert_records(file_index):
    record = FileRecord(path="/path/to/file.txt", size=1234, is_binary=False, number_of_lines=100)
    assert file_index.insert_records([record])
    result = file_index.run_query("%file.txt")
    assert list(result) == [record]


def test_wipe_data(file_index):
    record = FileRecord(path="/path/to/file.txt", size=1234, is_binary=False, number_of_lines=100)
    file_index.insert_records([record])
    file_index.wipe_data()
    results = file_index.run_query("*")
    assert list(results) == []


def test_run_query(file_index):
    record1 = FileRecord(path="/path/to/file1.txt", size=1234, is_binary=False, number_of_lines=100)
    record2 = FileRecord(path="/path/to/file2.txt", size=5678, is_binary=True, number_of_lines=200)
    file_index.insert_records([record1, record2])
    results = file_index.run_query("%file1%")
    assert list(results) == [record1]
    results = file_index.run_query("nonexistent")
    assert list(results) == []
    results = file_index.run_query("%")
    assert list(results) == [record1, record2]


def test_run_query_no_results(file_index):
    results = file_index.run_query("%")
    assert len(list(results)) == 0


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
    results = list(file_index.run_query("%"))

    # Check the results
    assert len(results) == 2

    file1_record = next((r for r in results if r.path == str(file1)), None)
    file2_record = next((r for r in results if r.path == str(file2)), None)

    assert file1_record == FileRecord(
        path=str(file1), size=file1.stat().st_size, is_binary=False, number_of_lines=2
    )
    assert file2_record == FileRecord(
        path=str(file2), size=file2.stat().st_size, is_binary=True, number_of_lines=0
    )
