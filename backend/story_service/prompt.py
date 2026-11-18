"""Armado de la peticion al modelo (BR1.6, BR3.4, NFR4.3, NFR4.4, ADR-003)."""

import re

TITLE_OPEN = "<titulo>"
TITLE_CLOSE = "</titulo>"
CONTEXT_OPEN = "<contexto>"
CONTEXT_CLOSE = "</contexto>"

# Texto visible que reemplaza una marca dentro del contenido. No contiene "<", el caracter con
# que empiezan las marcas, asi que un reemplazo no puede reconstruir otra marca anidada.
_NEUTRALIZED = "[marca eliminada]"
_MARK = re.compile(r"<\s*/?\s*(?:titulo|contexto)\s*>", re.IGNORECASE)


def neutralize_marks(content: str) -> str:
    """Reemplaza las marcas de la peticion (cualquier mayúscula y espacios) hasta que no quede."""
    previous = None
    while previous != content:
        previous = content
        content = _MARK.sub(_NEUTRALIZED, content)
    return content


def build_prompt(instructions: str, title: str, context: str | None = None) -> str:
    """Las instrucciones van aparte; titulo y contexto van dentro de marcas fijas, como dato.

    `title` y `context` ya vienen normalizados (una sola linea); aqui se neutralizan las marcas.
    """
    parts = [instructions, f"{TITLE_OPEN}\n{neutralize_marks(title)}\n{TITLE_CLOSE}"]
    if context:
        parts.append(f"{CONTEXT_OPEN}\n{neutralize_marks(context)}\n{CONTEXT_CLOSE}")
    return "\n\n".join(parts)
