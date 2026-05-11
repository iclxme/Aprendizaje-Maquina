from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.chatbot import SportsChatbot
from backend.config import get_settings
from backend.ollama_client import OllamaClient
from backend.rag import Retriever

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(title="Chatbot Deportes", version="0.1.0")

settings = get_settings()
ollama_client = OllamaClient(settings)
retriever = Retriever(settings, ollama_client)
chatbot = SportsChatbot(retriever=retriever, ollama_client=ollama_client)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class SourceResponse(BaseModel):
    chunk_id: str
    area: str
    document: str
    category: str
    source_ids: list[str]
    questions: list[str]
    canonical_url: str = ""
    source_section: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


@app.get("/")
async def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        chatbot_answer = await chatbot.answer(request.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    sources = [
        SourceResponse(
            chunk_id=source.chunk_id,
            area=source.area,
            document=source.document,
            category=source.category,
            source_ids=list(source.source_ids),
            questions=list(source.questions),
            canonical_url=source.canonical_url,
            source_section=source.source_section,
        )
        for source in chatbot_answer.sources
    ]
    return ChatResponse(answer=chatbot_answer.answer, sources=sources)


def run() -> None:
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
