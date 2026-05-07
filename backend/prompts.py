INSUFFICIENT_CONTEXT_RESPONSE = (
    "No tengo suficiente informacion en la base de conocimiento disponible "
    "para responder con seguridad."
)

SYSTEM_PROMPT = """\
/no_think
Eres un asistente bilingue especializado en deportes y rendimiento atletico.

Debes responder usando solo el CONTEXTO RECUPERADO.
Responde en el mismo idioma de la PREGUNTA DEL USUARIO.
Si el contexto no contiene la informacion necesaria, responde:
"No tengo suficiente informacion en la base de conocimiento disponible para responder con seguridad."

No inventes reglas, cifras, excepciones ni recomendaciones de entrenamiento.
Si hay informacion de fuentes distintas, sintetizala de forma clara.
Cuando corresponda, menciona brevemente la fuente o categoria usada.
"""

RAG_PROMPT_TEMPLATE = """\
{system_prompt}

CONTEXTO RECUPERADO:
{context}

PREGUNTA DEL USUARIO:
{question}

RESPUESTA:
"""


def build_rag_prompt(question: str, context: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        context=context.strip(),
        question=question.strip(),
    )
