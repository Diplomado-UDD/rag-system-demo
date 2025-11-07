"""LLM prompt templates in Spanish for RAG system."""

# System prompt for the RAG assistant
SYSTEM_PROMPT_TEMPLATE = """Eres un asistente útil que responde preguntas basándose EXCLUSIVAMENTE en el contexto proporcionado de un documento PDF.

REGLAS ESTRICTAS:
1. Si la respuesta NO está en el contexto, debes responder: "Lo siento, esa información no se encuentra en el documento. ¿Podrías reformular tu pregunta o hacer otra relacionada con el contenido?"
2. SIEMPRE debes incluir las páginas de referencia en tu respuesta usando el formato: [Página X]
3. Responde en español claro y natural, adaptado al español chileno cuando sea apropiado
4. NO inventes información que no esté en el contexto
5. Si el contexto es insuficiente o ambiguo, pide más detalles al usuario

CONTEXTO DEL DOCUMENTO:
{context}

Responde la siguiente pregunta basándote ÚNICAMENTE en el contexto anterior."""


def format_prompt(context: str, question: str) -> str:
    """
    Format the prompt with context and question.

    Args:
        context: Retrieved chunks of text from the document
        question: User's question in Spanish

    Returns:
        Formatted prompt ready for LLM
    """
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
    full_prompt = f"{system_prompt}\n\nPREGUNTA: {question}\n\nRESPUESTA:"
    return full_prompt


def format_context_from_chunks(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into context string.

    Args:
        chunks: List of chunk dictionaries with 'content' and 'page_number'

    Returns:
        Formatted context string with page references
    """
    if not chunks:
        return "No se encontró información relevante en el documento."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        page_num = chunk.get("page_number", "?")
        content = chunk.get("content", "")
        context_parts.append(f"[Fragmento {i} - Página {page_num}]\n{content}")

    return "\n\n".join(context_parts)


# Out-of-scope refusal message
REFUSAL_MESSAGE = (
    "Lo siento, esa información no se encuentra en el documento. "
    "¿Podrías reformular tu pregunta o hacer otra relacionada con el contenido?"
)
