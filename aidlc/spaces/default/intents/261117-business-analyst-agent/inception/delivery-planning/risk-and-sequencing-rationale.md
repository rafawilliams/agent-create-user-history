# Risk and Sequencing Rationale — Business Analyst Agent

Documentos de entrada: `requirements.md`, `unit-of-work.md`, `unit-of-work-dependency.md`, `contract-summary.md` y `team-practices.md`. Secuencia: `bolt-plan.md`. Respuestas: `delivery-planning-questions.md` (DP Qn).

Una **Bolt** es una pasada de construcción sobre una parte del trabajo (una o más unidades) que termina en algo que corre. El **esqueleto ambulante** es la versión mínima que corre de principio a fin, construida primero para probar que las piezas se conectan. **WSJF** (Weighted Shortest Job First, de Reinertsen y SAFe) es una puntuación que suma el valor para el usuario, la urgencia y la reducción de riesgo, y lo divide por el tamaño del trabajo: sale primero lo que más puntúa.

## Heurísticas elegidas

1. **Esqueleto ambulante primero** (Cockburn): B1 es la primera Bolt (Practices Discovery y DP Q2). Prueba que las piezas se conectan antes de construir las funciones reales.
2. **Infraestructura temprano:** B2 va justo después, para desplegar pronto y descubrir cuanto antes si el límite de tiempo del servicio permite los 60 segundos (DP Q2).
3. **Riesgo después:** el modelo (B3), la generación (B4), la interfaz (B5) y el control de acceso (B6) siguen en ese orden.
4. **WSJF como justificación, no como regla:** se puntúa cada Bolt, pero el orden lo fija DP Q2; si el puntaje propone otro orden, manda DP Q2 (DP Q8).

## Puntuación WSJF (pesos iguales; DP Q3, Q9)

Los valores son estimaciones del análisis (hipótesis), en una escala de 1 a 10, no datos medidos. La puntuación es (valor + urgencia + reducción de riesgo) ÷ tamaño.

| Bolt | Unidad | Valor | Urgencia | Reducción de riesgo | Tamaño | Puntaje |
|------|--------|-------|----------|---------------------|--------|---------|
| B1 | U1 | 8 | 9 | 9 | 5 | 5,2 |
| B2 | U6 | 5 | 7 | 7 | 5 | 3,8 |
| B3 | U2 | 7 | 8 | 9 | 3 | 8,0 |
| B4 | U3 | 9 | 8 | 6 | 5 | 4,6 |
| B5 | U5 | 8 | 7 | 4 | 5 | 3,8 |
| B6 | U4 | 6 | 5 | 5 | 5 | 3,2 |

El tamaño sale de la complejidad de `unit-of-work.md` (U2 es S y las demás M; U1 se considera M).

## Desviación del puntaje y razón

El puntaje WSJF pondría U2 (8,0) antes que U1 y U6, y U3 (4,6) antes que U6. U1 no puede ir después por ser el esqueleto ambulante, que es la primera unidad en el orden de dependencias. Respecto de U6, la persona decidió que la infraestructura vaya antes que el modelo y la generación (DP Q2) y que en caso de diferencia mande ese orden (DP Q8). Es una desviación consciente del puntaje, no una desviación del orden topológico: el mapa de dependencias permite cualquier orden después de U1.

## Riesgos de la secuencia

| Riesgo | Probabilidad | Impacto | Mitigación | Fuente |
|--------|--------------|---------|------------|--------|
| El modelo no alcanza la calidad de Gherkin pedida (80 % válido a la primera) | Media | Alto | La evaluación de Titan frente a Claude Sonnet queda en B3; el esqueleto ya usa el modelo real | DP Q7; `requirements.md` (NFR2) |
| No se llega a la demostración en dos semanas | Media | Alto | Revisar el plan al terminar B1 y recortar B6 o B5 si hace falta | DP Q7; SD Q11 |
| El límite de tiempo del servicio HTTP no permite 60 segundos | Media | Alto | Confirmarlo en B2, con la infraestructura | `contract-summary.md` (revisión R-06) |
| Dejar el control de acceso al final deja las demos intermedias sin inicio de sesión real | Alta | Medio | Usar el verificador de sesión simulado de U1 hasta B6; no publicar a otras personas antes de B6 | `contract-summary.md` (ADR-006) |
| Construir una unidad tras otra no cabe en el plazo | Media | Medio | Revisar el plan tras B1; la persona puede cambiar a ejecución en paralelo | DP Q4 |

Las valoraciones de probabilidad e impacto son del análisis (hipótesis).

## Assumptions & Open Questions

- Supuesto: los valores de WSJF son estimaciones del análisis; la persona puede ajustarlos y recalcular sin cambiar el orden (DP Q8).
- Abierto: cuántos títulos de ejemplo y quién califica el Gherkin a mano para decidir sobre el modelo (NFR2).
