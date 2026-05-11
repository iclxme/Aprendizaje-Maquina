# Chatbot Deportes

## Ejecutar

```bash
poetry install
cp .env.example .env
poetry run python -m scripts.ingest --reset
poetry run uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Abrir:

```text
http://127.0.0.1:8000/
```

Ollama debe estar corriendo con los modelos definidos en `.env`.

VIDEO DE CHATBOT (ANÁLISIS DE DESEMPEÑO): https://youtu.be/JAtAZ0n1Ug8