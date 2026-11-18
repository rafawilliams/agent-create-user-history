# Delivery Planning — Preguntas

Plan: decidir en qué orden se construyen las 6 unidades de `unit-of-work.md`. Una Bolt es una pasada de construcción sobre una parte del trabajo, que termina en algo que corre. El mapa de dependencias de Units Generation dice qué puede depender de qué; aquí se elige el camino por ese mapa. Ya está decidido que la primera Bolt es el corte delgado de punta a punta (esqueleto ambulante, una versión mínima que corre de principio a fin; Practices Discovery) y que la secuencia es riesgo primero (Scope Definition).

## Q1. [Entrega] ¿Qué tan grande es cada Bolt?

Contexto: hay 6 unidades. Una Bolt por unidad da pasos muy pequeños y mucha ceremonia en un plazo de dos semanas; agrupar unidades relacionadas reduce los pasos, pero mezcla más trabajo por entrega.

- A. Una Bolt por unidad (6 Bolts)
- B. Unidades relacionadas juntas: la Bolt 1 es el corte delgado (u1); la Bolt 2 reúne el acceso al modelo y la generación (u2 y u3); la Bolt 3 reúne el control de acceso y la interfaz (u4 y u5); la Bolt 4 es la infraestructura (u6)
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Entrega] Después del corte delgado, ¿en qué orden se construye lo demás?

Contexto: sigue la secuencia de riesgo primero. El mayor riesgo técnico es el modelo de IA (Amazon Titan frente a Claude Sonnet, y que esté habilitado en la cuenta); el mayor riesgo de plazo es la infraestructura.

- A. Riesgo primero: modelo (u2), generación (u3), interfaz (u5), control de acceso (u4) e infraestructura (u6)
- B. Valor primero: generación (u3), interfaz (u5), modelo (u2), control de acceso (u4) e infraestructura (u6)
- C. Infraestructura temprano, para desplegar pronto: infraestructura (u6) justo después del corte delgado, y luego el modelo, la generación, la interfaz y el control de acceso
- D. Not yet defined
- X. Other (please specify)

[Answer]: C

## Q3. [Entrega] ¿Se puntúan y ordenan las Bolts con un modelo formal?

Contexto: WSJF es una puntuación de valor y urgencia frente al tamaño del trabajo; sirve cuando hay muchas opciones comparables. Con 4 a 6 Bolts y un orden ya guiado por el riesgo, puede ser más peso del necesario.

- A. No, el orden lo guía el riesgo y las dependencias (recomendado)
- B. Sí, con una puntuación WSJF por Bolt
- C. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q4. [Entrega] ¿Se construyen varias Bolts a la vez o una tras otra?

Contexto: en Units Generation permitiste el paralelismo entre unidades independientes. La revisión de ese plan señaló que U2, U3, U4 y U5 comparten archivos y contratos que fija U1, así que construirlas a la vez puede producir conflictos de integración. Una a una es el modo por defecto.

- A. Una tras otra (recomendado)
- B. Varias a la vez cuando no dependan entre sí
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q5. [Entrega] ¿En qué estado está el acceso al modelo en Amazon Bedrock?

Contexto: en Feasibility indicaste que la cuenta existe pero el modelo no está habilitado. Esa dependencia externa bloquea el corte delgado y la evaluación de modelos.

- A. Ya está habilitado
- B. Ya se solicitó y está en trámite (indica el plazo en Other)
- C. Aún no se solicitó
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q6. [Entrega] ¿Quién registra la aplicación en Google y en Microsoft para el inicio de sesión, y cuánto tarda?

Contexto: iniciar sesión con Gmail u Outlook exige registrar la aplicación en los dos proveedores de identidad. Es una dependencia externa que bloquea el control de acceso (u4) y la prueba completa de la interfaz.

- A. Yo lo gestiono y puede estar listo en pocos días
- B. Lo gestiona otro equipo o persona (indica quién y el plazo en Other)
- C. Todavía no sé quién lo hace ni cuánto tarda
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q7. [Entrega] ¿Qué te preocupa más de esta construcción, para atacarlo pronto? (select all that apply)

Contexto: lo elegido guía qué se prueba primero.

- A. La calidad del Gherkin que genera cada modelo
- B. Llegar a la demostración en dos semanas con una tecnología nueva para el equipo
- C. El costo y el acceso abierto con cuentas de Gmail u Outlook
- D. Not yet defined
- X. Other (please specify)

[Answer]: A, B

## Q8. [Entrega] Si el puntaje WSJF sale distinto del orden que elegiste en Q2, ¿qué manda?

Contexto: en Q2 elegiste infraestructura temprano (u1, u6, u2, u3, u5, u4) y en Q3 pediste puntuar con WSJF. Si los puntajes proponen otro orden, hay que decidir cuál se sigue.

- A. Manda el orden de Q2; el WSJF se documenta como justificación y como señal de riesgos
- B. Manda el WSJF, con el único límite del mapa de dependencias
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q9. [Entrega] ¿Qué peso lleva cada factor del WSJF?

Contexto: el puntaje WSJF suma valor para el usuario, urgencia y reducción de riesgo, y lo divide por el tamaño del trabajo. Los pesos cambian qué Bolt sale primero.

- A. Pesos iguales para valor, urgencia y reducción de riesgo
- B. Más peso a la reducción de riesgo
- C. Más peso al valor para el usuario
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
