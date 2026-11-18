# CI/CD Pipeline — u1-walking-skeleton

Herramienta: GitHub Actions (ID Q1). Un solo entorno; despliegue automático al integrar en `main` (`team.md`). Toda integración pasa antes por una revisión de código.

## Etapas

| Etapa | Cuándo corre | Qué hace | Puerta (si falla) |
|-------|--------------|----------|-------------------|
| 1. Estilo y tipos | En cada solicitud de integración | Black y Ruff (Python); Prettier y ESLint (React) | Bloquea la integración (NFR8.3) |
| 2. Pruebas y cobertura | En cada solicitud de integración | Pruebas escritas antes que el código (TDD); cobertura mínima de 80 % de líneas | Bloquea la integración (NFR8.1, NFR8.2) |
| 3. Verificación de infraestructura | En cada solicitud de integración | `terraform fmt`, `terraform validate` y `terraform plan`; revisión estática de seguridad de la infraestructura | Bloquea la integración |
| 4. Verificaciones de seguridad del diseño | En cada solicitud de integración | Pruebas automáticas de que (a) con `APP_ENV` distinto de `local` y `test` no se enlaza el verificador simulado, (b) los registros no llevan contenido ni credenciales, (c) el plan de Terraform no define `ALLOW_SIMULATED_SESSION` ni activa el registro de invocaciones del modelo | Bloquea la integración (NFR5.2, NFR4.2, NFR4.3) |
| 5. Despliegue | Al integrar en `main` | `terraform apply` del plan revisado; publicación de la función y de la pantalla; invalidación de la distribución | Detiene el despliegue y deja la versión anterior |
| 6. Prueba de humo | Tras el despliegue | Una solicitud de humo a la API y una carga de la pantalla (ver abajo) | Marca el fallo; el retroceso es manual (ver abajo) |

## Prueba de humo

- La pantalla responde por HTTPS.
- Una solicitud sin sesión a la API devuelve SESSION_INVALID con forma de error de C1 (confirma que falla cerrado, NFR5.2). No se envía ningún título real. En el esqueleto, esta es la única ruta que se puede comprobar en AWS; la ruta de éxito se prueba en local (ver `infrastructure-specification.md`).
- La métrica de solicitudes de la función se incrementa con esa misma solicitud de humo (no es una prueba de éxito contra el modelo).
- Una solicitud real al modelo con un título fijo de prueba se hace solo de forma manual, una vez, para medir NFR1.3 (es el criterio del esqueleto; no corre en cada despliegue, por costo).

## Estrategia de despliegue

Despliegue directo de una versión nueva de la función con un alias estable. Sin azul-verde ni canary: un solo entorno, 5 personas y uso ocasional.

## Retroceso

1. La función se publica como versión numerada con un alias `live` que Terraform controla mediante una variable con la versión; retroceder es volver a aplicar con la versión anterior (minutos). No se cambia el alias a mano, para no generar deriva del estado de Terraform.
2. La pantalla: la versión anterior de los archivos se conserva como versión del depósito; se restaura e invalida la distribución.
3. La infraestructura: se aplica de nuevo la revisión anterior de `main` con Terraform. No hay datos que revertir (NFR4.1).
4. Quién decide: el retroceso es **manual**; lo inicia quien integró el cambio cuando falla la prueba de humo (el flujo de despliegue marca el fallo y avisa en rojo) o ante errores en las métricas. No hay retroceso automático en el MVP.
5. Estado de Terraform: como el despliegue corre en un ejecutor efímero de GitHub Actions, el estado **debe ser remoto desde el primer `apply`** (un estado local se perdería entre ejecuciones). Un paso de arranque único y manual, hecho por la persona antes del primer despliegue, crea el depósito de estado con versionado y cifrado; `u6-infrastructure` lo documenta y lo gobierna. Hasta que ese paso se haga, el esqueleto no se despliega desde el pipeline y se valida solo con `terraform plan`.
6. Plan: en la etapa 5 se aplica el plan guardado como archivo de la solicitud de integración revisada, para que lo aplicado sea lo revisado; si el estado cambió, se recalcula y se vuelve a revisar.

## Secretos y credenciales en CI/CD

- El despliegue se autentica en AWS con federación de identidad de GitHub (credenciales temporales), sin claves guardadas en el repositorio ni en variables de larga vida.
- Dos identidades: un rol de solo lectura para `terraform plan` en las solicitudes de integración, y un rol de aplicación que solo se asume desde la rama `main`; ambos con condiciones de confianza sobre el repositorio (ver la evaluación de riesgo de IAM en `infrastructure-specification.md`).
- El rol de despliegue tiene permiso solo sobre los recursos de este proyecto en us-east-1 y un límite de permisos.
- No hay secretos de aplicación: la función usa su rol de ejecución (NFR5.1). `.env` local sigue ignorado por git.

## Cumplimiento de NFR8

| Requisito | Dónde se verifica |
|-----------|-------------------|
| NFR8.1 TDD | Code Generation (pruebas primero); la revisión de código lo comprueba |
| NFR8.2 80 % de cobertura | Etapa 2 |
| NFR8.3 linters | Etapa 1 |
| NFR8.4 nombres en inglés | Revisión de código y ESLint/Ruff donde aplique |

## Assumptions & Open Questions

- Abierto: nombres de los flujos de trabajo y del rol de despliegue (se fijan en Code Generation y en `u6-infrastructure`).
- Abierto: política de aprobación para un futuro entorno de producción (pendiente desde las prácticas del equipo).
- Supuesto: la cuenta de AWS permite la federación de identidad de GitHub.
