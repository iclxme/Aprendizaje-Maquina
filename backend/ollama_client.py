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
            response = await _post_ollama(client, "/api/generate", payload, self.settings.ollama_base_url)

        content = response.json().get("response", "")
        return clean_model_response(content)

    async def embed(self, text: str) -> list[float]:
        payload = {
            "model": self.settings.ollama_embedding_model,
            "prompt": text,
        }

        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=120) as client:
            response = await _post_ollama(
                client,
                "/api/embeddings",
                payload,
                self.settings.ollama_base_url,
            )

        embedding = response.json().get("embedding")
        if not isinstance(embedding, list):
            raise ValueError("Ollama no devolvio un embedding valido.")
        return embedding


def clean_model_response(response: str) -> str:
    return THINK_BLOCK_PATTERN.sub("", response).strip()


async def _post_ollama(
    client: httpx.AsyncClient,
    path: str,
    payload: dict[str, Any],
    base_url: str,
) -> httpx.Response:
    try:
        response = await client.post(path, json=payload)
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"No se pudo conectar con Ollama en {base_url}. "
            "Verifica que Ollama este corriendo y que los modelos esten descargados."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Ollama respondio con error {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Ollama no respondio correctamente: {exc}") from exc
    return response
