# Documentación de Endpoints API

La API (Flask, servida con Waitress) es accesible de dos formas:

| Base URL | Uso |
|----------|-----|
| `http://localhost:5500/api` | A través del proxy de nginx. Es la que usa la página web (`/api/...` en su mismo origen). |
| `http://localhost:5000` | Acceso directo, para pruebas. El puerto se cambia con `API_PORT` en `.env`. |

Los ejemplos de esta guía usan el acceso directo. Las respuestas son reales, capturadas del sistema en marcha con los datos de `data/*.csv`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | [`/`](#1-get-) | Comprobación de que la API está en marcha |
| GET | [`/labels/t`, `/labels/n`, `/labels/m`](#2-get-labelst-labelsn-labelsm) | Valores T, N y M disponibles en Neo4j |
| GET | [`/get_stage_info`](#3-get-get_stage_info) | Consulta directa (síncrona) de estadios, pruebas y tratamientos |
| POST | [`/pipeline/submit`](#4-post-pipelinesubmit) | Envía una consulta al pipeline de microservicios |
| GET | [`/pipeline/result/<job_id>`](#5-get-pipelineresultjob_id) | Estado y resultado de una consulta del pipeline |
| GET | [`/pipeline/health`](#6-get-pipelinehealth) | Estado de RabbitMQ y del consumidor de resultados |
| GET | [`/pipeline/debug`](#7-get-pipelinedebug) | Todos los trabajos en memoria (depuración) |
| POST | [`/entradas`](#8-post-entradas) | Devuelve el JSON recibido (eco); la página no lo usa |

---

## 1. GET `/`
Verifica que la API está en funcionamiento.

**Response:** 200 OK
```
En ejecución
```

---

## 2. GET `/labels/t`, `/labels/n`, `/labels/m`
Devuelven los valores de los nodos `T_Stage_Finding`, `N_Stage_Finding` y `M_Stage_Finding` (máximo 100, sin orden garantizado).

**Response:** 200 OK
```json
["T0","T1","T4","T2","T3","Tx","Tis"]
```
```json
["Nx","N2","N3","N0","N1","N4"]
```
```json
["MX Stage Finding","M1","M0"]
```

El formulario de la página ofrece valores fijos (T: Tis, T0–T4, Tx; N: N0–N4, Nx; M: M0, M1); no usa estos endpoints.

---

## 3. GET `/get_stage_info`
Consulta Neo4j directamente y devuelve los estadios que corresponden a la combinación T, N y M, con sus pruebas recomendadas y opciones de tratamiento. No pasa por el pipeline ni por el validador.

La página no lo usa: solo muestra resultados que han pasado por el pipeline (ver [MICROSERVICIOS.md](MICROSERVICIOS.md#si-la-evaluación-no-se-completa)). Sirve para pruebas y diagnóstico, por ejemplo para comprobar los datos de Neo4j sin depender de RabbitMQ ni de los microservicios.

**Parámetros (query string, todos obligatorios):**
- `t_label`: valor T (ej. `T2`)
- `n_label`: valor N (ej. `N1`)
- `m_label`: valor M (ej. `M0`)

**Request:**
```
GET http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0
```

**Response:** 200 OK
```json
[
  {
    "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
    "Stage": "Stage IIA",
    "TreatmentOptions": ["Endocrine Therapy", "Radiation Therapy", "Surgery"]
  },
  {
    "RecommendedTests": ["Breast Biopsy", "Bone Scan", "Histologic Typing", "HER2 Test"],
    "Stage": "Stage IIIA",
    "TreatmentOptions": ["Mastectomy", "Lumpectomy", "Chemotherapy"]
  },
  {
    "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
    "Stage": "Stage IIB",
    "TreatmentOptions": ["Endocrine Therapy", "Radiation Therapy", "Surgery"]
  }
]
```

Una misma combinación puede devolver varios estadios: el grafo relaciona cada valor T, N y M con varios estadios, y la consulta devuelve todos los que comparten los tres (ver [MICROSERVICIOS.md](MICROSERVICIOS.md#modelo-de-datos-en-neo4j)). El orden de los elementos no está garantizado.

**Response:** 404 Not Found (la combinación no tiene estadios con pruebas y tratamientos; por ejemplo `Tis`, `N0`, `M0`)
```json
{"error": "No results found"}
```

**Response:** 400 Bad Request (falta algún parámetro)
```json
{"error": "Missing parameters"}
```

---

## 4. POST `/pipeline/submit`
Envía una consulta al pipeline de microservicios (recomendador → validador). Responde inmediatamente con un `job_id`; el resultado se consulta después con [`/pipeline/result/<job_id>`](#5-get-pipelineresultjob_id).

**Body (JSON):**

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `t_label`, `n_label`, `m_label` | Sí | Valores T, N y M. También se aceptan dentro de un objeto `tnm` (`{"tnm": {"t_label": ...}}`). |
| `context` | No | Datos del paciente. Solo se usa `surgery_preference`: con el valor `"No"` (sin distinguir mayúsculas) se excluyen los tratamientos quirúrgicos (Surgery, Lumpectomy, Mastectomy). El resto de campos se reenvía pero no influye en el resultado. |

**Request:**
```
POST http://localhost:5000/pipeline/submit
Content-Type: application/json

{
  "t_label": "T1",
  "n_label": "N0",
  "m_label": "M0",
  "context": {"edad": "45", "sexo": "Femenino", "surgery_preference": "No"}
}
```

**Response:** 202 Accepted
```json
{
  "job_id": "2f501371-e88b-4d59-8034-30f4d47f28ef",
  "message": "Trabajo enviado a microservicios",
  "status": "processing"
}
```

**Response:** 400 Bad Request (faltan T, N o M)
```json
{"error": "Missing TNM parameters"}
```

**Response:** 503 Service Unavailable (no se pudo publicar en RabbitMQ; el trabajo queda como `failed`)
```json
{"error": "Message broker unavailable", "job_id": "..."}
```

---

## 5. GET `/pipeline/result/<job_id>`
Devuelve el estado de un trabajo del pipeline. La página lo consulta cada 2 segundos hasta obtener `completed` o `failed`.

| `status` | Significado |
|----------|-------------|
| `processing` | El trabajo está en el pipeline |
| `completed` | Terminó; `result` contiene las recomendaciones validadas |
| `failed` | Un microservicio no pudo procesarlo o no se pudo publicar; `error` indica el motivo |

**Response:** 200 OK, en proceso
```json
{"job_id": "2f501371-...", "status": "processing"}
```

**Response:** 200 OK, completado (consulta T1, N0, M0 con `surgery_preference: "No"`)
```json
{
  "job_id": "2f501371-e88b-4d59-8034-30f4d47f28ef",
  "status": "completed",
  "result": {
    "job_id": "2f501371-e88b-4d59-8034-30f4d47f28ef",
    "status": "completed",
    "tnm": {"t_label": "T1", "n_label": "N0", "m_label": "M0"},
    "recommendations": [
      {
        "Stage": "Stage IIA",
        "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
        "TreatmentOptions": ["Endocrine Therapy", "Radiation Therapy"]
      },
      {
        "Stage": "Stage IA",
        "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
        "TreatmentOptions": ["Radiation Therapy", "Endocrine Therapy"]
      }
    ],
    "final_recommendations": [
      {
        "Stage": "Stage IIA",
        "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
        "TreatmentOptions": ["Endocrine Therapy", "Radiation Therapy"]
      },
      {
        "Stage": "Stage IA",
        "RecommendedTests": ["Receptor Testing", "Mammogram", "Lymph Node Biopsy"],
        "TreatmentOptions": ["Radiation Therapy", "Endocrine Therapy"]
      }
    ],
    "validation_details": [
      {
        "stage": "Stage IIA",
        "evaluations": [
          {"option": "Endocrine Therapy", "approved": true, "confidence": 0.78, "reason": "Aprobado por validador mock"},
          {"option": "Radiation Therapy", "approved": true, "confidence": 0.78, "reason": "Aprobado por validador mock"}
        ]
      },
      {
        "stage": "Stage IA",
        "evaluations": [
          {"option": "Radiation Therapy", "approved": true, "confidence": 0.78, "reason": "Aprobado por validador mock"},
          {"option": "Endocrine Therapy", "approved": true, "confidence": 0.78, "reason": "Aprobado por validador mock"}
        ]
      }
    ],
    "summary": {"approved_count": 4, "rejected_count": 0},
    "model": {"name": "mock-validator", "version": "0.1.0", "note": "Reemplazar por servicio ML real"},
    "timestamp": 1791434126
  }
}
```

- `recommendations`: lo que devolvió el recomendador (ya sin tratamientos quirúrgicos, porque `surgery_preference` era `"No"`).
- `final_recommendations`: lo que aprobó el validador. Es lo que muestra la página.
- `validation_details` y `summary`: la evaluación de cada tratamiento. El validador actual es **simulado** (ver [MICROSERVICIOS.md](MICROSERVICIOS.md#servicesml_validator_servicepy-validador-simulado)).

**Response:** 200 OK, fallido
```json
{
  "job_id": "prueba-fallo-recomendador",
  "status": "failed",
  "error": "recommender: Mensaje inválido: faltan job_id o TNM",
  "result": {
    "job_id": "prueba-fallo-recomendador",
    "status": "failed",
    "error": "recommender: Mensaje inválido: faltan job_id o TNM",
    "timestamp": 1791433898
  }
}
```

El prefijo de `error` indica qué servicio falló: `recommender:` o `ml-validator:`.

**Response:** 404 Not Found (el `job_id` no existe; los trabajos se guardan en memoria y se pierden al reiniciar la API)
```json
{"error": "job_id not found"}
```

---

## 6. GET `/pipeline/health`
Indica si la API puede conectarse a RabbitMQ y si su consumidor de resultados está activo.

**Response:** 200 OK
```json
{
  "consumer": "running",
  "queues": {
    "recommendation_request": "tnm.recommendation.request",
    "validation_result": "tnm.validation.result"
  },
  "rabbitmq": "up"
}
```

`rabbitmq` vale `"down"` si no hay conexión. No comprueba Neo4j ni los microservicios.

---

## 7. GET `/pipeline/debug`
Devuelve todos los trabajos guardados en memoria, con su resultado completo. Pensado para depuración: no tiene autenticación ni límite de tamaño.

**Response:** 200 OK
```json
{
  "total_jobs": 5,
  "timestamp": 1791434130,
  "jobs": {
    "2f501371-e88b-4d59-8034-30f4d47f28ef": {
      "status": "completed",
      "updated_at": 1791434126,
      "result": {"...": "mismo formato que en /pipeline/result"}
    }
  }
}
```

---

## 8. POST `/entradas`
Devuelve el JSON recibido. Es un endpoint de prueba de versiones anteriores: la página ya no lo llama.

**Response:** 201 Created
```json
{"datos": {"prueba": 1}, "mensaje": "Datos recibidos correctamente"}
```

**Response:** 400 Bad Request (sin cuerpo JSON)
```json
{"error": "No JSON body provided"}
```

---

## Ejemplos con PowerShell

```powershell
# Consulta directa
Invoke-RestMethod "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0" | ConvertTo-Json -Depth 10

# Pipeline: enviar y consultar el resultado
$body = @{ t_label = "T1"; n_label = "N0"; m_label = "M0"; context = @{ surgery_preference = "No" } } | ConvertTo-Json
$job = Invoke-RestMethod -Method Post -Uri http://localhost:5000/pipeline/submit -Body $body -ContentType "application/json"
Start-Sleep -Seconds 2
Invoke-RestMethod "http://localhost:5000/pipeline/result/$($job.job_id)" | ConvertTo-Json -Depth 10
```

Para una prueba completa del pipeline: `.\scripts\test-pipeline.ps1`.

## Ejemplos con cURL

```bash
# Consulta directa
curl "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0"

# Pipeline: enviar
curl -X POST http://localhost:5000/pipeline/submit \
  -H "Content-Type: application/json" \
  -d '{"t_label":"T1","n_label":"N0","m_label":"M0"}'

# Pipeline: consultar el resultado (sustituir <job_id>)
curl http://localhost:5000/pipeline/result/<job_id>
```

## Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - `/entradas` recibió el JSON |
| 202 | Accepted - Trabajo enviado al pipeline |
| 400 | Bad Request - Parámetros inválidos o faltantes |
| 404 | Not Found - Sin datos para esa combinación TNM, o `job_id` inexistente |
| 500 | Internal Server Error - Error inesperado en la API (ver `docker compose logs api`) |
| 502 | Bad Gateway - Solo a través del proxy (`:5500/api`): la API no está en marcha |
| 503 | Service Unavailable - RabbitMQ no disponible al enviar al pipeline |
