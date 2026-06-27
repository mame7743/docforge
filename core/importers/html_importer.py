import re
from pathlib import Path

from .base import Importer
from core.models.document import KnowledgeDocument
from core.models.section import KnowledgeSection

try:
    from bs4 import BeautifulSoup, Tag
    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False

_NOISE_SELECTORS = [
    "nav", "header", "footer", ".nav", ".navigation", ".sidebar",
    ".breadcrumb", ".toc", "#toc", ".noprint", "script", "style",
]

_HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


class HtmlImporter(Importer):
    name = "html"
    supported_extensions = {".html", ".htm"}

    def import_file(self, path: Path, context) -> KnowledgeDocument:
        if not _BS4_AVAILABLE:
            context.warn("beautifulsoup4 not installed; HTML import unavailable")
            return _empty_doc(path)

        encoding = getattr(context, "encoding_hint", None) or "utf-8"
        try:
            raw = path.read_bytes()
            html = raw.decode(encoding, errors="replace")
        except Exception as e:
            context.warn(f"Failed to read {path.name}: {e}")
            return _empty_doc(path)

        soup = BeautifulSoup(html, "html.parser")
        _remove_noise(soup)

        doc_id = _make_id(path)
        title = _extract_title(soup) or path.stem

        doc = KnowledgeDocument(
            id=doc_id,
            title=title,
            source_path=path,
            source_type="html",
            metadata={"source_file": str(path.name)},
        )

        body = soup.find("body") or soup
        sections = _parse_sections(body, doc_id, path, title)

        if not sections:
            text = body.get_text(separator="\n", strip=True)
            sec = KnowledgeSection(
                id=f"{doc_id}_body",
                title=title,
                text=text,
                level=1,
                order=0,
                source_ref=str(path),
                section_path=[title],
                metadata={"source_file": str(path.name)},
            )
            doc.sections.append(sec)
        else:
            doc.sections = sections

        return doc


def _empty_doc(path: Path) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=_make_id(path),
        title=path.stem,
        source_path=path,
        source_type="html",
    )


def _make_id(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", path.stem)[:64]


def _remove_noise(soup) -> None:
    for selector in _NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()


def _extract_title(soup) -> str | None:
    tag = soup.find("title")
    if tag:
        return tag.get_text(strip=True)
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return None


def _parse_sections(body, doc_id: str, path: Path, doc_title: str) -> list[KnowledgeSection]:
    headings = body.find_all(_HEADING_TAGS)
    if not headings:
        return []

    sections: list[KnowledgeSection] = []
    heading_stack: list[str] = []

    for i, h in enumerate(headings):
        level = int(h.name[1])
        title = h.get_text(strip=True)

        # collect sibling content until next heading
        body_parts: list[str] = []
        links: list[str] = []
        assets: list[str] = []

        for sib in h.next_siblings:
            if hasattr(sib, "name") and sib.name in _HEADING_TAGS:
                break
            if not hasattr(sib, "name") or sib.name is None:
                # NavigableString (plain text node)
                text = str(sib).strip()
                if text:
                    body_parts.append(text)
                continue
            chunk = sib.get_text(separator="\n", strip=True)
            if chunk:
                body_parts.append(chunk)
            for a in sib.find_all("a", href=True):
                links.append(a["href"])
            for img in sib.find_all("img"):
                src = img.get("src", "")
                if src:
                    assets.append(src)

        while len(heading_stack) >= level:
            heading_stack.pop()
        heading_stack.append(title)

        sec = KnowledgeSection(
            id=f"{doc_id}_s{i:04d}",
            title=title,
            text="\n\n".join(body_parts),
            level=level,
            order=i,
            source_ref=str(path),
            section_path=list(heading_stack),
            links=links,
            assets=assets,
            metadata={"source_file": str(path.name)},
        )
        sections.append(sec)

    return sections
