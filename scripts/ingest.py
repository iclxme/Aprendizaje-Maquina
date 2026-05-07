import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import chromadb

from backend.config import get_settings
from backend.ollama_client import OllamaClient
from backend.rag import ensure_data_directories

TRACEABLE_CHUNKS_FILE = Path("data/processed/chunks.jsonl")
REQUIRED_CHUNK_FIELDS = ("id", "text", "area", "category", "document", "source_ids", "questions")
MetadataValue = str | int | float | bool


async def ingest(reset: bool = False) -> None:
    ensure_data_directories()
    chunks = _load_traceable_chunks(TRACEABLE_CHUNKS_FILE)
    print(f"Ingesta trazable: {TRACEABLE_CHUNKS_FILE} ({len(chunks)} chunks).")

    settings = get_settings()
    ollama_client = OllamaClient(settings)
    chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    if reset:
        try:
            chroma_client.delete_collection(settings.chroma_collection)
        except ValueError:
            pass

    collection = chroma_client.get_or_create_collection(name=settings.chroma_collection)
    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, MetadataValue]] = []

    for chunk in chunks:
        chunk_id = str(chunk["id"])
        text = str(chunk["text"]).strip()
        if not text:
            continue

        print(f"Generando embedding: {chunk_id}")
        ids.append(chunk_id)
        documents.append(text)
        embeddings.append(await ollama_client.embed(text))
        metadatas.append(_metadata_from_chunk(chunk))

    if not documents:
        print("No se encontraron fragmentos con contenido para ingestar.")
        return

    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    print(f"Ingesta completada: {len(documents)} fragmentos en '{settings.chroma_collection}'.")


def _load_traceable_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo trazable de chunks: {path}")

    chunks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue

        try:
            chunk = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON invalido en {path}:{line_number}: {exc}") from exc

        missing = [field for field in REQUIRED_CHUNK_FIELDS if not _has_required_value(field, chunk)]
        if missing:
            raise ValueError(f"Chunk incompleto en {path}:{line_number}; faltan: {', '.join(missing)}")

        chunk_id = str(chunk["id"])
        if chunk_id in seen_ids:
            raise ValueError(f"Chunk duplicado en {path}:{line_number}: {chunk_id}")

        seen_ids.add(chunk_id)
        chunks.append(chunk)

    return chunks


def _metadata_from_chunk(chunk: dict[str, Any]) -> dict[str, MetadataValue]:
    metadata = _dict_or_empty(chunk.get("metadata"))
    chroma_metadata: dict[str, MetadataValue] = {
        "chunk_id": str(chunk["id"]),
        "area": str(chunk.get("area", "")),
        "category": str(chunk.get("category", "general")),
        "document": str(chunk.get("document", "")),
        "source_ids": _json_string(_string_list(chunk.get("source_ids"))),
        "questions": _json_string(_string_list(chunk.get("questions"))),
        "metadata_json": _json_string(metadata),
    }

    for key, value in metadata.items():
        if isinstance(value, str | int | float | bool):
            chroma_metadata[key] = value
        elif value is not None:
            chroma_metadata[key] = _json_string(value)

    return chroma_metadata


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _has_required_value(field: str, chunk: dict[str, Any]) -> bool:
    value = chunk.get(field)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return field == "questions" or bool(value)
    return value is not None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _json_string(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta trazable de chunks JSONL a ChromaDB.")
    parser.add_argument("--reset", action="store_true", help="Recrear la coleccion antes de ingestar.")
    args = parser.parse_args()
    asyncio.run(ingest(reset=args.reset))


if __name__ == "__main__":
    main()
