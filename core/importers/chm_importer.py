from __future__ import annotations

"""CHM (.chm) の Importer。

Windows の hh.exe -decompile でファイルを展開し、
.hhc（目次ファイル）を読んで HTML ページを目次順に処理する。

非 Windows では警告を出して空ドキュメントを返す。
将来は 7z / libmspack などの代替バックエンドに差し替えられる設計。
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .base import Importer
from .html_importer import HtmlImporter
from core.models.document import KnowledgeDocument
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext

try:
    from bs4 import BeautifulSoup
    _BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None  # type: ignore[assignment,misc]
    _BS4_AVAILABLE = False


class ChmImporter(Importer):
    name = "chm"
    supported_extensions = {".chm"}

    def __init__(self) -> None:
        self._html_importer = HtmlImporter()

    def import_file(self, path: Path, context: PipelineContext) -> KnowledgeDocument:
        doc_id = _make_id(path)

        if sys.platform != "win32":
            raise ImportError(
                f"CHM import requires Windows (hh.exe). Platform: {sys.platform}"
            )

        with tempfile.TemporaryDirectory(prefix="docforge_chm_") as tmp:
            extract_dir = Path(tmp)
            try:
                subprocess.run(
                    ["hh.exe", "-decompile", str(extract_dir), str(path)],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                raise ImportError(f"hh.exe failed for {path.name}: {e}") from e

            return self._build_document(path, extract_dir, doc_id, context)

    def _build_document(
        self, path: Path, extract_dir: Path, doc_id: str, context: PipelineContext
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            id=doc_id,
            title=path.stem,
            source_path=path,
            source_type="chm",
            metadata={"source_file": str(path.name)},
        )

        hhc_files = list(extract_dir.rglob("*.hhc"))
        ordered_pages: list[Path] = []

        if hhc_files:
            ordered_pages = _parse_hhc(hhc_files[0], extract_dir, context)
        else:
            context.warn(f".hhc not found in {path.name}: fallback to filename order")

        # .hhc にないページは末尾に追加する
        all_html = sorted(extract_dir.rglob("*.htm")) + sorted(extract_dir.rglob("*.html"))
        ordered_set = set(ordered_pages)
        remaining = [p for p in all_html if p not in ordered_set]
        pages = ordered_pages + remaining

        order = 0
        for html_path in pages:
            page_doc = self._html_importer.import_file(html_path, context)
            for sec in page_doc.sections:
                # CHM 内の各ページのセクション ID が衝突しないよう doc_id を prefix として付ける
                sec.id = f"{doc_id}_{sec.id}"
                sec.order = order
                sec.metadata["source_file"] = f"{path.name}/{html_path.name}"
                sec.source_ref = f"{path.name}/{html_path.name}"
                order += 1
            doc.sections.extend(page_doc.sections)
            doc.warnings.extend(page_doc.warnings)

        return doc


def _make_id(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", path.stem)[:64]


def _parse_hhc(hhc_path: Path, base_dir: Path, context: PipelineContext) -> list[Path]:
    """HHC（HTML Help Contents）を解析してページの順序を取得する。

    HHC は HTML 形式の XML で、<param name="Local" value="page.htm"> の形で
    ページファイルへのパスが記録されている。
    """
    if not _BS4_AVAILABLE:
        context.warn(".hhc parsing requires beautifulsoup4")
        return []

    try:
        raw = hhc_path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        context.warn(f"Failed to read .hhc: {e}")
        return []

    soup = BeautifulSoup(text, "html.parser")
    pages: list[Path] = []

    for param in soup.find_all("param", {"name": re.compile(r"local", re.I)}):
        val: str = param.get("value", "")
        if val:
            candidate = base_dir / val.replace("\\", "/")
            if candidate.exists():
                pages.append(candidate)

    return pages
