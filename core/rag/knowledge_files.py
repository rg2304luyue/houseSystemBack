"""Knowledge-source discovery, hashing, and loading helpers."""

import hashlib
import logging
from pathlib import Path
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


logger = logging.getLogger(__name__)


def file_sha256(filepath: str | Path) -> str:
    path = Path(filepath)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_sources(
    path: str | Path, allowed_types: tuple[str, ...], *, recursive: bool = True
) -> tuple[Path, ...]:
    root = Path(path)
    if not root.is_dir():
        logger.error("Knowledge data directory does not exist: %s", root)
        return ()
    suffixes = {f".{value.lower().lstrip('.')}" for value in allowed_types}
    candidates = root.rglob("*") if recursive else root.iterdir()
    return tuple(
        item.resolve()
        for item in sorted(candidates, key=lambda value: value.as_posix().casefold())
        if item.is_file() and item.suffix.lower() in suffixes
    )


# Keep parsing tokens ASCII-only in source so Windows code pages cannot corrupt them.
_LISTING_START = re.compile(r"(?=^\[\u623f\u6e90\s+[^\]]+\]\s*$)", re.MULTILINE)
_FIELD_LINE = re.compile(r"^([^\uff1a\n]+)\uff1a\s*(.+)$", re.MULTILINE)
_METADATA_FIELDS = {
    "\u6765\u6e90\u94fe\u63a5": "source_url",
    "\u91c7\u96c6\u65e5\u671f": "collected_at",
    "\u533a\u57df": "region",
    "\u751f\u6548\u65e5\u671f": "effective_at",
    "\u9002\u7528\u8303\u56f4": "jurisdiction",
}


def _document_title(content: str, path: Path) -> str:
    for line in content.splitlines():
        title = line.strip().lstrip("#").strip()
        if title:
            return title[:200]
    return path.stem


def _generic_knowledge_type(path: Path) -> str:
    normalized = "/".join(part.casefold() for part in path.parts)
    if any(token in normalized for token in ("policy", "policies", "\u653f\u7b56", "\u6cd5\u89c4")):
        return "policy"
    return "guide"


def load_source(filepath: str | Path) -> list[Document]:
    """Load PDF pages or listing-level TXT records with citation metadata."""
    path = Path(filepath)
    if path.suffix.lower() == ".pdf":
        documents = PyPDFLoader(str(path)).load()
        for document in documents:
            document.metadata.update({
                "title": path.stem,
                "knowledge_type": _generic_knowledge_type(path),
                "verification_status": "source_required",
            })
        return documents
    if path.suffix.lower() != ".txt":
        return []

    content = path.read_text(encoding="utf-8")
    starts = list(_LISTING_START.finditer(content))
    if not starts:
        fields = {key.strip(): value.strip() for key, value in _FIELD_LINE.findall(content)}
        metadata: dict[str, object] = {
            "source": str(path),
            "title": _document_title(content, path),
            "knowledge_type": _generic_knowledge_type(path),
            "verification_status": "source_required",
        }
        for source_key, metadata_key in _METADATA_FIELDS.items():
            value = fields.get(source_key)
            if value:
                metadata[metadata_key] = value
        return [Document(page_content=content, metadata=metadata)]

    common_fields = {
        key.strip(): value.strip()
        for key, value in _FIELD_LINE.findall(content[:starts[0].start()])
    }
    documents: list[Document] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(content)
        section = content[start.start():end].strip()
        fields = {key.strip(): value.strip() for key, value in _FIELD_LINE.findall(section)}
        header = section.splitlines()[0].strip("[]")
        metadata: dict[str, object] = {
            "source": str(path),
            "section": header,
            "title": _document_title(content, path),
            "knowledge_type": "historical_snapshot",
            "verification_status": "unverified_public_snapshot",
            "is_current": False,
        }
        for source_key, metadata_key in _METADATA_FIELDS.items():
            value = fields.get(source_key) or common_fields.get(source_key)
            if value:
                metadata[metadata_key] = value
        match = re.search(r"CS-PUBLIC-\d{8}-\d{3}", header)
        if match:
            metadata["house_num"] = match.group(0)
        documents.append(Document(page_content=section, metadata=metadata))
    return documents
