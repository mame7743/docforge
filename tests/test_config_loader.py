"""core.config.loader のテスト。"""

from pathlib import Path

import pytest

from core.config.loader import load_config


def _write_yaml(tmp_path: Path, content: str) -> Path:
    cfg = tmp_path / "docforge.yaml"
    cfg.write_text(content, encoding="utf-8")
    return cfg


def test_basic_load(tmp_path):
    (tmp_path / "file.md").touch()
    cfg = _write_yaml(tmp_path, f"""\
inputs:
  - file.md
output:
  dir: out
  markdown: true
  notebooklm: false
  jsonl: true
  split_size: 50000
""")
    s = load_config(cfg)
    assert s.input_paths == [tmp_path / "file.md"]
    assert s.out_dir == tmp_path / "out"
    assert s.export_markdown is True
    assert s.export_notebooklm is False
    assert s.export_jsonl is True
    assert s.split_size_chars == 50_000


def test_glob_expansion(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("a.txt", "b.txt", "c.txt"):
        (docs / name).touch()

    cfg = _write_yaml(tmp_path, "inputs:\n  - docs/*.txt\n")
    s = load_config(cfg)
    assert len(s.input_paths) == 3
    assert all(p.suffix == ".txt" for p in s.input_paths)


def test_per_path_encoding(tmp_path):
    f = tmp_path / "data.txt"
    f.touch()
    cfg = _write_yaml(tmp_path, """\
inputs:
  - path: data.txt
    encoding: cp932
""")
    s = load_config(cfg)
    assert s.input_encodings[tmp_path / "data.txt"] == "cp932"


def test_format_settings_parsed(tmp_path):
    cfg = _write_yaml(tmp_path, """\
inputs: []
formats:
  .pdf:
    extra_noise_patterns:
      - "Page \\\\d+"
    split_size: 50000
  txt:
    encoding: cp932
    enabled_transformers:
      - clean_noise
""")
    s = load_config(cfg)
    assert ".pdf" in s.format_settings
    assert s.format_settings[".pdf"].extra_noise_patterns == ["Page \\d+"]
    assert s.format_settings[".pdf"].split_size_chars == 50_000
    assert ".txt" in s.format_settings
    assert s.format_settings[".txt"].encoding == "cp932"
    assert s.format_settings[".txt"].enabled_transformers == ["clean_noise"]


def test_no_formats_key(tmp_path):
    cfg = _write_yaml(tmp_path, "inputs: []\n")
    s = load_config(cfg)
    assert s.format_settings == {}


def test_defaults_when_output_missing(tmp_path):
    cfg = _write_yaml(tmp_path, "inputs: []\n")
    s = load_config(cfg)
    assert s.export_markdown is True
    assert s.export_notebooklm is True
    assert s.export_jsonl is False
    assert s.export_report is True
    assert s.split_size_chars == 100_000


def test_enabled_transformers_none_when_absent(tmp_path):
    """YAMLで enabled_transformers が省略された場合は None になる（全て使用）。"""
    cfg = _write_yaml(tmp_path, """\
inputs: []
formats:
  .md:
    encoding: utf-8
""")
    s = load_config(cfg)
    assert s.format_settings[".md"].enabled_transformers is None
