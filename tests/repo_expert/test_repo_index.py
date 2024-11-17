import sqlite3
import pytest
from token_talkers.repo_expert.repo_index import SQLiteNodeIndex, NodeRecord


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_database.db"


@pytest.fixture
def node_index(db_path):
    index = SQLiteNodeIndex(db_path)
    index.initialize_schema()
    yield index
    del index


def test_initialize_schema(node_index):
    node_index._cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes'")
    table = node_index._cursor.fetchone()
    assert table is not None
    assert table[0] == "nodes"


def test_insert_node_records(node_index):
    record = NodeRecord(
        name="MyClass", type="class", container=None, hard_file_path="/path/to/file.txt"
    )
    assert node_index.insert_node_records([record])
    assert list(node_index.query_node_records("MyClass", "/path/to/file.txt")) == [record]


def test_wipe_data(node_index):
    record = NodeRecord(
        name="MyClass", type="class", container=None, hard_file_path="/path/to/file.txt"
    )
    node_index.insert_node_records([record])
    node_index.wipe_data()
    results = node_index.query_node_records("%")
    assert list(results) == []


def test_query_node_records(node_index):
    record1 = NodeRecord(
        name="MyClass1", type="class", container=None, hard_file_path="/path/to/file1.txt"
    )
    record2 = NodeRecord(
        name="MyClass2", type="class", container=None, hard_file_path="/path/to/file2.txt"
    )
    node_index.insert_node_records([record1, record2])
    assert list(node_index.query_node_records("MyClass1", "/path/to/file1.txt")) == [record1]
    assert list(node_index.query_node_records("nonexistent")) == []
    assert list(node_index.query_node_records("%")) == [record1, record2]


def test_container_constraint(node_index):
    # Insert a record without a container
    subclass_record = NodeRecord(
        name="MySubClass", type="class", container="MyClass", hard_file_path="/path/to/file.txt"
    )
    with pytest.raises(sqlite3.IntegrityError):
        assert node_index.insert_node_records([subclass_record])

    class_record = NodeRecord(
        name="MyClass", type="class", container=None, hard_file_path="/path/to/file.txt"
    )
    assert node_index.insert_node_records([class_record, subclass_record])
    assert set(node_index.query_node_records("%")) == {class_record, subclass_record}
