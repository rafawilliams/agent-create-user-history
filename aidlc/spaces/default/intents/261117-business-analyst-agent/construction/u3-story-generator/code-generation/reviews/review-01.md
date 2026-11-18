## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-17T17:22:17Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | backend/story_service/evaluation.py > REQUIRED_PREFIX y check_format (líneas 30 y 56-70); backend/story_service/evaluate_models.py > uso de settings.instructions | u3 cambió en su sitio las instrucciones por defecto para que el modelo devuelva JSON, pero el comando de evaluación de u2 sigue exigiendo que el texto empiece con "Como analista de negocio" y contar bloques "Escenario". Con una respuesta real en JSON, format_ok sale falso siempre y ambos modelos puntúan cero, así que la comparación Titan frente a Sonnet (US7.1) da un resultado inútil. Las pruebas de u2 siguen en verde solo porque alimentan texto con el prefijo antiguo, de modo que la suite no detecta la regresión. La brecha está registrada con honestidad en code-summary.md (Desviaciones, punto 1), pero u3 la deja como regresión conocida en un comando que modificó indirectamente. | Hacer que check_format de evaluación reutilice parse_story_draft y build_markdown de u3 (o aceptar ambos formatos), y añadir una prueba con una respuesta JSON real del modelo simulado. Si se difiere, registrarlo como bloqueo explícito de la evaluación real, no solo como nota. | New |
| R-02 | Minor | backend/story_service/response_parsing.py > _SPANISH_WORDS y _looks_spanish | La heurística rechaza español válido y corto. Verificado con el código: acción "exportar reportes en PDF" con beneficio "compartirlos rápido", acción "iniciar sesión" con beneficio "acceder rápido", y acción "ver el historial" con beneficio "consultar pagos antiguos" dan INVALID_MODEL_RESPONSE. Faltan palabras muy comunes como "a", "es", "me", "le". El servicio no reintenta una respuesta inválida, así que la persona debe reintentar a mano. code-summary.md lo menciona, pero sin cifra. | Ampliar la lista de palabras comunes o contar solo si hay una señal clara de otro idioma, y añadir pruebas de falsos rechazos con estas frases. | New |
| R-03 | Minor | backend/story_service/response_parsing.py > _FENCE y parse_story_draft (codificación UTF-8) | Un cerco con saltos CRLF ("```jsonrn...rn```") se rechaza aunque sea un único cerco válido. Una cadena con un sustituto suelto (p. ej. "ud800", que json.loads del cuerpo de Bedrock puede producir) hace que text.encode lance UnicodeEncodeError; cae en el manejador interno y devuelve MODEL_FAILURE no reintentable con internal_error, en lugar de INVALID_MODEL_RESPONSE reintentable. | Aceptar r?n en el cerco y medir los bytes con errors="replace" (o capturar UnicodeEncodeError como respuesta inválida); añadir pruebas de ambos casos. | New |
| R-04 | Minor | backend/tests/test_prompt.py > test_nested_marks_cannot_rebuild_a_closing_mark; backend/tests/test_models_errors.py > test_story_request_normalizes_control_characters_and_unicode_spaces_in_the_title | La neutralización se prueba solo con espacios ASCII y la normalización solo con x00 y el espacio ideográfico; no hay prueba de U+2028, U+0085, U+00A0 dentro de una marca ni de que el contexto pase por la misma normalización antes del prompt. Se comprobó a mano que hoy funcionan, pero nada las protege. Una marca partida con un carácter de ancho cero ("<​titulo>") pasa tal cual al prompt; es poco explotable, pero no está documentada. | Añadir esos casos a las pruebas y anotar en prompt.py que los caracteres de formato (Cf) no se tratan. | New |
| R-05 | Minor | backend/tests/test_story_generation.py > test_own_work_median_is_under_50_ms_and_max_over_200_ms_only_warns | La prueba de tiempos mide generate completo (sesión, registro y métricas incluidos) con un modelo simulado instantáneo, no el trabajo propio de u3 que NFR1.5 acota; el método (mediana de 20 tras calentamiento, hasta 3 intentos, máximo solo avisa) sí coincide con el plan. Aporta poca señal. | Medir validación, armado del prompt, interpretación y armado del Markdown por separado, o renombrar la prueba para reflejar lo que mide. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| python -m pytest tests -q (backend) | 356 passed | Coincide con code-summary.md. |
| python -m pytest tests -q --cov=story_service --cov-fail-under=80 | 356 passed, cobertura 99,65 %, piso de 80 % alcanzado | fail_under = 80 sigue intacto en pyproject.toml; el piso no se debilitó. |
| Comando de la unidad (7 archivos de prueba) | 185 passed | Coincide con code-summary.md. |
| Sondeos de solo lectura con las funciones de u3 (sin AWS) | BR3.1 a BR3.3 (200/201, 500/501, "Login" pide contexto, "Recuperar contraseña" genera, contexto vacío ausente), neutralización repetida con variantes de mayúsculas y espacios, escape fuera del bloque, cerco más largo que cualquier racha de acentos graves, plazo agotado sin llamar al modelo: correctos. docs/titulos-prueba-nfr2.md: el título 7 mide 200 caracteres. | Sin defectos en las reglas BR3.1 a BR3.10 más allá de los hallazgos; traceability.json marca AC3.1.2 como Deferred con honestidad y code-summary.md declara lo que no se ejecutó. |

### Summary

La implementación de BR3.1 a BR3.10 es sólida y está bien probada; no encontré Critical. El único Major es la brecha ya conocida de u2: la evaluación sigue comprobando el prefijo antiguo y puntuaría cero a todo modelo real. Con un Major y el resto Minor, el veredicto es READY.
