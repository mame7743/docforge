"""GitRepoImporter に渡すリポジトリ取り込み設定。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RepoSettings:
    max_file_size: int = 500_000
    include_patterns: list[str] = field(default_factory=list)  # 空=[全ファイル]
    exclude_patterns: list[str] = field(default_factory=list)  # 空=[除外なし]
    branch: str | None = None
    tag: str | None = None
    include_gitignored: bool = False
    include_submodules: bool = False
