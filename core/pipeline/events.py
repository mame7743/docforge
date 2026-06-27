from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportStarted:
    path: Path
    importer_name: str


@dataclass
class ImportFinished:
    path: Path
    section_count: int


@dataclass
class TransformStarted:
    transformer_name: str


@dataclass
class WriteStarted:
    writer_name: str


@dataclass
class WriteFinished:
    writer_name: str
    output_files: list[Path]
