from pathlib import Path
from core.models import KnowledgeDocument, KnowledgeSection, KnowledgeAsset, ConvertSettings, ConvertResult


def test_knowledge_document_defaults():
    doc = KnowledgeDocument(id="d1", title="Test", source_path=None, source_type="text")
    assert doc.sections == []
    assert doc.assets == []
    assert doc.metadata == {}
    assert doc.warnings == []


def test_knowledge_section_defaults():
    sec = KnowledgeSection(id="s1", title="Section", text="body")
    assert sec.level == 1
    assert sec.order == 0
    assert sec.links == []
    assert sec.keywords == []


def test_convert_settings_defaults():
    settings = ConvertSettings(input_paths=[Path("a.txt")], out_dir=Path("out"))
    assert settings.export_markdown is True
    assert settings.export_notebooklm is True
    assert settings.export_jsonl is False
    assert settings.split_size_chars == 100_000


def test_convert_result_defaults():
    result = ConvertResult()
    assert result.document_count == 0
    assert result.warnings == []
