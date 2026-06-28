from __future__ import annotations

"""ナビゲーションリンク・著作権表記などのノイズをセクションから除去する Transformer。

CHM や Web ページには「前へ / 次へ」「Copyright ...」といった本文と無関係な
テキストが含まれることが多い。これらを除去することで RAG の精度を高める。
"""

import re

from .base import Transformer
from core.models.document import KnowledgeDocument
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.pipeline.context import PipelineContext

# 行単位で除去するノイズパターン
_NOISE_PATTERNS = [
    re.compile(
        r"^(前へ|次へ|前のページ|次のページ|戻る|ホーム|目次|トップ|top|home|back|prev|next|previous)[\s　]*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(r"^\s*copyright\s+.*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*all rights reserved\.?\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*page \d+ of \d+\s*$", re.IGNORECASE | re.MULTILINE),
]

# このタイトルを持ち本文がほぼ空のセクションはナビゲーション専用ページとして丸ごと除去する
_NOISE_TITLE_RE = re.compile(
    r"^(前へ|次へ|ホーム|目次|トップ|Navigation|Contents|Home|Index|Back|Next|Previous)$",
    re.IGNORECASE,
)


class CleanNoiseTransformer(Transformer):
    name = "clean_noise"

    def transform(self, document: KnowledgeDocument, context: PipelineContext) -> KnowledgeDocument:
        patterns = list(_NOISE_PATTERNS)
        fmt = context.format_settings
        if fmt and fmt.extra_noise_patterns:
            for raw in fmt.extra_noise_patterns:
                try:
                    patterns.append(re.compile(raw, re.IGNORECASE | re.MULTILINE))
                except re.error as e:
                    context.warn(f"Invalid noise pattern '{raw}': {e}")

        cleaned = []
        for sec in document.sections:
            text = sec.text
            for pat in patterns:
                text = pat.sub("", text)
            # 連続する空行を最大2行に圧縮する
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

            if _is_noise_section(sec.title, text):
                continue

            sec.text = text
            cleaned.append(sec)

        document.sections = cleaned
        return document


def _is_noise_section(title: str, text: str) -> bool:
    """ナビゲーション専用セクションかどうかを判定する。"""
    if _NOISE_TITLE_RE.match(title.strip()) and len(text) < 50:
        return True
    return False
