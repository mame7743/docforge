"""Git リポジトリ / ディレクトリを gitingest でナレッジ化する Importer。

gitingest が返す (summary, tree, content) を KnowledgeDocument へ変換する。
ファイルごとにセクションを1つ作成し、最初の2セクションは概要とファイルツリーにする。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .base import Importer
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext

_FILE_SEP = re.compile(
    r"^={40,}\nFILE: (.+?)\n={40,}\n",
    re.MULTILINE,
)


class GitRepoImporter(Importer):
    name = "gitrepo"
    supported_extensions: set[str] = set()  # ディレクトリは拡張子なし

    def __init__(
        self,
        max_file_size: int = 500_000,
        include_patterns: str | set[str] | None = None,
        exclude_patterns: str | set[str] | None = None,
        branch: str | None = None,
        tag: str | None = None,
        include_gitignored: bool = False,
        include_submodules: bool = False,
    ) -> None:
        self.max_file_size = max_file_size
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.branch = branch
        self.tag = tag
        self.include_gitignored = include_gitignored
        self.include_submodules = include_submodules

    def can_import(self, path: Path) -> bool:
        return path.is_dir()

    def import_file(self, path: Path, context: "PipelineContext") -> KnowledgeDocument:
        try:
            from gitingest import ingest
        except ImportError:
            context.warn("gitingest がインストールされていません: pip install gitingest")
            return _empty_doc(path)

        resolved = path.resolve()
        repo_name = resolved.name or resolved.parts[-1]

        try:
            summary, tree, content = ingest(
                str(resolved),
                max_file_size=self.max_file_size,
                include_patterns=self.include_patterns,
                exclude_patterns=self.exclude_patterns,
                branch=self.branch,
                tag=self.tag,
                include_gitignored=self.include_gitignored,
                include_submodules=self.include_submodules,
            )
        except Exception as e:
            context.warn(f"gitingest 失敗 ({repo_name}): {e}")
            return _empty_doc(path)

        doc_id = re.sub(r"[^a-zA-Z0-9_]", "_", repo_name)[:64]
        doc = KnowledgeDocument(
            id=doc_id,
            title=repo_name,
            source_path=path,
            source_type="gitrepo",
            metadata={"source_dir": str(path)},
        )

        order = 0

        # セクション0: リポジトリ概要
        doc.sections.append(KnowledgeSection(
            id=f"{doc_id}_s0000",
            title=f"{repo_name} — 概要",
            text=summary,
            level=1,
            order=order,
            source_ref=str(resolved),
            section_path=[repo_name],
            metadata={"source_dir": str(resolved)},
        ))
        order += 1

        # セクション1: ファイルツリー
        doc.sections.append(KnowledgeSection(
            id=f"{doc_id}_s0001",
            title=f"{repo_name} — ファイルツリー",
            text=f"```\n{tree}\n```",
            level=1,
            order=order,
            source_ref=str(resolved),
            section_path=[repo_name],
            metadata={"source_dir": str(resolved)},
        ))
        order += 1

        # セクション2〜: ファイルごとの内容
        for file_path, file_content in _parse_content(content):
            parts = file_path.replace("\\", "/").split("/")
            level = 2 if len(parts) > 1 else 1
            ext = Path(file_path).suffix.lstrip(".")
            formatted = f"```{ext}\n{file_content}\n```" if ext else file_content

            doc.sections.append(KnowledgeSection(
                id=f"{doc_id}_s{order:04d}",
                title=file_path,
                text=formatted,
                level=level,
                order=order,
                source_ref=str(resolved / file_path),
                section_path=[repo_name] + parts[:-1],
                metadata={"source_file": file_path, "source_dir": str(resolved)},
            ))
            order += 1

        return doc


def _parse_content(content: str) -> list[tuple[str, str]]:
    """gitingest の content 文字列をファイルパスと本文のペアに分割する。"""
    parts = _FILE_SEP.split(content)
    # split() の結果: [先頭テキスト, file1_path, file1_body, file2_path, file2_body, ...]
    results: list[tuple[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        file_path = parts[i].strip()
        body = parts[i + 1].rstrip()
        if file_path and body:
            results.append((file_path, body))
        i += 2
    return results


def _empty_doc(path: Path) -> KnowledgeDocument:
    doc_id = re.sub(r"[^a-zA-Z0-9_]", "_", path.name)[:64]
    return KnowledgeDocument(
        id=doc_id,
        title=path.name,
        source_path=path,
        source_type="gitrepo",
    )
