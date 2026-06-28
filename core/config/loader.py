"""YAMLバッチコンフィグを ConvertSettings に変換するローダー。"""

from __future__ import annotations

import glob as glob_module
from pathlib import Path

import yaml

from core.models.settings import ConvertSettings
from core.models.format_settings import FormatSettings
from core.models.repo_settings import RepoSettings
from core.models.split_settings import SplitSettings


def load_config(config_path: Path) -> ConvertSettings:
    """YAMLバッチコンフィグファイルを読み込み ConvertSettings を返す。

    すべてのパスは config_path の親ディレクトリを基準に解決される。
    """
    text = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    base_dir = config_path.parent

    input_paths, input_encodings = _parse_inputs(data.get("inputs", []), base_dir)

    output = data.get("output", {})
    out_dir = base_dir / output.get("dir", "out")

    format_settings: dict[str, FormatSettings] = {}
    for ext, fdata in (data.get("formats") or {}).items():
        ext = ext if ext.startswith(".") else f".{ext}"
        format_settings[ext.lower()] = _parse_format_settings(fdata or {})

    repo_settings = _parse_repo_settings(data.get("repository") or {})
    split_settings = _parse_split_settings(data.get("split") or {})

    return ConvertSettings(
        input_paths=input_paths,
        input_encodings=input_encodings,
        out_dir=out_dir,
        export_markdown=output.get("markdown", True),
        export_notebooklm=output.get("notebooklm", True),
        export_jsonl=output.get("jsonl", False),
        export_report=output.get("report", True),
        split_size_chars=output.get("split_size", 100_000),
        format_settings=format_settings,
        repo_settings=repo_settings,
        split_settings=split_settings,
    )


def _parse_inputs(
    entries: list, base_dir: Path
) -> tuple[list[Path], dict[Path, str]]:
    paths: list[Path] = []
    encodings: dict[Path, str] = {}

    for entry in entries:
        if isinstance(entry, str):
            resolved = _expand_glob(entry, base_dir)
            paths.extend(resolved)
        elif isinstance(entry, dict):
            raw_path = entry.get("path", "")
            resolved = _expand_glob(raw_path, base_dir)
            paths.extend(resolved)
            if "encoding" in entry:
                for p in resolved:
                    encodings[p] = entry["encoding"]
        else:
            raise ValueError(f"inputs エントリの形式が不正です: {entry!r}")

    return paths, encodings


def _expand_glob(pattern: str, base_dir: Path) -> list[Path]:
    """globパターンを base_dir 基準で展開する。globなしは単一パスとして返す。"""
    if any(c in pattern for c in ("*", "?", "[")):
        abs_pattern = str(base_dir / pattern)
        matched = sorted(glob_module.glob(abs_pattern, recursive=True))
        return [Path(p) for p in matched]
    return [base_dir / pattern]


def _parse_format_settings(data: dict) -> FormatSettings:
    return FormatSettings(
        encoding=data.get("encoding"),
        extra_noise_patterns=data.get("extra_noise_patterns") or [],
        enabled_transformers=data.get("enabled_transformers"),
        split_size_chars=data.get("split_size"),
    )


def _parse_repo_settings(data: dict) -> RepoSettings:
    return RepoSettings(
        max_file_size=data.get("max_file_size", 500_000),
        include_patterns=data.get("include_patterns") or [],
        exclude_patterns=data.get("exclude_patterns") or [],
        branch=data.get("branch"),
        tag=data.get("tag"),
        include_gitignored=bool(data.get("include_gitignored", False)),
        include_submodules=bool(data.get("include_submodules", False)),
    )


def _parse_split_settings(data: dict) -> SplitSettings:
    return SplitSettings(
        enabled=bool(data.get("enabled", False)),
        metric=data.get("metric", "chars"),
        threshold=data.get("threshold", 500_000),
        max_sources=data.get("max_sources", 50),
        overflow=data.get("overflow", "warn"),
    )
