import re

from .base import Transformer
from core.models.document import KnowledgeDocument

_NOISE_PATTERNS = [
    re.compile(r"^(前へ|次へ|前のページ|次のページ|戻る|ホーム|目次|トップ|top|home|back|prev|next|previous)[\s　]*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*copyright\s+.*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*all rights reserved\.?\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*page \d+ of \d+\s*$", re.IGNORECASE | re.MULTILINE),
]

_NOISE_TITLE_RE = re.compile(
    r"^(前へ|次へ|ホーム|目次|トップ|Navigation|Contents|Home|Index|Back|Next|Previous)$",
    re.IGNORECASE,
)


class CleanNoiseTransformer(Transformer):
    name = "clean_noise"

    def transform(self, document: KnowledgeDocument, context) -> KnowledgeDocument:
        cleaned = []
        for sec in document.sections:
            text = sec.text
            for pat in _NOISE_PATTERNS:
                text = pat.sub("", text)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

            if _is_noise_section(sec.title, text):
                continue

            sec.text = text
            cleaned.append(sec)

        document.sections = cleaned
        return document


def _is_noise_section(title: str, text: str) -> bool:
    if _NOISE_TITLE_RE.match(title.strip()) and len(text) < 50:
        return True
    return False
