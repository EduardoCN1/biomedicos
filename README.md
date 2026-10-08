# Proyecto Biomedicos

Aplicación Flask+Neo4j para consultoría de estadios oncológicos (TNM), pruebas recomendadas y opciones de tratamiento para cáncer de mama.

## Resumen Rápido
__________________________________________________________________________
| Aspecto          |    Detalle                                           |
|------------------|------------------------------------------------------|
| **Stack**        | Flask 3.0 + Neo4j 5.x + RabbitMQ + Bootstrap 5       |
| **Lenguajes**    | Python (backend), JavaScript/HTML5 (frontend)        |
| **Base Datos**   | Neo4j (graph database)                               |
| **Mensajería**   | RabbitMQ (message broker) - Comunicación asíncrona   |
| **Ejecución**    | Docker Compose (Windows, Linux o macOS)              |
| **Python**       | 3.11 (incluido en la imagen Docker)                  |

## Arquitectura de Microservicios y Mensajería

El proyecto implementa una **arquitectura de microservicios desacoplados** que se comunican a través de **RabbitMQ**:

```
┌─────────────┐
│   Frontend  │ (HTML + JS)
│ (puerto5500)│
└──────┬──────┘
       │ HTTP requests
       ▼
┌──────────────────────────────────────────────────┐
│          API Principal (biomedicos-api)          │
│          Flask + Neo4j (puerto 5000)             │
│  • Recibe solicitudes del frontend               │
│  • Publica eventos a RabbitMQ (validación, etc)  │
│  • Enruta respuestas al frontend                 │
└──────────────┬───────────────────────────────────┘
               │ RabbitMQ Pub/Sub
               ▼
      ┌────────────────┐
      │   RabbitMQ     │ (puerto 15672 - admin)
      │  (message      │ (puerto 5672 - AMQP)
      │   broker)      │
      └────┬───────┬──┘
           │       │
    ┌──────▼─┐   ┌─▼────────┐
    │Recomm. │   │Validator │
    │Service │   │Service   │
    │(ML)    │   │(ML)      │
    │5001    │   │5002      │
    └────────┘   └──────────┘
       ↑               ↑
       └───► Neo4j ◄───┘
```

### Microservicios

| Servicio | Puerto | Función | Tecnología |
|----------|--------|---------|------------|
| **API** | 5000 | Endpoint principal, orquestación | Flask + Neo4j |
| **Recommender** | 5001 | Genera recomendaciones ML | Python + scikit-learn/TensorFlow |
| **ML Validator** | 5002 | Valida patrones oncológicos | Python + ML models |
| **RabbitMQ** | 5672/15672 | Message broker, comunicación async | RabbitMQ |
| **Neo4j** | 7474/7687 | Base de datos de grafos | Neo4j |

### Flujo de Mensajería

1. **Usuario envía formulario** → Frontend
2. **API recibe datos** → Valida y publica a cola `requests` en RabbitMQ
3. **Validator consume** → Valida patrones, publica resultado a cola `validations`
4. **Recommender consume** → Genera recomendaciones, publica a cola `recommendations`
5. **API consume respuestas** → Agrega datos de Neo4j y envía al frontend
6. **Frontend recibe** → Muestra resultados al usuario

## Instalación

El proyecto se ejecuta completo con Docker Compose: no hace falta instalar Python, Neo4j ni Node.js.

**Requisitos:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop) (en Windows usa WSL2), con al menos 4 GB de RAM asignados.
- Git.
- Unos 2 GB de disco para las imágenes.
- Conexión a internet: la primera vez se descargan las imágenes, y la página carga Bootstrap, jQuery y Toastr desde CDN.

**Pasos:**
```powershell
git clone https://github.com/EduardoCN1/biomedicos.git
cd biomedicos
docker compose up -d --build
```

La primera vez tarda unos minutos. Compose construye la imagen del proyecto, espera a que Neo4j y RabbitMQ estén listos y el servicio `seed` carga los datos de `data/*.csv` en Neo4j automáticamente.

Cuando termine, abre **http://localhost:5500**.

| Servicio | Dirección | Credenciales |
|----------|-----------|--------------|
| Aplicación web | http://localhost:5500 | — |
| API | http://localhost:5000 | — |
| Neo4j Browser | http://localhost:7474 | `neo4j` / `password` (o los de tu `.env`) |
| RabbitMQ (administración) | http://localhost:15672 | `guest` / `guest` |

