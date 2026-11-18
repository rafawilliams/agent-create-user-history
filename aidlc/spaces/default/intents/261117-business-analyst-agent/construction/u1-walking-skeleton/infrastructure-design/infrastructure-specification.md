# Infrastructure Specification — u1-walking-skeleton

Entradas: `nfr-design/*` de esta unidad, `functional-spec.md`, `contract-summary.md`, `components.md`. Respuestas: `infrastructure-design-questions.md` (ID Qn). Región: us-east-1. Infraestructura como código: Terraform. Los valores marcados "propuesta" no los confirmó la persona; se fijan o corrigen en Code Generation y en `u6-infrastructure`.

## Deployment

| Facet | Choice | Rationale |
|-------|--------|-----------|
| Modelo de cómputo | Sin servidores: una función de AWS Lambda con el servicio de generación (Python) | Uso ocasional de 5 personas; sin estado (NFR3.1); sin servidor que operar |
| Entrada de la API | Pasarela REST de Amazon API Gateway con el límite de integración ampliado mediante una cuota ajustable de la cuenta (ID Q3). **Es un supuesto, no un hecho**: la cuota requiere solicitud y aprobación, y puede afectar el límite de limitación (throttle) de la cuenta | El servicio responde hasta los 55 s (NFR1.1); las pasarelas HTTP suelen limitar a unos 30 s |
| Cadena de tiempos | Servicio 55 s < función 57 s < integración de la pasarela 58 s < interfaz 60 s | Cada capa corta después de la anterior y antes de la siguiente; ninguna comparte el mismo valor |
| Si la cuota se niega | Se vuelve a la opción B de ID Q3 (URL de función con respuesta en flujo) o se rediseña el presupuesto con la persona, sin acortar en silencio el corte de 50 s del modelo | Alternativa concreta, decidida en `u6-infrastructure` |
| Red | Sin VPC propia; la función llama a Amazon Bedrock por su punto de entrada público de AWS, solo por HTTPS | Sin recursos privados que proteger en el esqueleto; evita costo y complejidad de red (propuesta) |
| Almacenamiento de datos | Ninguno (NFR4.1). Solo existe el depósito de archivos estáticos de la pantalla (ver abajo) | Sin persistencia en el MVP |
| Pantalla mínima | Depósito privado de Amazon S3 detrás de una distribución de Amazon CloudFront con HTTPS (ID Q2) | Alojamiento estático barato y simple para 5 personas |
| Entornos | Uno solo, desplegado al integrar en `main` | Práctica del equipo (`team.md`, Deployment) |
| IaC | Terraform, con estado remoto y bloqueo (propuesta: bucket de S3 con bloqueo nativo) | Práctica del equipo; el estado remoto lo define `u6-infrastructure` |
| Dimensionado | Función con 512 MB de memoria y tiempo de ejecución de 57 s (propuesta); concurrencia reservada de 5 como respaldo (NFR3.1) | El plazo de 55 s del servicio cabe en 57 s. La cuota de concurrencia de la cuenta puede impedir reservar 5 (siempre debe quedar un mínimo sin reservar): se verifica en la cuenta antes de aplicar; si no se puede, el tope lo da solo el límite de la pasarela |
| Limitación y 429 | El 429 de `RATE_LIMITED` lo produce **solo** el límite de uso de la pasarela (ráfaga 5, tasa sostenida 1 por segundo), con una respuesta de pasarela personalizada. El exceso de concurrencia reservada de la función puede llegar al cliente como 502 detrás de una pasarela REST; se acepta como respaldo de costo, no como parte del contrato | Corrige la suposición de `scalability-design.md`: el contrato C1 solo promete 429 por el límite de la pasarela |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---------|------|---------------|-------|
| Amazon API Gateway (REST) | Entrada HTTPS y límite de tasa | HTTPS obligatorio; límite de uso: propuesta de 1 solicitud por segundo sostenida y ráfaga de 5 (`scalability-design.md`); respuesta 429 fija con la forma del error de C1 (`RATE_LIMITED`, `retryable` verdadero); tiempo de espera de integración 58 s (ver la cadena de tiempos) | NFR3.1, NFR3.2 (parcial), NFR1.1. Si la cuenta no admite 60 s, se activa el criterio de revisión de `performance-design.md` |
| AWS Lambda | Servicio de generación | Python; concurrencia reservada 5; variable `APP_ENV` fijada a `prod`; **sin** `ALLOW_SIMULATED_SESSION`; registro estructurado con lista cerrada de campos | NFR5.2: sin verificador real, falla cerrado (rechaza toda solicitud) hasta que exista `u4-access-control` |
| Amazon Bedrock | Modelo de IA | Invocación solo del modelo configurado; **registro de invocaciones del modelo desactivado**; acceso al modelo habilitado en la cuenta | NFR4.2. Elección del modelo (Titan o Claude Sonnet) sigue abierta; se parametriza |
| IAM (rol de ejecución) | Permisos de la función | Permiso mínimo: invocar solo el modelo configurado, escribir sus propios registros y métricas; sin permisos amplios | NFR5.1 |
| Amazon CloudWatch | Registros y métricas | Grupo de registros con retención de 14 días (propuesta); métricas `requests_total`, `errors_total`, `generation_duration_ms` | NFR1.4, NFR3.3, NFR4.5 |
| Amazon S3 (pantalla) | Archivos estáticos | Privado; bloqueo de acceso público; versionado activado (permite el retroceso); solo lo lee la distribución mediante control de acceso al origen (OAC) | Sin datos de personas |
| CORS | Política de la pasarela | Solo el origen de la distribución de la pantalla; la configuración exacta se fija en Code Generation y con `u4-access-control` | Evita que otros orígenes llamen a la API desde un navegador |
| Amazon CloudFront | Entrega de la pantalla | HTTPS; certificado por defecto de la distribución (propuesta) | Dominio propio fuera del MVP |

