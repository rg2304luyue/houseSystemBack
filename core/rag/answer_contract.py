"""Deterministic, conservative validation for cited RAG answers."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Mapping, Sequence


_CITATION_PATTERN = re.compile(r"\[(\d+)\]")
_CLAIM_SPLIT_PATTERN = re.compile(r"(?<=[。！？；!?])|\n+")
_ARABIC_FACT_PATTERN = re.compile(
    r"\d+(?:\.\d+)?(?:%|％|万元|元|年|个月|月|日|条|倍|㎡|平方米)?"
)
_CHINESE_FACT_PATTERN = re.compile(
    r"[零〇一二两三四五六七八九十百千万亿]+"
    r"(?:万元|元|年|个月|月|日|条|倍|成)"
)
_SOCIAL_PATTERN = re.compile(
    r"^(?:希望.*(?:有帮助|能帮到你)|如需.*(?:可以|请)|你还可以继续提问|请问.*[？?])$"
)
_MARKDOWN_PREFIX = re.compile(r"^[\s>#*+\-\d.、]+")
_ATTRIBUTION_PREFIXES = (
    "根据资料",
    "资料显示",
    "相关资料指出",
    "公开资料显示",
)
_DECISIVE_TERMS = (
    "可以",
    "不得",
    "禁止",
    "不能",
    "无需",
    "无须",
    "不需要",
    "随意",
    "没收",
    "扣留",
    "永久",
)


@dataclass(frozen=True)
class CitationValidationResult:
    valid: bool
    reason: str | None = None


def _normalized_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", "", text)


def _chunk_content(chunk: Mapping[str, Any] | object) -> str:
    if isinstance(chunk, Mapping):
        return str(chunk.get("content", ""))
    return str(getattr(chunk, "content", ""))


def _claims(answer: str) -> list[str]:
    claims: list[str] = []
    for part in _CLAIM_SPLIT_PATTERN.split(answer):
        raw = part.strip()
        cleaned = _MARKDOWN_PREFIX.sub("", raw).strip()
        if not cleaned or cleaned.endswith(("：", ":")):
            continue
        if re.match(r"^#{1,6}\s+", raw):
            factual_heading = bool(
                _fact_tokens(cleaned)
                or any(term in _normalized_text(cleaned) for term in _DECISIVE_TERMS)
            )
            if not factual_heading and not _CITATION_PATTERN.search(cleaned):
                continue
        if _SOCIAL_PATTERN.fullmatch(_CITATION_PATTERN.sub("", cleaned).strip("。！？!?")):
            continue
        if re.search(r"[\u4e00-\u9fffA-Za-z0-9]", cleaned):
            claims.append(cleaned)
    return claims


def _fact_tokens(value: str) -> set[str]:
    without_citations = _CITATION_PATTERN.sub("", _normalized_text(value))
    return set(_ARABIC_FACT_PATTERN.findall(without_citations)) | set(
        _CHINESE_FACT_PATTERN.findall(without_citations)
    )


def _extractive_claim(value: str) -> str:
    cleaned = _CITATION_PATTERN.sub("", _normalized_text(value)).strip("。！？；!?")
    for prefix in _ATTRIBUTION_PREFIXES:
        normalized_prefix = _normalized_text(prefix)
        if cleaned.startswith(normalized_prefix):
            cleaned = cleaned[len(normalized_prefix):].lstrip("，,:：")
            break
    return cleaned.strip("。！？；!?")


def _claim_supported(claim: str, evidence: str) -> bool:
    evidence_normalized = _normalized_text(evidence)
    if any(token not in evidence_normalized for token in _fact_tokens(claim)):
        return False
    # Legal modality and destructive outcomes can invert a sentence while
    # retaining the same nouns (for example, contract/deposit).  Treat these
    # as exact evidence-bearing facts instead of allowing fuzzy overlap.
    claim_normalized = _normalized_text(claim)
    if any(
        term in claim_normalized and term not in evidence_normalized
        for term in _DECISIVE_TERMS
    ):
        return False

    # Deterministic token overlap cannot prove entailment: an inverted claim
    # can keep the same nouns. Runtime answers therefore use an extractive
    # contract. Every factual sentence, excluding a bounded attribution
    # prefix, must occur verbatim in its cited evidence after normalization.
    claim_core = _extractive_claim(claim)
    return bool(claim_core) and claim_core in evidence_normalized


def validate_cited_claims(
    answer: str,
    chunks: Sequence[Mapping[str, Any] | object],
) -> CitationValidationResult:
    """Require every substantive statement to be supported by its citations.

    This deliberately favors false refusals over citation laundering.  It is a
    deterministic release/runtime guard, not a claim of complete semantic
    entailment.
    """

    if not answer.strip():
        return CitationValidationResult(False, "empty_answer")
    claims = _claims(answer)
    if not claims:
        return CitationValidationResult(False, "no_claims")
    for claim in claims:
        citations = [int(value) for value in _CITATION_PATTERN.findall(claim)]
        if not citations:
            return CitationValidationResult(False, "uncited_claim")
        if any(index < 1 or index > len(chunks) for index in citations):
            return CitationValidationResult(False, "citation_out_of_bounds")
        evidence = "\n".join(_chunk_content(chunks[index - 1]) for index in citations)
        if not evidence.strip() or not _claim_supported(claim, evidence):
            return CitationValidationResult(False, "claim_not_supported")
    return CitationValidationResult(True)


__all__ = ("CitationValidationResult", "validate_cited_claims")
