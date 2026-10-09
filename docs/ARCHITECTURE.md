# Arquitectura del Proyecto

## Estructura de Carpetas

```
biomedicos/
├── backend/                     # API Flask (servicio 'api')
│   ├── __init__.py
│   ├── api.py                   # Endpoints, publicación en RabbitMQ y consumidor de resultados
│   ├── config.py                # Configuración leída de variables de entorno
│   └── run_waitress.py          # Arranque del servidor Waitress (puerto 5000)
│
├── services/                    # Microservicios que consumen de RabbitMQ
│   ├── recommender_service.py   # Servicio 'recommender': consulta Neo4j
│   └── ml_validator_service.py  # Servicio 'ml-validator': validador simulado
│
├── frontend/                    # Página web (servicio 'frontend', servida por nginx)
│   ├── index.html
│   ├── css/
│   │   ├── stilous.scss         # Fuente SCSS de los estilos globales
│   │   ├── stilous.css          # Estilos globales compilados
│   │   └── index-custom.css     # Estilos de la página principal
│   ├── js/
│   │   ├── main.js              # Interfaz: modales, perfil del paciente, tratamientos desplegables
│   │   └── entradas.js          # Consulta: envío al pipeline, sondeo del resultado y presentación
│   └── modals/                  # Formularios cargados al abrir la página
│       ├── modal-personal.html
│       ├── modal-heredofamiliar.html
│       ├── modal-tumoral.html
│       └── modal-ihc.html
│
├── nginx/
│   └── default.conf             # Configuración de nginx: sirve frontend/ y reenvía /api/ a la API
│
├── data/                        # Fuente de los datos de Neo4j (ver DATABASE.md)
│   ├── nodos.csv
│   └── relaciones.csv
│
├── scripts/
│   ├── import_csv.py            # Valida e importa los CSV (servicio 'seed')
│   └── test-pipeline.ps1        # Prueba de extremo a extremo del pipeline
│
├── tests/
│   └── test_api.py              # Tests de la API (pytest)
│
├── docs/                        # Documentación
│
├── docker-compose.yml           # Definición de todos los servicios
├── Dockerfile                   # Imagen 'biomedicos-app' (api, seed, recommender, ml-validator)
├── requirements.txt             # Dependencias de Python
├── requirements-dev.txt         # Dependencias de los tests
├── .env.example                 # Plantilla de configuración (opcional)
├── CHANGELOG.md
└── README.md
```

## Componentes

| Servicio | Imagen | Código | Puerto en el equipo |
|----------|--------|--------|---------------------|
| `frontend` | `nginx:alpine` | `frontend/`, `nginx/default.conf` | 5500 (`FRONTEND_PORT`), accesible desde la red |
| `api` | `biomedicos-app` | `backend/` | 5000 (`API_PORT`), solo `127.0.0.1` |
| `recommender` | `biomedicos-app` | `services/recommender_service.py` | — |
| `ml-validator` | `biomedicos-app` | `services/ml_validator_service.py` | — |
| `seed` | `biomedicos-app` | `scripts/import_csv.py` | — |
| `rabbitmq` | `rabbitmq:3-management` | — | 5672, 15672, solo `127.0.0.1` |
| `neo4j` | `neo4j:5` | — | 7474, 7687, solo `127.0.0.1` |

`api`, `recommender`, `ml-validator` y `seed` comparten la imagen `biomedicos-app`, construida una sola vez desde el `Dockerfile`; cada uno arranca con su propio comando.

Solo la aplicación web es accesible desde otros equipos de la red. Los demás puertos se publican en `127.0.0.1`, de modo que la API, Neo4j y RabbitMQ solo responden en el propio servidor; dentro de Docker, los servicios se comunican por su red interna sin depender de esos puertos.

Ver [MICROSERVICIOS.md](MICROSERVICIOS.md) para el detalle de cada componente y el formato de los mensajes.

## Flujos de Datos

### Consulta (flujo normal)

```
Página (entradas.js)
    ↓ POST /api/pipeline/submit
nginx (frontend) ── reenvía /api/... ──→ API (api.py)
    ↓ publica en tnm.recommendation.request
Recomendador ── consulta ──→ Neo4j
    ↓ publica en tnm.validation.request
Validador (simulado)
    ↓ publica en tnm.validation.result
API (hilo consumidor) ── guarda el resultado en memoria
    ↑ GET /api/pipeline/result/<job_id> cada 2 s
Página ── muestra hasta 3 estadios con pruebas y tratamientos
```

### Si la evaluación no se completa

Si el pipeline no completa la consulta (error al enviar, trabajo `failed` o 60 s sin resultado), la página muestra el aviso «No se pudo completar la evaluación» y no presenta tratamientos: solo se muestran resultados que han pasado por el recomendador y el validador. Ver [MICROSERVICIOS.md](MICROSERVICIOS.md#si-la-evaluación-no-se-completa).

### Arranque (`docker compose up`)

1. `neo4j` y `rabbitmq` arrancan y esperan a superar sus comprobaciones de salud.
2. `seed` valida los CSV y los importa si Neo4j está vacío; después termina.
3. `api` y `recommender` arrancan cuando `seed` termina bien; `ml-validator`, cuando RabbitMQ está listo.
4. `frontend` arranca después de `api`.

## Configuración

La configuración se pasa a los contenedores como variables de entorno desde `docker-compose.yml`, y `backend/config.py` las lee con valores por defecto.

| Dónde | Qué |
|-------|-----|
| `.env` (opcional) | `NEO4J_USER`, `NEO4J_PASSWORD`, `FRONTEND_PORT`, `API_PORT` (ver `.env.example`) |
| `docker-compose.yml` | URIs de Neo4j y RabbitMQ, nombres de las colas, puertos internos |
| `nginx/default.conf` | Ruta `/api/`, destino del proxy y bloqueo de `/api/pipeline/debug` |
| `frontend/js/entradas.js` | `API_URL = '/api'` (ruta relativa: no depende del host ni del puerto) |

## Dependencias Principales

**Python** (`requirements.txt`, imagen `python:3.11-slim`):

| Paquete | Versión | Uso |
|---------|---------|-----|
| flask | 3.0.0 | Framework de la API |
| flask-cors | 4.0.0 | Cabeceras CORS para llamadas directas a la API |
| waitress | 2.1.2 | Servidor WSGI |
| neo4j | 5.15.0 | Driver oficial de Neo4j (API, recomendador e importación) |
| pika | 1.3.2 | Cliente de RabbitMQ |
| pytest | 8.3.3 | Tests (`requirements-dev.txt`) |

**Servicios** (imágenes de Docker): `neo4j:5`, `rabbitmq:3-management`, `nginx:alpine`.

**Frontend** (cargadas desde CDN): Bootstrap 5.3.3, jQuery 3.6.0, Toastr, Font Awesome 6.4.0.

## Testing

```powershell
# Tests de la API (requieren el proyecto levantado, con datos en Neo4j)
docker compose run --rm api python -m pytest tests -v

# Prueba de extremo a extremo del pipeline
.\scripts\test-pipeline.ps1
```

Los tests (`tests/test_api.py`) cubren los endpoints `/`, `/get_stage_info`, `/labels/*` y `/entradas`. El pipeline se prueba con `test-pipeline.ps1`.

## Próximos Pasos

Ver [MICROSERVICIOS.md](MICROSERVICIOS.md#mejoras-futuras) y el roadmap del [CHANGELOG](../CHANGELOG.md#roadmap---próximas-versiones).
