import sqlite3
from abc import ABC, abstractmethod
from typing import Iterator, List, NamedTuple
import os
from pathlib import Path
import argparse


class HardFileRecord(NamedTuple):
    path: str
    size: int
    is_binary: bool
    number_of_lines: int
    processed: bool = True


class SoftFileRecord(NamedTuple):
    path: str
    hard_path: str


class FileIndex(ABC):
    @abstractmethod
    def initialize_schema(self, drop_existing: bool = False):  # pragma: no cover
        pass

    @abstractmethod
    def wipe_data(self):  # pragma: no cover
        pass

    @abstractmethod
    def insert_hard_records(self, records: List[HardFileRecord]) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def query_hard_records(self, fuzzy_path: str) -> Iterator[HardFileRecord]:  # pragma: no cover
        pass

    @abstractmethod
    def insert_soft_records(self, records: List[SoftFileRecord]) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def query_soft_records(self, fuzzy_path: str) -> Iterator[SoftFileRecord]:  # pragma: no cover
        pass


class SQLiteFileIndex(FileIndex):
    """
    Example usage:
    index = SQLiteFileIndex('/path/to/database.db')
    index.initialize_schema()
    index.wipe_data()
    record = FileRecord(path='/path/to/file.txt', size=1234, is_binary=False, number_of_lines=100,
      processed=True)
    index.insert_record(record)
    results = index.run_query('SELECT * FROM file_index')
    print(results)
    """

    HARD_FILES = "hard_files"
    SOFT_FILES = "soft_files"

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()

    def initialize_schema(self, drop_existing: bool = False):
        if drop_existing:
            self._cursor.execute(f"DROP TABLE IF EXISTS {self.HARD_FILES}")
            self._cursor.execute(f"DROP TABLE IF EXISTS {self.SOFT_FILES}")
        self._cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.HARD_FILES} (
                path TEXT PRIMARY KEY,
                size INTEGER,
                is_binary BOOLEAN,
                number_of_lines INTEGER,
                processed BOOLEAN
            )
        """
        )
        self._cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.SOFT_FILES} (
                path TEXT PRIMARY KEY,
                hard_path TEXT,
                FOREIGN KEY(hard_path) REFERENCES {self.HARD_FILES}(path)
            )
        """
        )
        self._conn.commit()

    def wipe_data(self):
        self._cursor.execute(f"DELETE FROM {self.HARD_FILES}")
        self._cursor.execute(f"DELETE FROM {self.SOFT_FILES}")
        self._conn.commit()

    def insert_hard_records(self, records: List[HardFileRecord]) -> bool:
        try:
            for record in records:
                self._cursor.execute(
                    f"""INSERT INTO {self.HARD_FILES}
                    (path, size, is_binary, number_of_lines, processed) VALUES (?, ?, ?, ?, ?)""",
                    record,
                )
            self._conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False

    def query_hard_records(self, fuzzy_path: str) -> Iterator[HardFileRecord]:
        query = f"SELECT * FROM {self.HARD_FILES} WHERE path LIKE ?"
        self._cursor.execute(query, (fuzzy_path,))
        return (HardFileRecord(*row) for row in self._cursor.fetchall())

    def insert_soft_records(self, records: List[SoftFileRecord]) -> bool:
        try:
            for record in records:
                self._cursor.execute(
                    f"INSERT INTO {self.SOFT_FILES} (path, hard_path) VALUES (?, ?)",
                    record,
                )
            self._conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False

    def query_soft_records(self, fuzzy_path: str) -> Iterator[SoftFileRecord]:
        query = f"SELECT * FROM {self.SOFT_FILES} WHERE path LIKE ?"
        self._cursor.execute(query, (fuzzy_path,))
        return (SoftFileRecord(*row) for row in self._cursor.fetchall())

    def __del__(self):
        self._conn.close()


def populate_index(index: FileIndex, input_dir: Path, wipe: bool = False):
    if wipe:
        index.initialize_schema(drop_existing=True)
        index.wipe_data()
    elif (
        next(index.query_hard_records("%"), None) is not None
        or next(index.query_soft_records("%"), None) is not None
    ):
        raise ValueError("There are existing records in the database. Set wipe=True.")

    if not input_dir.is_dir():
        raise ValueError(f"'{input_dir}' is not a directory or does not exist.")

    for root, _, files in os.walk(input_dir, followlinks=True):
        for file in files:
            file_path = Path(root) / file
            resolved_path = str(file_path.resolve())
            hard_record_exists = any(index.query_hard_records(resolved_path))

            if not hard_record_exists:
                is_binary = False
                number_of_lines = 0
                processed = False
                try:
                    with open(file_path, "rb") as f:
                        is_binary = b"\0" in f.read(1024)
                        number_of_lines = 0
                    if not is_binary:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            try:
                                for _ in f:
                                    number_of_lines += 1
                            except UnicodeDecodeError:
                                is_binary = True
                                number_of_lines = 0
                    processed = True
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")

                hard_file = HardFileRecord(
                    path=resolved_path,
                    size=file_path.stat().st_size,
                    is_binary=is_binary,
                    number_of_lines=number_of_lines,
                    processed=processed,
                )
                index.insert_hard_records([hard_file])

            soft_record = SoftFileRecord(
                path=str(os.path.abspath(file_path)), hard_path=resolved_path
            )
            index.insert_soft_records([soft_record])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate file index database.")
    parser.add_argument("input_dir", type=Path, help="Directory to index files from.")
    parser.add_argument("db_path", type=Path, help="Path to the SQLite database file.")
    parser.add_argument("--wipe", action="store_true", help="Wipe existing data before populating.")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    db_path = args.db_path
    wipe = args.wipe

    file_index = SQLiteFileIndex(db_path)
    populate_index(file_index, input_dir, wipe=wipe)
