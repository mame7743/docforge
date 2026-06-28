"""FormatSettings モデルと ConvertSettings への統合テスト。"""

from pathlib import Path

from core.models.format_settings import FormatSettings
from core.models.settings import ConvertSettings


def test_format_settings_defaults():
    fs = FormatSettings()
    assert fs.encoding is None
    assert fs.extra_noise_patterns == []
    assert fs.enabled_transformers is None  # None=全て使用
    assert fs.split_size_chars is None


def test_format_settings_values():
    fs = FormatSettings(
        encoding="cp932",
        extra_noise_patterns=["Page \\d+"],
        enabled_transformers=["clean_noise"],
        split_size_chars=50_000,
    )
    assert fs.encoding == "cp932"
    assert fs.extra_noise_patterns == ["Page \\d+"]
    assert fs.enabled_transformers == ["clean_noise"]
    assert fs.split_size_chars == 50_000


def test_convert_settings_format_settings_default(tmp_path):
    s = ConvertSettings(input_paths=[], out_dir=tmp_path)
    assert s.format_settings == {}
    assert s.input_encodings == {}


def test_convert_settings_format_settings_roundtrip(tmp_path):
    fs = FormatSettings(split_size_chars=50_000)
    s = ConvertSettings(
        input_paths=[],
        out_dir=tmp_path,
        format_settings={".pdf": fs},
    )
    assert s.format_settings[".pdf"].split_size_chars == 50_000


def test_enabled_transformers_empty_list():
    """空リストは「Transformerなし」を意味する（None とは区別する）。"""
    fs = FormatSettings(enabled_transformers=[])
    assert fs.enabled_transformers == []
    assert fs.enabled_transformers is not None
