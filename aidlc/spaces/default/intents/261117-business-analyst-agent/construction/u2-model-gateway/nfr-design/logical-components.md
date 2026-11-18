# Logical Components — u2-model-gateway

Documentos de entrada: `security-requirements.md`, `tech-stack-decisions.md`, `functional-spec.md`, `rules.md` y `contract-summary.md`. No hubo preguntas en esta etapa.

Vista por componentes de dónde se aplican los patrones de diseño no funcional de u2, como puente hacia Infrastructure Design. u2 no se despliega por separado: es una biblioteca dentro del servicio de `u1-walking-skeleton` y `u3-story-generator`.

## Inventario lógico

| Componente lógico | Qué es | Patrones que se aplican | Dominio de falla |
|-------------------|--------|------------------------|------------------|
| Selector de perfil de modelo | Lee la configuración (modelo, región, tiempos de espera) y arma el `ModelProfile` | Lista cerrada de proveedores `anthropic` y `amazon`; rechazo antes de cualquier llamada a AWS (NFR5.3); valores por defecto de 50 s para ambos modelos (NFR1.2) | Al inicializar el servicio: un valor inválido impide armar el acceso; en la función de AWS eso hace fallar cada invocación, por lo que la prueba de humo del despliegue lo detecta antes de que lo use una persona |
| Cliente de Bedrock | Una llamada al modelo con la API de conversación | Cliente de AWS creado una vez y reutilizado con una configuración fija: cero reintentos propios (NFR1.4), tiempo de conexión de 5 s y tiempo de lectura de 50 s (NFR1.2). El tiempo pedido en cada llamada (que cambia por llamada) no se configura en el cliente: se aplica en la llamada con una espera acotada sobre un hilo de trabajo, de modo que la persona que llama recupera el control al cumplirse el tiempo pedido más una tolerancia de 1 s (NFR1.1), aunque el hilo siga hasta su propio tope de 50 s; la conexión no suma tiempo adicional porque ese mismo plazo la cubre. Efecto acotado de los hilos abandonados: con la concurrencia máxima de 5 del servicio y un solo intento por llamada, hay a lo sumo unos pocos hilos en vuelo, y el grupo de conexiones del cliente se dimensiona para ese máximo (el tamaño exacto se fija en Code Generation) | Una llamada: un fallo no afecta a las demás |
| Traductor de errores | Tabla fija de código de AWS a `kind` y `reason`, con texto propio | Descarta el texto de AWS en el punto de captura (NFR4.2); valor por defecto `unavailable` y `unknown` | Sin estado |
| Registro de llamada | Cuatro campos por llamada | Solo identificador del modelo, resultado, motivo y duración (NFR4.2) | Si falla, la llamada sigue |
| Comando de evaluación | Genera con cada modelo los 5 títulos y escribe el registro | Se niega sin 5 títulos aprobados (NFR4.3); sin reintentos; un modelo bloqueado no detiene a los demás; escribe solo `docs/evaluacion-modelos.md` (NFR4.1); mide el tiempo de cada llamada con un reloj monótono alrededor de la llamada (NFR1.3) y calcula la puntuación por modelo contando los resultados con formato correcto (NFR2.1); ambos datos los calcula y escribe el propio comando | Se ejecuta a mano, fuera del servicio desplegado |
| Amazon Bedrock | Servicio externo | Permiso mínimo por modelo (NFR5.2) | Externo; su fallo se traduce a `ModelError` |

## Radio de impacto

- Un fallo de Bedrock afecta solo a la llamada en curso y se traduce a un `ModelError`; no se propaga.
- La biblioteca no tiene estado: un fallo no deja datos corruptos.
- El comando de evaluación no corre en el servicio desplegado; su fallo no afecta a las personas.

## Recursos compartidos

- La cuenta y la región de AWS (us-east-1) son compartidas con el servicio.
- El rol de ejecución es el único recurso con acceso a los modelos; su alcance lo verifica `u6-infrastructure`.

## Puente con Infrastructure Design

Infrastructure Design debe: entregar al rol de ejecución solo el permiso de invocar los modelos de `ModelProfile` (Claude Sonnet y Amazon Titan configurados), sin comodines sobre todos los modelos (solo se admite un comodín de región para el modelo base de un perfil de inferencia, como indica `security-design.md`); confirmar el acceso a ambos modelos en la cuenta; y no activar el registro de invocaciones de modelos en la cuenta.

## Categorías que u2 no produce como documento propio

Por ser una biblioteca, u2 no escribe `performance-requirements`, `scalability-requirements`, `reliability-requirements` ni `observability-requirements` como documentos aparte. Lo que le toca de cada una está cubierto así:

- **performance-requirements:** los tiempos de espera y el único intento por llamada están en `tech-stack-decisions.md` (NFR1.1 a NFR1.4) y en el cliente de Bedrock de este documento.
- **scalability-requirements:** sin estado; la capacidad concurrente la imponen el servicio y la infraestructura (NFR3 es N/A en u2).
- **reliability-requirements:** la fiabilidad de una llamada es la traducción de errores a cuatro tipos y el reintento decidido por el servicio, no por u2.
- **observability-requirements:** los cuatro campos de registro por llamada de este documento; las métricas del servicio son de `u1-walking-skeleton` y `u3-story-generator`.

## Cobertura de NFR1 y NFR8

- NFR1.1 a NFR1.4: cliente de Bedrock y selector de perfil (tiempos de espera, un solo intento).
- NFR2.1: comando de evaluación (puntuación de formato por modelo).
- NFR8.1 a NFR8.4: no son patrones de diseño; los verifican Code Generation (pruebas primero) y Build and Test (umbral de cobertura en CI).

## Assumptions & Open Questions

- Abierto: cómo se aloja la comprobación de patrones de claves en CI.
- Abierto: el identificador de Amazon Titan y su acceso en la cuenta.
