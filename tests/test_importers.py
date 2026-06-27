import tempfile
from pathlib import Path

import pytest

from core.importers import TextImporter, MarkdownImporter, HtmlImporter, ImporterRegistry
from core.pipeline.context import PipelineContext


def _ctx():
    return PipelineContext(work_dir=Path(tempfile.mkdtemp()))


# TextImporter

def test_text_importer_basic(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("Hello world\n\nSecond paragraph", encoding="utf-8")
    doc = TextImporter().import_file(f, _ctx())
    assert doc.title == "hello"
    assert doc.source_type == "text"
    assert len(doc.sections) == 2
    assert doc.sections[0].text == "Hello world"


def test_text_importer_empty(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    ctx = _ctx()
    doc = TextImporter().import_file(f, ctx)
    assert doc.sections == []
    assert len(ctx.warnings) == 1


# MarkdownImporter

def test_markdown_importer_headings(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nbody\n\n## Section A\n\ntext A\n\n## Section B\n\ntext B\n", encoding="utf-8")
    doc = MarkdownImporter().import_file(f, _ctx())
    assert len(doc.sections) == 3
    assert doc.sections[0].title == "Title"
    assert doc.sections[1].title == "Section A"


def test_markdown_importer_no_headings(tmp_path):
    f = tmp_path / "plain.md"
    f.write_text("Just some text without headings.", encoding="utf-8")
    doc = MarkdownImporter().import_file(f, _ctx())
    assert len(doc.sections) == 1
    assert doc.sections[0].text == "Just some text without headings."


def test_markdown_importer_links(tmp_path):
    f = tmp_path / "links.md"
    f.write_text("# Head\n\n[click](http://example.com) and ![img](images/foo.png)\n", encoding="utf-8")
    doc = MarkdownImporter().import_file(f, _ctx())
    sec = doc.sections[0]
    assert "http://example.com" in sec.links
    assert "images/foo.png" in sec.assets


# HtmlImporter

def test_html_importer_basic(tmp_path):
    f = tmp_path / "page.html"
    f.write_text("<html><head><title>My Page</title></head><body><h1>Hello</h1><p>World</p></body></html>", encoding="utf-8")
    doc = HtmlImporter().import_file(f, _ctx())
    assert doc.title == "My Page"
    assert len(doc.sections) >= 1
    assert doc.sections[0].title == "Hello"
    assert "World" in doc.sections[0].text


# ImporterRegistry

def test_registry_find(tmp_path):
    reg = ImporterRegistry()
    reg.register(TextImporter())
    reg.register(MarkdownImporter())
    txt = tmp_path / "a.txt"
    txt.touch()
    assert reg.find(txt).name == "text"
    md = tmp_path / "b.md"
    md.touch()
    assert reg.find(md).name == "markdown"


def test_registry_unsupported(tmp_path):
    reg = ImporterRegistry()
    reg.register(TextImporter())
    f = tmp_path / "file.xyz"
    f.touch()
    with pytest.raises(ValueError):
        reg.find(f)