## Seguridad de IAM: evaluación de riesgo

| Elemento | Diseño | Riesgo y mitigación |
|----------|--------|---------------------|
| Rol de ejecución de la función | Permiso para invocar solo el modelo configurado, y escribir sus registros y métricas | Riesgo: un permiso amplio filtraría acceso a otros modelos. Mitigación: recurso acotado al modelo, sin comodines |
| Federación de GitHub (OIDC) | La confianza exige el repositorio de este proyecto; el rol que aplica cambios (`apply`) solo se asume desde la rama `main`; un rol de solo lectura distinto se asume en solicitudes de integración para `terraform plan` | Riesgo: otro repositorio o rama asumiría el rol. Mitigación: condiciones de confianza sobre repositorio y rama |
| Rol de despliegue | Con un límite de permisos (permissions boundary) que acota lo que puede crear, incluidos los roles de IAM que Terraform crea | Riesgo: escalada de privilegios al crear roles. Mitigación: ningún rol creado puede exceder el límite |
| Sesión de despliegue | Credenciales temporales de corta duración | Riesgo: robo de credenciales. Mitigación: caducidad corta, sin claves de larga vida |

Cualquier cambio de roles, redes o cifrado requiere una revisión de seguridad documentada (guía de operación).

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|-----------------|------------|----------------|-----------------|
| Pasarela REST y función de generación | u1-walking-skeleton (esqueleto) | u3-story-generator, u4-access-control | La función es una; u3 y u4 extienden su código, no crean otra |
| Rol de ejecución | u6-infrastructure (versión final) | u1, u2, u3 | Permiso mínimo al modelo configurado |
| Estado remoto de Terraform | u6-infrastructure | u1 | Solo la identidad de despliegue |
| Cuenta y región de AWS | u6-infrastructure | Todas | us-east-1 |

El esqueleto crea una versión mínima de estos recursos con Terraform; `u6-infrastructure` la endurece y completa sin cambiar los nombres.

## Qué se puede verificar en AWS y qué no, en el esqueleto

Con `APP_ENV` desplegado y sin verificador real, el servicio **rechaza toda solicitud** (NFR5.2). Por eso, en el entorno desplegado solo se comprueba la ruta de rechazo y la forma de los errores. La ruta de éxito de extremo a extremo y la medición real de tiempo (NFR1.3, cadena de 60 s) se comprueban **localmente**, con el verificador simulado habilitado solo en `local` y un modelo real, y en el entorno desplegado solo cuando exista el verificador real de `u4-access-control`. Esta limitación está aceptada y queda registrada: el esqueleto desplegado demuestra la infraestructura y el fallo cerrado, no el flujo completo de la persona.

## Costo (estimación orientativa, propuesta)

Con uso ocasional de 5 personas, el costo dominante es el de las llamadas al modelo; la función, la pasarela, el almacenamiento y la distribución quedan en cantidades marginales. No se estima una cifra exacta aquí: la valida la persona antes de ampliar el uso, y el tope de concurrencia de 5 y el límite de tasa acotan el máximo.

## Assumptions & Open Questions

- Abierto: confirmar en la cuenta de AWS la cuota que amplía el tiempo de integración de la pasarela REST a 60 s.
- Abierto: elección final entre Titan y Claude Sonnet y su disponibilidad en us-east-1.
- Supuesto: los valores de memoria, retención, tasa y estado remoto son propuestas de esta etapa.
- Abierto: la forma exacta del 429 de la concurrencia reservada depende de lo que permita la pasarela; se verifica con una prueba en el entorno desplegado.
