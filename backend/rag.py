import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb

from backend.config import Settings
from backend.ollama_client import OllamaClient


@dataclass(frozen=True)
class RetrievedSource:
    document: str
    category: str
    text: str
    chunk_id: str = ""
    area: str = ""
    source_ids: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    canonical_url: str = ""
    source_section: str = ""
    consulted_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedContext:
    text: str
    sources: list[RetrievedSource]

    @property
    def has_context(self) -> bool:
        return bool(self.text.strip())


class Retriever:
    def __init__(self, settings: Settings, ollama_client: OllamaClient) -> None:
        self.settings = settings
        self.ollama_client = ollama_client
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection)

    async def search(self, question: str, n_results: int = 4) -> RetrievedContext:
        if self.collection.count() == 0:
            return RetrievedContext(text="", sources=[])

        embedding = await self.ollama_client.embed(question)
        results = self.collection.query(query_embeddings=[embedding], n_results=n_results)

        documents = _first_result(results.get("documents"))
        metadatas = _first_result(results.get("metadatas"))

        sources: list[RetrievedSource] = []
        context_parts: list[str] = []

        for index, document_text in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            source = RetrievedSource(
                document=str(metadata.get("document", "desconocido")),
                category=str(metadata.get("category", "general")),
                text=document_text,
                chunk_id=str(metadata.get("chunk_id", "")),
                area=str(metadata.get("area", "")),
                source_ids=tuple(_decode_string_list(metadata.get("source_ids"))),
                questions=tuple(_decode_string_list(metadata.get("questions"))),
                canonical_url=str(metadata.get("canonical_url", "")),
                source_section=str(metadata.get("source_section", "")),
                consulted_at=str(metadata.get("consulted_at", "")),
                metadata=_decode_dict(metadata.get("metadata_json")),
            )
            sources.append(source)
            context_parts.append(f"{_source_header(source)}\n{source.text.strip()}")

        return RetrievedContext(text="\n\n".join(context_parts), sources=sources)


def _first_result(value: Any) -> list[Any]:
    if isinstance(value, list) and value and isinstance(value[0], list):
        return value[0]
    return []


def _source_header(source: RetrievedSource) -> str:
    parts = [
        f"area={source.area or source.category}",
        f"category={source.category}",
        f"document={source.document}",
    ]
    if source.chunk_id:
        parts.append(f"chunk_id={source.chunk_id}")
    if source.source_ids:
        parts.append(f"source_ids={', '.join(source.source_ids)}")
    if source.source_section:
        parts.append(f"section={source.source_section}")
    if source.canonical_url:
        parts.append(f"url={source.canonical_url}")
    return f"[{'; '.join(parts)}]"


def _decode_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = [item.strip() for item in value.split(",")]
    else:
        decoded = value

    if not isinstance(decoded, list):
        return []
    return [str(item) for item in decoded if str(item).strip()]


def _decode_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def ensure_data_directories() -> None:
    Path("data/processed").mkdir(parents=True, exist_ok=True)
