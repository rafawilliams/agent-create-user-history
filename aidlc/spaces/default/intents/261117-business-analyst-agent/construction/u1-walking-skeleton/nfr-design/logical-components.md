# Logical Components — u1-walking-skeleton

Documentos de entrada: `performance-requirements.md`, `security-requirements.md`, `scalability-requirements.md`, `reliability-requirements.md`, `observability-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md` y `contract-summary.md`. Respuestas: `nfr-design-questions.md` (ND Qn).

Este documento da la vista por componentes de dónde se aplican los patrones de diseño no funcional, como puente hacia Infrastructure Design.

## Inventario lógico

| Componente lógico | Qué es | Patrones que se aplican | Dominio de falla |
|-------------------|--------|------------------------|------------------|
| Pantalla mínima (WebApp, mínima) | Una pantalla estática que envía el título y muestra el resultado | Muestra el mensaje de error del servicio como texto | La propia pantalla; no afecta al servicio |
| Pasarela HTTP | La entrada del servicio por HTTPS | Límite de tasa global; rechazo con RATE_LIMITED; HTTPS obligatorio | Compartido por todas las solicitudes |
| Servicio de generación | Una función sin estado que agrupa StoryGenerator, AccessControl y ModelGateway | Plazo de 55 s; verificador de sesión que falla cerrado; lista cerrada de campos de registro; un reintento acotado; concurrencia máxima de 5 | Una solicitud por ejecución; un fallo no afecta a las demás |
| Acceso al modelo (en el servicio) | El cliente del modelo y su corte de 50 s | Corte de 50 s; reintento único ante fallo pasajero; reuso del cliente | Falla de forma independiente por solicitud |
| Modelo de IA (Amazon Bedrock) | Servicio externo | Permiso mínimo por rol; registro de invocaciones desactivado | Externo; su fallo se traduce a MODEL_FAILURE o GENERATION_TIMEOUT |
| Monitoreo (AWS) | Receptor de métricas y registros | Solo errores y métricas, sin contenido | Si falla, el servicio sigue respondiendo |

## Radio de impacto

- Un fallo del modelo afecta solo a las solicitudes en curso y se informa como error con `retryable`.
- Un fallo de la pasarela HTTP afecta a todas las solicitudes (es el punto de entrada compartido).
- El servicio no tiene estado, así que ningún fallo deja datos corruptos.

## Recursos compartidos

- La cuenta de AWS y la región us-east-1 son compartidas por la pantalla, la pasarela, el servicio y el modelo.
- El permiso del rol de ejecución es el único recurso con acceso al modelo; su alcance se limita a invocar el modelo configurado.

## Puente con Infrastructure Design

Infrastructure Design debe dar forma a: la pasarela con su límite de tasa; el servicio con tope de concurrencia de 5 y sin el verificador simulado; el rol con permiso mínimo al modelo; el registro de invocaciones del modelo desactivado; las métricas y los registros sin contenido; y el alojamiento de la pantalla mínima.

## Alcance frente a los requisitos

- NFR4.5 (códigos de error en las métricas) se cubre en `observability-design.md`.
- NFR8.1 a NFR8.4 (TDD, cobertura de 80 %, linters, identificadores en inglés) no son patrones de diseño: los verifica Code Generation (pruebas primero) y Build and Test (umbral de cobertura en CI).
- Desviación registrada: NFR3.2 queda diferido a `u4-access-control` (ver `scalability-design.md`).

## Assumptions & Open Questions

- Abierto: cómo se aloja la pantalla mínima (decisión de `u6-infrastructure`).
- Abierto: los límites reales de los servicios de AWS que respaldan cada componente.