El archivo `.env` es opcional; solo hace falta para cambiar la contraseña de Neo4j o el puerto de la aplicación web (ver [Variables de Entorno](#variables-de-entorno)).

Ver [DOCKER.md](docs/DOCKER.md) para la guía completa.

## Uso Diario

```powershell
docker compose up -d            # Arrancar (los datos de Neo4j se conservan entre arranques)
docker compose down             # Detener
docker compose logs -f          # Ver los registros de todos los servicios
docker compose ps               # Ver el estado de los servicios
```

Al aplicar cambios:
- **Frontend** (`frontend/`): basta con recargar el navegador.
- **Backend o microservicios** (`backend/`, `services/`, `scripts/`, `requirements.txt`): `docker compose up -d --build`.

## Estructura de Carpetas

Ver [ARCHITECTURE.md](docs/ARCHITECTURE.md) para detalle completo.
```
biomedicos/
├── backend/                 # API Flask (servida con Waitress)
│   ├── api.py
│   ├── config.py
│   ├── run_waitress.py
│   └── __init__.py
├── services/                # Microservicios que consumen de RabbitMQ
│   ├── recommender_service.py
│   └── ml_validator_service.py
├── frontend/                # HTML + JavaScript + CSS (servido con nginx)
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── modals/
├── data/                    # Datos de Neo4j
│   ├── nodos.csv
│   └── relaciones.csv
├── scripts/
│   ├── import_csv.py        # Carga los CSV en Neo4j (lo ejecuta el servicio seed)
│   └── test-pipeline.ps1    # Prueba de extremo a extremo del pipeline
├── tests/
│   └── test_api.py
├── docs/                    # Documentación
├── docker-compose.yml       # Definición de todos los servicios
├── Dockerfile               # Imagen de la API y los microservicios
├── .env.example
├── requirements.txt
├── requirements-dev.txt     # Dependencias de los tests (pytest)
└── README.md
```

###  Novedades v2.3 (Mayo 2026)
- **Arquitectura de Microservicios**: Comunicación asíncrona con RabbitMQ
- **API Principal**: Servicio Flask centralizado con validación de datos
- **Recomendador (ML)**: Microservicio que genera recomendaciones basadas en ML
- **Validador de ML**: Microservicio que valida patrones oncológicos
- **Message Broker**: RabbitMQ para orquestar comunicación entre servicios

###  Novedades v2.2 (Marzo 2026)
- **Reestructuración Frontend**: CSS, JS y modales en archivos separados
- **Interfaz Mejorada**: Diseño moderno con animaciones y validaciones
- **Modales Dinámicos**: Carga on-demand de formularios
- **Better UX**: Spinner de carga, notificaciones, perfil en tiempo real

Ver [REESTRUCTURACION_FRONTEND.md](docs/REESTRUCTURACION_FRONTEND.md) para detalles completos.

## Documentación Completa

Consulte la documentación apropiada según su caso de uso:

  - **[DOCKER.md](docs/DOCKER.md)** - Instalación y uso del proyecto con Docker Compose
  - **[MICROSERVICIOS.md](docs/MICROSERVICIOS.md)** - Arquitectura detallada de microservicios y RabbitMQ
  - **[DATABASE.md](docs/DATABASE.md)** - Gestión de datos Neo4j (CSV, dump, backups)
  - **[API.md](docs/API.md)** - Referencia de endpoints con ejemplos cURL y PowerShell
  - **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Flujos de datos y dependencias del proyecto
  - **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Solución de problemas avanzados
  - **[DIAGRAMAS.md](docs/DIAGRAMAS.md)** - Diagramas Mermaid de arquitectura
  - **[REESTRUCTURACION_FRONTEND.md](docs/REESTRUCTURACION_FRONTEND.md)** - Mejoras UI/UX v2.2 (Marzo 2026)

## Endpoints Disponibles

  | GET                   |       POST                     |
  |-----------------------|--------------------------------|
  | `GET /`               | `POST /entradas`               |
  | `GET /labels/t`       |     (recibir datos formulario) |
  | `GET /labels/n`       |                                | 
  | `GET /labels/m`       |                                | 
  | `GET /get_stage_info?t_label=T2&n_label=N1&m_label=M0` | 
  
  >**Ver** [API.md](docs/API.md) **para ejemplos y respuestas.**

## Variables de Entorno

  El archivo `.env` es **opcional**: sin él se usan los valores por defecto. Para personalizarlo, copia la plantilla y edítala:

  ```powershell
  cp .env.example .env
  ```

  | Variable | Por defecto | Uso |
  |----------|-------------|-----|
  | `NEO4J_USER` | `neo4j` | Usuario de Neo4j |
  | `NEO4J_PASSWORD` | `password` | Contraseña de Neo4j (mínimo 8 caracteres) |
  | `FRONTEND_PORT` | `5500` | Puerto de la aplicación web en tu equipo |

  El resto de la configuración (URIs, colas de RabbitMQ y demás puertos) está fijada en `docker-compose.yml`.

  **Notas:**
  - La contraseña de Neo4j solo se aplica la primera vez que se crea su volumen. Si la cambias después, recrea el volumen con `docker compose down -v` (los datos se vuelven a cargar desde los CSV).
  - No commitear `.env` a Git (contiene credenciales).

## Tests

  ```powershell
  # Tests de la API (con el proyecto levantado; usan Neo4j con datos)
  docker compose run --rm api python -m pytest tests -v

  # Prueba de extremo a extremo del pipeline (PowerShell)
  .\scripts\test-pipeline.ps1
  ```

## Gestión de Datos Neo4j

  Los datos se cargan solos: al levantar el proyecto, el servicio `seed` importa `data/nodos.csv` y `data/relaciones.csv` si Neo4j está vacío. Si ya tiene datos, no hace nada.

  Para volver a cargarlos desde cero (por ejemplo, después de editar los CSV):

  ```powershell
  docker compose down -v      # Borra el volumen de Neo4j
  docker compose up -d
  ```

  > **Ver [DATABASE.md](docs/DATABASE.md)** para copias de seguridad, restauración y consultas de verificación.

## Desarrollo

  ### Agregar nuevo endpoint

  Editar `backend/api.py`:

  ```python
  @app.route('/mi_endpoint', methods=['GET'])
  def mi_endpoint():
      # Tu lógica aquí
      return {'resultado': 'OK'}, 200
  ```

  Después, reconstruir: `docker compose up -d --build`.

  ### Modificar frontend

  Editar `frontend/index.html` y `frontend/js/entradas.js`, y recargar el navegador:

  ```javascript
  // entradas.js - Añadir función AJAX
  function miFunc() {
      $.ajax({
          url: 'http://127.0.0.1:5000/mi_endpoint',
          ...
      });
  }
  ```

  ### Agregar dependencias

  Editar `requirements.txt` (o `requirements-dev.txt` para herramientas de test) y reconstruir:
  ```powershell
  docker compose up -d --build
  ```

## Solucionar Problemas

  ### Un puerto ya está en uso
  - **Aplicación web (5500):** cambia `FRONTEND_PORT` en `.env` y vuelve a ejecutar `docker compose up -d`.
  - **Otros puertos (5000, 5672, 7474, 7687, 15672):** libera el puerto cerrando el programa que lo usa. En macOS, el 5000 lo ocupa el Receptor AirPlay (se desactiva en Ajustes del Sistema → General → AirDrop y Handoff).

  ### "Cannot connect to the Docker daemon"
  Docker Desktop no está abierto. Ábrelo, espera a que indique que está en ejecución y repite el comando.

  ### La página carga pero no muestra tratamientos
  - Comprueba que todos los servicios estén en marcha: `docker compose ps -a` (`seed` debe aparecer como `Exited (0)`).
  - Revisa los registros: `docker compose logs api recommender ml-validator`.

  > **Ver** [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) **para más soluciones.**

## Próximas Mejoras
- [ ] Autenticación JWT
- [ ] Frontend React/Vue
- [ ] Más tests (cobertura 90%+)
- [ ] CI/CD (GitHub Actions)


## Contacto y Licencia
Proyecto de práctica sobre arquitectura de software biomedico.

---
**Última actualización:** 2026-03-04
**Versión:** 2.2 (Reestructuración Frontend + Mejoras UI/UX)
