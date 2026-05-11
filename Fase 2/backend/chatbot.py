from dataclasses import dataclass

from backend.ollama_client import OllamaClient
from backend.prompts import INSUFFICIENT_CONTEXT_RESPONSE, build_rag_prompt
from backend.rag import RetrievedSource, Retriever


@dataclass(frozen=True)
class ChatbotAnswer:
    answer: str
    sources: list[RetrievedSource]


class SportsChatbot:
    def __init__(self, retriever: Retriever, ollama_client: OllamaClient) -> None:
        self.retriever = retriever
        self.ollama_client = ollama_client

    async def answer(self, question: str) -> ChatbotAnswer:
        retrieved = await self.retriever.search(question)
        if not retrieved.has_context:
            return ChatbotAnswer(answer=INSUFFICIENT_CONTEXT_RESPONSE, sources=[])

        prompt = build_rag_prompt(question=question, context=retrieved.text)
        answer = await self.ollama_client.generate(prompt)
        return ChatbotAnswer(answer=answer, sources=retrieved.sources)
