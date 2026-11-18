"""Armado del Markdown final con el Gherkin y escape de caracteres (BR3.5, BR3.8, BR3.9).

El rol, las palabras clave del Gherkin, la linea de idioma y la estructura las fija el servicio;
el modelo solo aporta la accion, el beneficio y las partes de cada criterio.
"""

from __future__ import annotations

import re

from story_service.models import StoryDraft, normalize_line

ROLE = "analista de negocio"
STORY_PREFIX = f"Como {ROLE}"
GHERKIN_LANGUAGE_LINE = "# language: es"

# Caracteres con significado en Markdown o HTML (BR3.8).
_SPECIAL = re.compile(r"([\\*_\[\]()#`><&|~!])")
# Un numero seguido de punto al comienzo de la linea se leeria como lista numerada.
_NUMBERED_START = re.compile(r"^(\d+)\.")
_BACKTICK_RUN = re.compile(r"`+")


def escape_markdown(text: str) -> str:
    """Escapa una sola linea para usarla fuera del bloque de codigo."""
    escaped = _SPECIAL.sub(r"\\\1", text)
    if escaped.startswith(("-", "+")):
        return "\\" + escaped
    numbered = _NUMBERED_START.match(escaped)  # "12)" ya queda escapado por el parentesis
    if numbered:
        return f"{numbered.group(1)}\\.{escaped[numbered.end() :]}"
    return escaped


def _fence_for(content: str) -> str:
    """Cerco con mas acentos graves que la secuencia mas larga del contenido (minimo tres)."""
    longest = max((len(run) for run in _BACKTICK_RUN.findall(content)), default=0)
    return "`" * max(3, longest + 1)


def build_markdown(title: str, draft: StoryDraft) -> str:
    """Titulo, historia, lista numerada de criterios y un unico bloque con el Gherkin completo."""
    clean_title = normalize_line(title)
    story = (
        f"{STORY_PREFIX}, quiero {escape_markdown(draft.action)}, "
        f"para {escape_markdown(draft.benefit)}"
    )
    criteria_list = "\n".join(
        f"{number}. {escape_markdown(criterion.name)}"
        for number, criterion in enumerate(draft.criteria, start=1)
    )

    gherkin_lines = [GHERKIN_LANGUAGE_LINE, f"Característica: {clean_title}"]
    for criterion in draft.criteria:
        gherkin_lines += [
            "",
            f"  Escenario: {criterion.name}",
            f"    Dado {criterion.given}",
            f"    Cuando {criterion.when}",
            f"    Entonces {criterion.then}",
        ]
    gherkin = "\n".join(gherkin_lines)
    fence = _fence_for(gherkin)

    return (
        f"# {escape_markdown(clean_title)}\n\n"
        f"{story}\n\n"
        f"{criteria_list}\n\n"
        f"{fence}gherkin\n{gherkin}\n{fence}\n"
    )
