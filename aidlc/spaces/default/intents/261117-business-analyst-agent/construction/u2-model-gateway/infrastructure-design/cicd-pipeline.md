# CI/CD Pipeline — u2-model-gateway

Documentos de entrada: `security-design.md`, `logical-components.md`, `functional-spec.md`, `components.md` y `contract-summary.md`. No hubo preguntas en esta etapa: u2 es una biblioteca que no se despliega por separado, así que no agrega recursos de infraestructura propios y reutiliza el flujo de GitHub Actions y la infraestructura de `u1-walking-skeleton`, que `u6-infrastructure` completa. Este documento dice qué agrega u2 a esas etapas y qué entrega a u6.

## Infraestructura propia de u2

Ninguna. u2 es código dentro de la función de generación (`infrastructure-specification.md` de u1). No añade servicios, redes, almacenamiento ni monitoreo propios: las métricas y los registros los emite el servicio, y u2 solo aporta los cuatro campos de registro por llamada de `security-design.md`.

## Documentos de diseño que u2 no produce

Por ser una biblioteca, u2 no escribe `performance-design`, `scalability-design`, `reliability-design` ni `observability-design` como documentos aparte (ver `logical-components.md`): los tiempos de espera y el único intento por llamada están en `logical-components.md`, la capacidad concurrente la imponen el servicio y la infraestructura de u1 y u6, y los registros por llamada están en `security-design.md`. Tampoco produce `infrastructure-specification` ni `monitoring-design`: no tiene recursos ni métricas propios.

## Qué agrega u2 a las etapas del flujo de CI

| Etapa del flujo | Qué agrega u2 | Puerta (si falla) |
|-----------------|---------------|-------------------|
| 1. Estilo y tipos | Black y Ruff sobre el código nuevo de u2 (NFR8.3) | Bloquea la integración |
| 2. Pruebas y cobertura | Las pruebas de u2 corren en la suite del servicio, con TDD (NFR8.1) y el piso de 80 % medido sobre la suite completa; la cobertura de los archivos de u2 se informa aparte (NFR8.2). Incluyen: traducción de errores con un ARN en el texto de AWS y captura de todos los registros (NFR4.2), un solo intento y cero reintentos del cliente (NFR1.4), tiempo pedido con fracciones y tolerancia de 1 s (NFR1.1), identificadores no soportados o mal escritos sin llamada a AWS (NFR5.3), el comando de evaluación con modelos simulados (NFR1.3, NFR2.1) y su negativa a correr sin 5 títulos con huella válida (NFR4.3) | Bloquea la integración |
| 4. Verificaciones de seguridad del diseño | Búsqueda de patrones de claves de AWS en el código y en las pruebas, que ejecuta la etapa de seguridad de `cicd-pipeline.md` de u1 (NFR5.1) | Bloquea la integración |
| 5 y 6. Despliegue y prueba de humo | Sin cambios de u2; u6 agrega la verificación descrita abajo | No aplica a u2 |

El comando de evaluación contra Amazon Bedrock **no** corre en CI: llama a AWS con la cuenta de la persona. Se ejecuta a mano, como `local_run` en u1, y su resultado queda en `docs/evaluacion-modelos.md`.

## Qué entrega u2 a `u6-infrastructure`

| Entrega | Contenido | Quién lo verifica |
|---------|-----------|-------------------|
| Lista de modelos | El identificador del modelo por defecto (hoy Claude Sonnet 4.6) y, cuando se fije en Code Generation, el de Amazon Titan; los dos salen de la misma variable de Terraform que alimenta la configuración del servicio (NFR5.2) | `u6-infrastructure` |
| Forma del permiso | Permiso de invocar el perfil de inferencia (ARN de la cuenta) y el modelo base en cada región de destino; el comodín de región solo para ese modelo base, nunca un comodín sobre todos los modelos | `u6-infrastructure` (revisión de IAM) |
| Registro de invocaciones | Debe seguir desactivado en la cuenta (NFR4.2) | La prueba de humo de u6 consulta la configuración de registro de invocaciones |
| Identificador no válido | Un valor mal escrito hace fallar la inicialización y cada invocación; la prueba de humo de u6 debe detectarlo | La prueba de humo de u6 |
| Búsqueda de claves de AWS en CI | La etapa de seguridad de CI debe buscar patrones de claves de AWS en el código y en las pruebas (NFR5.1); dueño: la etapa de CI de `u6-infrastructure`, que la agrega al flujo de u1 | `u6-infrastructure` |
| Métricas y SLO | El servicio publica las métricas `errors_total` y `generation_duration_ms` con el código de error; u6 debe poder ver en ellas un modelo bloqueado (`MODEL_FAILURE` sostenido) o un identificador inválido (la invocación falla al inicializar). u2 no tiene métricas ni SLO propios: la salud y la tasa de error por componente son las del servicio, y el MVP no tiene SLO por decisión confirmada | `u6-infrastructure` |
| Variable de Terraform | La variable del identificador del modelo debe validar el patrón exacto de identificadores de `security-design.md` para detener un valor mal escrito antes del despliegue | `u6-infrastructure` |
| Configuración completa | Región, tiempo de conexión de 5 s y de lectura de 50 s, tiempo máximo de la función mayor que 51 s (el plazo del servicio es 55 s y la función de u1 tiene 57 s), y el permiso que la prueba de humo necesita para leer la configuración del registro de invocaciones | `u6-infrastructure` |
| Riesgo de IAM | El comodín de región del modelo base es una ampliación acotada a un modelo; el retroceso por alias de la función no revierte el permiso, así que un cambio de modelo se revierte aplicando de nuevo la revisión anterior con Terraform | `u6-infrastructure` (revisión de IAM) |
| Acceso a los modelos | Acceso habilitado y formulario de uso de Anthropic enviado en la cuenta; ya se vio que sin eso la llamada falla con un error de acceso | La prueba de humo de u6 y la evaluación de u2 (un modelo bloqueado se registra) |

## Estrategia de despliegue y retroceso

u2 no tiene despliegue propio. Se despliega con la función de generación y se retrocede con ella (apuntar el alias a la versión anterior, ver `cicd-pipeline.md` de u1). No hay datos que revertir (NFR4.1: el acceso al modelo no guarda nada; el único archivo es `docs/evaluacion-modelos.md`, versionado en Git, que se revierte con Git).

## Secretos y credenciales

Sin secretos de aplicación: el acceso usa la cadena de credenciales estándar de AWS (rol de ejecución en AWS, perfil local en la evaluación) (NFR5.1). El flujo de despliegue sigue usando la federación de identidad de GitHub definida en u1.

## Assumptions & Open Questions

- Abierto: el identificador de Amazon Titan y su acceso en la cuenta; se fija en Code Generation.
- Decidido: la búsqueda de patrones de claves de AWS la agrega y la posee la etapa de CI de `u6-infrastructure` (ver la tabla de entregas).
- Abierto: tamaño del grupo de conexiones del cliente de Bedrock; se fija en Code Generation.
