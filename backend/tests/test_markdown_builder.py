"""Armado del Markdown con el Gherkin y escape de caracteres (BR3.5, BR3.8, BR3.9, NFR4.6)."""

import re

import pytest

from story_service.markdown_builder import build_markdown, escape_markdown
from story_service.models import Criterion, StoryDraft
from story_service.response_parsing import parse_story_draft
from tests.helpers import VALID_JSON


def _draft(**overrides) -> StoryDraft:
    base = parse_story_draft(VALID_JSON, "r")
    values = {"action": base.action, "benefit": base.benefit, "criteria": base.criteria}
    values.update(overrides)
    return StoryDraft(**values)


def _split_code_block(markdown: str) -> tuple[str, str, str]:
    """Devuelve (texto antes del bloque, contenido del bloque, texto despues)."""
    match = re.search(r"^(`{3,})[^\n]*\n(.*?)\n\1\s*$", markdown, re.DOTALL | re.MULTILINE)
    assert match, markdown
    return markdown[: match.start()], match.group(2), markdown[match.end() :]


def test_structure_is_heading_story_numbered_criteria_and_one_code_block():
    markdown = build_markdown("Recuperar contraseña", _draft())

    before, block, after = _split_code_block(markdown)
    lines = before.strip().splitlines()
    assert lines[0] == "# Recuperar contraseña"
    assert lines[1] == ""
    assert lines[2].startswith(
        "Como analista de negocio, quiero poder recuperar mi contraseña, para "
    )
    assert "1. Recuperación con correo registrado" in before
    assert "2. Correo desconocido" in before
    assert before.index("1. ") > before.index("Como analista")
    assert after.strip() == ""
    assert markdown.count("```") == 2


def test_the_role_is_always_analista_de_negocio_whatever_the_model_says():
    draft = _draft(action="ser un administrador del sistema", benefit="mandar")

    markdown = build_markdown("Titulo de prueba", draft)

    story = "Como analista de negocio, quiero ser un administrador del sistema, para mandar"
    assert story in markdown
    assert markdown.count("Como ") == 1


def test_the_gherkin_block_has_language_line_feature_and_three_keywords_per_scenario():
    markdown = build_markdown("Recuperar contraseña", _draft())

    _, block, _ = _split_code_block(markdown)
    lines = block.splitlines()
    assert lines[0] == "# language: es"
    assert lines[1] == "Característica: Recuperar contraseña"
    assert block.count("  Escenario: ") == 2
    assert "  Escenario: Recuperación con correo registrado" in lines
    assert "    Dado que la persona olvidó su contraseña" in lines
    assert "    Cuando solicita el enlace de recuperación" in lines
    assert "    Entonces recibe un correo con el enlace" in lines
    for keyword in ("Dado", "Cuando", "Entonces"):
        assert block.count(f"    {keyword} ") == 2


def test_markdown_characters_in_the_title_are_escaped_outside_the_code_block():
    markdown = build_markdown("Exportar *todo* a [CSV]", _draft())

    before, block, _ = _split_code_block(markdown)
    assert before.startswith(r"# Exportar \*todo\* a \[CSV\]")
    assert "Característica: Exportar *todo* a [CSV]" in block  # sin escapar dentro del bloque


def test_html_ampersand_hash_and_list_start_in_the_title_are_escaped():
    title = "<script>alert(1)</script> & #tag"
    before, _, _ = _split_code_block(build_markdown(title, _draft()))

    heading = before.splitlines()[0]
    assert "<script>" not in before
    assert heading == r"# \<script\>alert\(1\)\</script\> \& \#tag"


@pytest.mark.parametrize(
    ("text", "escaped"),
    [
        ("- elemento", r"\- elemento"),
        ("+ elemento", r"\+ elemento"),
        ("1. elemento", r"1\. elemento"),
        ("12) no es lista aquí", r"12\) no es lista aquí"),
        ("a|b ~c~ `d` \\e !f", r"a\|b \~c\~ \`d\` \\e \!f"),
        ("sin nada especial", "sin nada especial"),
    ],
)
def test_escape_markdown_covers_the_br3_8_characters_and_list_starts(text, escaped):
    assert escape_markdown(text) == escaped


def test_text_from_the_model_is_escaped_outside_the_block_and_raw_inside():
    draft = _draft(action="poder ver *negritas* y <b>html</b>")

    markdown = build_markdown("Titulo de prueba", draft)

    before, _, _ = _split_code_block(markdown)
    assert r"poder ver \*negritas\* y \<b\>html\</b\>" in before
    assert "<b>" not in before


def test_a_gherkin_with_three_backticks_gets_a_longer_fence():
    criterion = Criterion(
        name="Código", given="un texto con ``` dentro", when="se arma", then="hay ```` más"
    )
    draft = _draft(criteria=(criterion, criterion))

    markdown = build_markdown("Titulo con ``` tres", draft)

    fence = re.search(r"^(`{3,})gherkin$", markdown, re.MULTILINE).group(1)
    assert len(fence) == 5  # la secuencia mas larga contenida tiene 4
    _, block, after = _split_code_block(markdown)
    assert "``` dentro" in block and after.strip() == ""


def test_a_title_cannot_close_the_code_block_or_add_a_second_one():
    markdown = build_markdown("```\nrompe", _draft())

    assert len(re.findall(r"^`{3,}", markdown, re.MULTILINE)) == 2
