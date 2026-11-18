# CI/CD Pipeline — u3-story-generator

Documentos de entrada: `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`, `logical-components.md`, `components.md`, `functional-spec.md` y `contract-summary.md`. No hubo preguntas en esta etapa: u3 reutiliza el flujo de GitHub Actions de u1, con un solo entorno y despliegue al integrar en `main`.

## Infraestructura propia de u3

Ninguna (ver `infrastructure-specification.md`). u3 se despliega con la función de generación y se retrocede con ella.

## Qué agrega u3 al flujo de CI

| Etapa del flujo | Qué agrega u3 | Puerta (si falla) |
|-----------------|---------------|-------------------|
| 1. Estilo y tipos | Black y Ruff sobre el código de u3 (NFR8.3, NFR8.4) | Bloquea la integración |
| 2. Pruebas y cobertura | Las pruebas de u3 corren con TDD (NFR8.1) y el piso de 80 % se mide en la suite completa; la cobertura de los archivos de u3 se informa aparte (NFR8.2). Incluyen: validación del título y del contexto con límites en 200/201 y 500/501 (NFR4.4), petición de contexto sin llamar al modelo (NFR1.3), inyección y delimitadores (NFR4.3), respuesta del modelo inválida por cada etapa y de más de 16 KB (NFR1.6, NFR4.5), escape y cerco de código (NFR4.6), registros sin contenido (NFR4.2), 5 solicitudes en paralelo (NFR3.1), tiempos de 50 ms: bloquea la mediana de 20 repeticiones mayor que 50 ms, repetida hasta 3 veces antes de fallar (los ejecutores compartidos varían), y el máximo de 200 ms solo emite un aviso y no bloquea (NFR1.2, NFR1.5), error interno sin traza (NFR1.8) y plazo agotado antes de llamar (NFR1.7) | Bloquea la integración |
| 4. Verificaciones de seguridad del diseño | La búsqueda de patrones de claves de AWS que posee `u6-infrastructure` | Bloquea la integración |
| 5 y 6. Despliegue y prueba de humo | Sin cambios de u3; la prueba de humo de u1 devuelve SESSION_INVALID hasta que exista el verificador real | No aplica a u3 |

El comando de punta a punta contra el modelo real de u1 no corre en CI; se ejecuta a mano y también ejercita la generación de u3 cuando esté integrada.

## Revisión manual de NFR2 y de Jira

La revisión manual de los títulos de prueba (80 % de Gherkin válido) y la comprobación de pegado en el editor de Jira son manuales y no corren en CI; sus resultados se registran en `docs/` y los revisa la persona (ver `tech-stack-decisions.md` de u3).

## Retroceso

u3 no tiene despliegue propio: se retrocede con la función de generación (volver a aplicar la revisión anterior con Terraform, ver `cicd-pipeline.md` de u1). No hay datos que revertir (NFR4.1). El cambio coordinado de las listas cerradas de u1 se revierte con Git junto con el resto.

## Secretos y credenciales

Sin secretos: u3 no usa credenciales ni habla con AWS (NFR5.1). Las instrucciones son texto de configuración sin credenciales (NFR5.2).

## Assumptions & Open Questions

- Supuesto: el flujo de u1 ejecuta la suite completa en la etapa 2, así que las pruebas de u3 entran sin cambios en el flujo.
- Abierto: dónde se guarda el registro de la revisión manual de NFR2 (se propone `docs/`).
