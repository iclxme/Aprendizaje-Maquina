import re
from typing import Any

import httpx

from backend.config import Settings

THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate(self, prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self.settings.ollama_chat_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            },
        }

        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=120) as client:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()

        content = response.json().get("response", "")
        return clean_model_response(content)

    async def embed(self, text: str) -> list[float]:
        payload = {
            "model": self.settings.ollama_embedding_model,
            "prompt": text,
        }

        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=120) as client:
            response = await client.post("/api/embeddings", json=payload)
            response.raise_for_status()

        embedding = response.json().get("embedding")
        if not isinstance(embedding, list):
            raise ValueError("Ollama no devolvio un embedding valido.")
        return embedding


def clean_model_response(response: str) -> str:
    return THINK_BLOCK_PATTERN.sub("", response).strip()
