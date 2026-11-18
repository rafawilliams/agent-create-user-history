# NFR Requirements — u1-walking-skeleton — Preguntas

Los requisitos no funcionales de Inception ya fijan el tiempo máximo (60 segundos), la capacidad (hasta 5 personas), la privacidad (sin guardar datos y sin registrar contenido), los secretos, la accesibilidad, los dispositivos y las prácticas de pruebas (`requirements.md`, NFR1 a NFR8). Estas preguntas cubren lo que quedó abierto y que el esqueleto necesita para ser medible.

## Q1. [Operaciones] ¿Qué objetivo de disponibilidad tiene el servicio en el MVP?

Contexto: en `requirements.md` quedó abierto el objetivo de disponibilidad; el uso es ocasional y de hasta 5 personas.

- A. Sin objetivo formal: el MVP se ofrece al mejor esfuerzo, sin compromiso de disponibilidad
- B. 99 % de las solicitudes atendidas sin error del servicio, medido en una ventana de 30 días
- C. 99,9 % de las solicitudes atendidas sin error del servicio, medido en una ventana de 30 días
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q2. [Operaciones] ¿Qué se mide y qué alarmas tiene el MVP?

Contexto: los registros de la nube solo pueden tener errores y métricas, sin el contenido de los títulos ni de las historias (NFR4). Hace falta al menos una métrica de salud y una de tasa de error por cada componente nuevo (guía de operación).

- A. Número de solicitudes, errores por código y duración de cada generación, sin alarmas en el MVP
- B. Lo mismo, más una alarma cuando los errores superan un porcentaje de las solicitudes (indica cuál en Other)
- C. Not yet defined
- X. Other (please specify)

[Answer]: A

## Q3. [Seguridad] ¿Hay un límite de uso para controlar el costo del modelo?

Contexto: cada generación llama al modelo y tiene costo; no hay un límite definido (`requirements.md`, pregunta abierta). El acceso con Gmail u Outlook se agrega después, así que durante el esqueleto el servicio no está abierto a otras personas.

- A. Sin límite en el MVP
- B. Un límite de solicitudes por persona por día (indica el valor en Other)
- C. Un tope de costo mensual con una alerta cuando se acerque
- D. Not yet defined
- X. Other (please specify)

[Answer]: B

## Q4. [Seguridad] ¿Cuántas solicitudes por persona por día permite el límite?

Contexto: en Q3 elegiste un límite de solicitudes por persona por día, sin indicar el valor. Sin una identidad de persona real (llega con el control de acceso), el límite del esqueleto se aplica por origen de la solicitud y se afina después.

- A. 20 solicitudes por persona por día
- B. 50 solicitudes por persona por día
- C. 100 solicitudes por persona por día
- D. Not yet defined
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
