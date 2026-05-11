import asyncio

from backend.chatbot import SportsChatbot
from backend.config import get_settings
from backend.ollama_client import OllamaClient
from backend.rag import Retriever

EXIT_COMMANDS = {"exit", "quit", "salir"}


async def run_chat() -> None:
    settings = get_settings()
    ollama_client = OllamaClient(settings)
    retriever = Retriever(settings, ollama_client)
    chatbot = SportsChatbot(retriever=retriever, ollama_client=ollama_client)

    print("Chatbot Deportes v1")
    print("Escribe una pregunta o usa 'salir' para terminar.\n")

    try:
        while True:
            question = input("Tu: ").strip()
            if not question:
                continue

            if question.lower() in EXIT_COMMANDS:
                break

            try:
                response = await chatbot.answer(question)
            except Exception as exc:
                print(f"Error: {exc}\n")
                continue

            print(f"\nAsistente: {response.answer}")
            if response.sources:
                sources = ", ".join(
                    f"{source.chunk_id or source.category} [{', '.join(source.source_ids)}]"
                    for source in response.sources
                )
                print(f"Fuentes: {sources}")
            print()
    except KeyboardInterrupt:
        print("\nChat finalizado.")


def main() -> None:
    asyncio.run(run_chat())


if __name__ == "__main__":
    main()
