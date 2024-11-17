import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, List
import os
from pathlib import Path
import argparse


@dataclass
class FileRecord:
    path: str
    size: int
    is_binary: bool
    number_of_lines: int
    processed: bool = True


class FileIndex(ABC):
    @abstractmethod
    def initialize_schema(self):  # pragma: no cover
        pass

    @abstractmethod
    def wipe_data(self):  # pragma: no cover
        pass

    @abstractmethod
    def insert_records(self, records: List[FileRecord]) -> bool:  # pragma: no cover
        pass

    @abstractmethod
    def run_query(self, fuzzy_path: str) -> Iterator[FileRecord]:  # pragma: no cover
        pass


class SQLiteFileIndex(FileIndex):
    """
    Example usage:
    index = SQLiteFileIndex('/path/to/database.db')
    index.initialize_schema()
    index.wipe_data()
    record = FileRecord(path='/path/to/file.txt', size=1234, is_binary=False, number_of_lines=100, processed=True)
    index.insert_record(record)
    results = index.run_query('SELECT * FROM file_index')
    print(results)
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()

    def initialize_schema(self, drop_existing: bool = False):
        if drop_existing:
            self._cursor.execute("DROP TABLE IF EXISTS files")
        self._cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                size INTEGER,
                is_binary BOOLEAN,
                number_of_lines INTEGER,
                processed BOOLEAN
            )
        """
        )
        self._conn.commit()

    def wipe_data(self):
        self._cursor.execute("DELETE FROM files")
        self._conn.commit()

    def insert_records(self, records: List[FileRecord]) -> bool:
        try:
            for record in records:
                self._cursor.execute(
                    "INSERT INTO files (path, size, is_binary, number_of_lines, processed) VALUES (?, ?, ?, ?, ?)",
                    (
                        record.path,
                        record.size,
                        record.is_binary,
                        record.number_of_lines,
                        record.processed,
                    ),
                )
            self._conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False

    def run_query(self, fuzzy_path: str) -> Iterator[FileRecord]:
        query = "SELECT * FROM files WHERE path LIKE ?"
        self._cursor.execute(query, (fuzzy_path,))
        return (FileRecord(*row) for row in self._cursor.fetchall())

    def __del__(self):
        self._conn.close()


def populate_index(file_index: FileIndex, input_dir: Path, wipe: bool = False):
    if wipe:
        file_index.initialize_schema()
        file_index.wipe_data()
    elif next(file_index.run_query("%"), False):
        raise ValueError("There are existing records in the database. Set wipe=True.")

    for root, _, files in os.walk(input_dir, followlinks=True):
        for file in files:
            file_path = Path(root) / file
            file_record = FileRecord(
                path=str(os.path.abspath(file_path)),
                size=file_path.stat().st_size,
                is_binary=False,
                number_of_lines=0,
                processed=False,
            )
            try:
                with open(file_path, "rb") as f:
                    file_record.is_binary = b"\0" in f.read(1024)
                    file_record.number_of_lines = 0
                if not file_record.is_binary:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        try:
                            for _ in f:
                                file_record.number_of_lines += 1
                        except UnicodeDecodeError:
                            file_record.is_binary = True
                            file_record.number_of_lines = 0
                file_record.processed = True
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
            file_index.insert_records([file_record])


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
    file_index.initialize_schema(drop_existing=wipe)
    populate_index(file_index, input_dir, wipe=wipe)
