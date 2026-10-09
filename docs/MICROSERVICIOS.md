# Arquitectura de Microservicios y Mensajería

## Visión General

Cuando el usuario pulsa **Consultar**, la página no espera a que se calcule el resultado: la API registra un trabajo, lo publica en RabbitMQ y responde al instante. Dos microservicios lo procesan en cadena (primero el **recomendador**, después el **validador**) y el resultado vuelve a la API, que la página consulta periódicamente hasta que está listo.

```
Página ──POST /api/pipeline/submit──► API ──► [tnm.recommendation.request] ──► Recomendador ◄──► Neo4j
  ▲                                    ▲                                            │
  │                                    │                                            ▼
  └──GET /api/pipeline/result/<id>─────┤                                 [tnm.validation.request]
       (cada 2 s)                      │                                            │
                                       │                                            ▼
                                       └──────── [tnm.validation.result] ◄──── Validador (simulado)
```

El validador actual es **simulado**: aplica una regla por palabras clave, no un modelo de aprendizaje automático. Sustituirlo por un modelo real es trabajo futuro (ver [más abajo](#sustituirlo-por-un-modelo-de-ml-real-trabajo-futuro)).

Ver [DIAGRAMAS.md](DIAGRAMAS.md) para los diagramas de arquitectura y de secuencia, y [DOCKER.md](DOCKER.md) para los contenedores y puertos.

## Servicios

| Servicio | Código | Función |
|----------|--------|---------|
| `frontend` | `frontend/`, `nginx/default.conf` | nginx: sirve la página y reenvía `/api/...` a la API |
| `api` | `backend/api.py` | Recibe las consultas, publica los trabajos, recoge los resultados y los sirve a la página |
| `recommender` | `services/recommender_service.py` | Consulta Neo4j y genera las recomendaciones de cada estadio |
| `ml-validator` | `services/ml_validator_service.py` | Evalúa cada tratamiento (validador simulado) |
| `rabbitmq` | — | Transporta los mensajes entre la API y los microservicios |
| `neo4j` | — | Grafo con los estadios, pruebas y tratamientos |
| `seed` | `scripts/import_csv.py` | Carga los datos en Neo4j al arrancar (no participa en las consultas) |

`recommender` y `ml-validator` no tienen API HTTP ni puertos publicados: solo se comunican a través de RabbitMQ.

## Flujo de una Consulta

1. **Página** (`frontend/js/entradas.js`): comprueba que estén completos edad, sexo, altura, peso, T, N y M, y envía `POST /api/pipeline/submit` con los valores TNM y un objeto `context` con los datos del paciente.
2. **nginx** reenvía la petición al servicio `api`.
3. **API**: genera un `job_id` (UUID), guarda el trabajo en memoria con estado `processing`, publica un mensaje en `tnm.recommendation.request` y responde `202` con el `job_id`.
4. **Recomendador**: consume el mensaje, consulta Neo4j y, si `context.surgery_preference` es `"No"`, quita los tratamientos quirúrgicos (Surgery, Lumpectomy, Mastectomy) y descarta los estadios que se queden sin tratamientos. Publica el resultado en `tnm.validation.request`.
5. **Validador**: evalúa cada tratamiento y publica el resultado final en `tnm.validation.result`.
6. **API**: un hilo consumidor recibe el resultado y marca el trabajo como `completed`.
7. **Página**: consulta `GET /api/pipeline/result/<job_id>` cada 2 segundos (hasta 30 intentos, 60 segundos). Cuando el estado es `completed`, vuelve a aplicar el filtro de cirugía (redundante, por seguridad) y muestra `final_recommendations`: **como máximo los 3 primeros estadios**, con sus pruebas y tratamientos.

Si algo falla por el camino, la página no muestra tratamientos (ver [Si la evaluación no se completa](#si-la-evaluación-no-se-completa)).

## Colas de RabbitMQ

| Cola | Publica | Consume | Contenido |
|------|---------|---------|-----------|
| `tnm.recommendation.request` | API | recommender | Solicitud: TNM y datos del paciente |
| `tnm.validation.request` | recommender | ml-validator | Recomendaciones sin validar |
| `tnm.validation.result` | ml-validator (y cualquier microservicio que falle) | API | Resultado final o aviso de fallo |

- Se usa el exchange por defecto de RabbitMQ: cada mensaje se publica directamente en la cola por su nombre.
- Las colas son durables y los mensajes persistentes (`delivery_mode=2`): sobreviven a un reinicio de RabbitMQ.
- Los microservicios procesan los mensajes de uno en uno (`prefetch_count=1`); el consumidor de la API, de diez en diez.
- Cada mensaje se confirma (`ack`) al terminar de procesarlo, también si falla: no se reintenta.
- Los nombres de las colas se configuran con variables de entorno (`RECOMMENDATION_REQUEST_QUEUE`, `VALIDATION_REQUEST_QUEUE`, `VALIDATION_RESULT_QUEUE`), fijadas en `docker-compose.yml`.

## Formato de los Mensajes

### `tnm.recommendation.request` (API → recomendador)

```json
{
  "job_id": "2f501371-e88b-4d59-8034-30f4d47f28ef",
  "tnm": {"t_label": "T1", "n_label": "N0", "m_label": "M0"},
  "context": {
    "edad": "45", "sexo": "Femenino", "peso": "60", "talla": "165",
    "RP": "Positivo", "RE": "Positivo", "HER2": "Negativo", "Grade": "II",
    "surgery_preference": "No"
  },
  "timestamp": 1791434124
}
```

`context` contiene lo que envía la página. De todos sus campos, solo `surgery_preference` influye en el resultado.

### `tnm.validation.request` (recomendador → validador)

```json
{
  "job_id": "2f501371-e88b-4d59-8034-30f4d47f28ef",
  "tnm": {"t_label": "T1", "n_label": "N0", "m_label": "M0"},
  "recommendations": [
    {
      "Stage": "Stage IIA",
      "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
      "TreatmentOptions": ["Endocrine Therapy", "Radiation Therapy"]
    }
  ],
  "context": {"...": "igual que en la solicitud"},
  "timestamp": 1791434125
}
```

### `tnm.validation.result` (validador → API)

Cuando todo va bien, el validador publica el resultado completo: `recommendations`, `final_recommendations`, `validation_details`, `summary` y `model`. Es el mismo objeto que devuelve la API en el campo `result` de [`/pipeline/result`](API.md#5-get-pipelineresultjob_id).

Cuando un microservicio no puede procesar un trabajo, publica en esta misma cola un aviso de fallo, y la API marca el trabajo como `failed`:

```json
{
  "job_id": "2f501371-e88b-4d59-8034-30f4d47f28ef",
  "status": "failed",
  "error": "recommender: Cannot resolve address neo4j:7687",
  "timestamp": 1791434130
}
```

El prefijo de `error` indica el servicio que falló (`recommender:` o `ml-validator:`). Si el mensaje ni siquiera tiene `job_id`, el fallo solo queda en los registros del servicio.

## Componentes

### `backend/api.py`: API

- Expone los endpoints descritos en [API.md](API.md).
- Al enviar al pipeline solo comprueba que lleguen T, N y M; no valida sus valores.
- Guarda los trabajos en un diccionario en memoria (`jobs_store`), protegido con un lock.
- Un hilo en segundo plano consume `tnm.validation.result`; si pierde la conexión con RabbitMQ, reintenta cada 5 segundos.
- Consulta Neo4j con transacciones gestionadas (`execute_read`), que reintentan ante errores transitorios, como la primera consulta tras reiniciar Neo4j.

### `services/recommender_service.py`: recomendador

- Ejecuta en Neo4j la misma consulta que `/get_stage_info` (ver [Modelo de datos](#modelo-de-datos-en-neo4j)).
- Aplica el filtro de preferencia de cirugía.
- Mantiene una sola conexión a Neo4j durante toda su vida; si pierde RabbitMQ, se reconecta cada 5 segundos.
- Si falla al procesar un trabajo, publica un aviso de fallo en `tnm.validation.result`.

### `services/ml_validator_service.py`: validador simulado

Regla actual (`evaluate_treatment`):
- Rechaza un tratamiento si su nombre contiene `experimental`, `no recomendado` o `descartar`; si no, lo aprueba.
- Asigna una confianza fija: `0.78` si aprueba y `0.42` si rechaza.
- Si rechaza todos los tratamientos de un estadio, conserva el primero para no dejarlo vacío.
- Identifica el modelo como `mock-validator` versión `0.1.0`.

Con los datos actuales ninguno de los 8 tratamientos contiene esas palabras, así que **el validador aprueba todo**: `final_recommendations` coincide con `recommendations`. No consulta Neo4j ni usa los datos del paciente.

#### Sustituirlo por un modelo de ML real (trabajo futuro)

- **Mantener el contrato de mensajes:** consumir `tnm.validation.request` y publicar en `tnm.validation.result` con los mismos campos. Así la API y la página no necesitan cambios.
- **Sustituir la lógica** de `evaluate_treatment` (o de `validate_recommendations`) por la inferencia del modelo, y actualizar el campo `model` con su nombre y versión.
- **Aprovechar los datos del paciente:** el mensaje ya incluye `context` (edad, receptores RP/RE, HER2, grado), que hoy no se usa.
- **Darle su propia imagen Docker:** hoy los cuatro servicios de Python comparten la imagen `biomedicos-app`. Dependencias pesadas como scikit-learn o TensorFlow no deberían añadirse a esa imagen, sino a un Dockerfile propio del validador.

### `frontend/js/entradas.js`: página

- Llama a la API con rutas relativas (`/api/...`), así que no depende del host ni del puerto.
- Gestiona el envío, la consulta periódica del resultado, la presentación y los errores.

## Si la Evaluación no se Completa

La página **solo muestra tratamientos que han pasado por todo el pipeline** (recomendador y validador). El validador está pensado para evaluar cada tratamiento según la base de conocimiento y los datos del paciente; mostrar resultados que no ha evaluado podría presentar tratamientos que habría descartado.

Por eso, cuando:
- el envío al pipeline falla (por ejemplo, `503` porque RabbitMQ no está disponible);
- el trabajo termina como `failed` (un microservicio avisó de un fallo);
- tras 30 consultas (60 segundos) el trabajo sigue sin terminar (por ejemplo, porque un microservicio está detenido);

la página no muestra resultados y presenta el aviso **«No se pudo completar la evaluación»**, con el motivo y la sugerencia de reintentar. El detalle técnico del fallo (campo `error` de `/pipeline/result`) queda en la consola del navegador.

El endpoint `/get_stage_info`, que consulta Neo4j sin pasar por el pipeline, sigue disponible para pruebas y diagnóstico, pero la página no lo usa.

*Hasta la v2.3, la página tenía un «modo degradado» que en estos casos mostraba los resultados de `/get_stage_info` sin validar; se eliminó en la v2.4.*

## Modelo de Datos en Neo4j

Los datos proceden de una ontología de estadificación del cáncer (`cancer_staging_terms.owl`) y se cargan desde `data/nodos.csv` y `data/relaciones.csv` (ver [DATABASE.md](DATABASE.md)).

**Nodos que usan las consultas:**

| Tipo (label de Neo4j) | Valores |
|-----------------------|---------|
| `T_Stage_Finding` | T0, T1, T2, T3, T4, Tx, Tis |
| `N_Stage_Finding` | N0, N1, N2, N3, N4, Nx |
| `M_Stage_Finding` | M0, M1, MX Stage Finding |
| `R7_Stage`, `Sub_R7_Stage` | Estadios según la 7.ª edición de AJCC |
| `R8_Stage`, `Sub_R8_Stage` | Estadios según la 8.ª edición de AJCC |
| `Test` | 9 pruebas (Mammogram, Bone Scan, HER2 Test…) |
| `Treatment` | 8 tratamientos (Surgery, Chemotherapy, Endocrine Therapy…) |

El grafo incluye además otros nodos de la ontología (subcategorías de T/N/M, estado de receptores, grado histológico) que las consultas no usan.

**Relaciones:**
- `Has_Stage`: de cada valor T, N y M a los estadios con los que se relaciona, de ambas ediciones.
- `Has_Recommended_Test` y `Has_Treatment_Option`: de los estadios a sus pruebas y tratamientos. **Solo los estadios de la 8.ª edición las tienen.**

**Consulta** (en `api.py` y en el recomendador):

```cypher
MATCH (n:N_Stage_Finding {label: $n_label})-[:Has_Stage]->(target),
      (m:M_Stage_Finding {label: $m_label})-[:Has_Stage]->(target),
      (t:T_Stage_Finding {label: $t_label})-[:Has_Stage]->(target)
MATCH (target)-[:Has_Recommended_Test]->(test),
      (target)-[:Has_Treatment_Option]->(treatment)
RETURN target AS Stage,
       collect(distinct test.label) AS RecommendedTests,
       collect(distinct treatment.label) AS TreatmentOptions
```

Consecuencias:
- Solo se devuelven estadios de la 8.ª edición, porque son los únicos con pruebas y tratamientos.
- El grafo relaciona cada valor T, N y M con varios estadios por separado, y la consulta devuelve todos los que comparten los tres. Por eso una combinación puede dar varios estadios (T2, N1, M0 → Stage IIA, IIB y IIIA) o ninguno (Tis, N0, M0 → 404). No es una tabla de estadificación AJCC completa.

## Limitaciones Conocidas

- **Trabajos en memoria:** se pierden al reiniciar la API, y solo puede haber una instancia de la API.
- **Sin reintentos ni cola de mensajes fallidos (DLQ):** si un microservicio falla con un mensaje, avisa a la API y el mensaje se descarta.
- **No se puede escalar con `docker compose up --scale`:** los servicios tienen `container_name` fijo. Para ejecutar varias réplicas de un microservicio habría que quitarlo; RabbitMQ repartiría los mensajes entre ellas.
- **Seguridad pensada para entorno local:** `/pipeline/debug` no tiene autenticación, y RabbitMQ (`guest`/`guest`) y Neo4j (`neo4j`/`password`) usan credenciales por defecto.
- **Validador simulado** y **datos del paciente sin usar**, salvo la preferencia de cirugía.
- **La página muestra como máximo 3 estadios** por consulta.

## Mejoras Futuras

- Modelo de ML real para el validador (ver [arriba](#sustituirlo-por-un-modelo-de-ml-real-trabajo-futuro)).
- Guardar los trabajos en un almacenamiento compartido (por ejemplo Redis) para no perderlos y poder escalar la API.
- Reintentos y cola de mensajes fallidos en RabbitMQ.
- Autenticación en la API y credenciales propias en RabbitMQ y Neo4j.

## Monitoreo y Depuración

- **Consola de RabbitMQ** (http://localhost:15672, `guest`/`guest`): en **Queues**, cada una de las tres colas debe tener 1 consumidor; si los mensajes se acumulan, el servicio que la consume está detenido o atascado.
- **Registros:** `docker compose logs -f api recommender ml-validator`. Cada servicio indica cada trabajo procesado (`job_id=... enviado a validación`, `... validado y publicado`, `Resultado recibido para job_id=...`) y cada fallo.
- **API:** `/pipeline/health` (RabbitMQ y consumidor) y `/pipeline/debug` (todos los trabajos).
- **Prueba de extremo a extremo:** `.\scripts\test-pipeline.ps1`.
- **Publicar un mensaje a mano** (por ejemplo, para probar el aviso de fallo con un mensaje sin TNM), con la API de administración de RabbitMQ:
  ```bash
  curl -u guest:guest -H "content-type:application/json" -X POST \
    "http://localhost:15672/api/exchanges/%2F/amq.default/publish" \
    -d '{"properties":{"delivery_mode":2},"routing_key":"tnm.recommendation.request","payload":"{\"job_id\":\"prueba-fallo\"}","payload_encoding":"string"}'
  ```
  Después, `GET /pipeline/result/prueba-fallo` devuelve `status: "failed"` con el motivo.

## Referencias

- [API.md](API.md) - Endpoints de la API
- [DOCKER.md](DOCKER.md) - Instalación, servicios y puertos
- [DATABASE.md](DATABASE.md) - Datos de Neo4j
- [Documentación de RabbitMQ](https://www.rabbitmq.com/docs)
- [Driver de Python para Neo4j](https://neo4j.com/docs/python-manual/current/)
