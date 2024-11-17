import sqlite3
from abc import ABC, abstractmethod
from typing import Iterator, List, NamedTuple, Optional

from token_talkers.repo_expert.file_index import SQLiteFileIndex


class NodeRecord(NamedTuple):
    hard_file_path: str
    name: str
    type: str
    container: Optional[str]


class NodeIndex(ABC):
    @abstractmethod
    def initialize_schema(self, drop_existing: bool = False):  # pragma: no cover
        pass

    @abstractmethod
    def wipe_data(self):  # pragma: no cover
        pass

    @abstractmethod
    def insert_node_records(self, records: List[NodeRecord]) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def query_node_records(
        self, fuzzy_name: str, fuzzy_path: str
    ) -> Iterator[NodeRecord]:  # pragma: no cover
        pass


class SQLiteNodeIndex(NodeIndex):
    """
    Example usage:
    index = SQLiteNodeIndex('/path/to/database.db')
    index.initialize_schema()
    index.wipe_data()
    record = NodeRecord(hard_file_path='/path/to/file.txt', name='MyClass', type='class',
        container=None)
    index.insert_node_records([record])
    results = index.query_node_records('MyClass')
    print(list(results))
    """

    NODES = "nodes"

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()

    def initialize_schema(self, drop_existing: bool = False):
        if drop_existing:
            self._cursor.execute(f"DROP TABLE IF EXISTS {self.NODES}")
        self._cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.NODES} (
            hard_file_path TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT,
            container_hard_file_path TEXT,
            container_name TEXT,
            PRIMARY KEY (hard_file_path, name),
            FOREIGN KEY(hard_file_path) REFERENCES {SQLiteFileIndex.HARD_FILES}(path)
            FOREIGN KEY(container_hard_file_path, container_name)
                REFERENCES {self.NODES}(hard_file_path, name)
            )
        """
        )
        self._conn.commit()

    def wipe_data(self):
        self._cursor.execute(f"DELETE FROM {self.NODES}")
        self._conn.commit()

    def insert_node_records(self, records: List[NodeRecord]) -> bool:
        inserted_count = 0
        for record in records:
            if not self._is_valid_container_reference(record):
                raise sqlite3.IntegrityError(
                    f"Cannot insert into nodes. "
                    f"Container foreign key constraing violated. "
                    f"hard_file_path={record.hard_file_path} name={record.container} "
                    f"does not exist in {self.NODES}"
                )
            self._cursor.execute(
                f"""INSERT INTO {self.NODES}
                (hard_file_path, name, type, container_hard_file_path, container_name)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    record.hard_file_path,
                    record.name,
                    record.type,
                    record.hard_file_path,
                    record.container,
                ),
            )
            inserted_count += self._cursor.rowcount
        self._conn.commit()

        return inserted_count == len(records)

    def _is_valid_container_reference(self, record: NodeRecord) -> bool:
        return (
            record.container is None
            or next(self.query_node_records(record.container, record.hard_file_path), None)
            is not None
        )

    def query_node_records(self, fuzzy_name: str, fuzzy_path: str = "%") -> Iterator[NodeRecord]:
        query = f"""SELECT hard_file_path, name, type, container_name
        FROM {self.NODES} WHERE hard_file_path LIKE ? and name LIKE ?"""
        self._cursor.execute(
            query,
            (
                fuzzy_path,
                fuzzy_name,
            ),
        )
        return (NodeRecord(*row) for row in self._cursor.fetchall())

    def __del__(self):
        self._conn.close()
