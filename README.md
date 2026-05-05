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
| **OS**           | Windows 10/11, Linux/macOS compatible                |
| **Python**       | 3.11+ (recomendado con Miniforge)                    |

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

## Cómo Instalar el Proyecto

El proyecto se puede instalar de dos formas:

### Opción 1: Con Docker Compose (Recomendado)

Ideal si desea una instalación rápida sin dependencias locales.

**Requisitos:** Docker Desktop

**Pasos:**
```powershell
git clone https://github.com/EduardoCN1/biomedicos.git
cd biomedicos
Copy-Item .env.example .env
docker compose up --build
```

Ver [DOCKER.md](docs/DOCKER.md) para instrucciones completas y guía de uso.

### Opción 2: Instalación Local (Windows)

Ideal si prefiere usar Neo4j Desktop y Conda.

**Requisitos:** Miniforge/Conda, Neo4j 5.x

**Pasos:** Ver [SETUP.md](docs/SETUP.md) para instalación inicial, y [USO_DIARIO_SIN_DOCKER.md](docs/USO_DIARIO_SIN_DOCKER.md) para uso diario.

## Estructura de Carpetas 

Ver [ARCHITECTURE.md](docs/ARCHITECTURE.md) para detalle completo.
```
biomedicos/
├── backend/                 # Servidor Flask + Neo4j
│   ├── api.py
│   ├── config.py
│   ├── run_waitress.py
│   └── __init__.py
├── frontend/                # HTML + JavaScript + CSS
│   ├── index.html           # Página principal (reestructurada v2.2)
│   ├── css/
│   │   ├── stilous.css      # Estilos globales
│   │   ├── stilous.scss     # Fuente SCSS
│   │   └── index-custom.css # Estilos específicos del index
│   ├── js/
│   │   ├── config.js        # Configuración
│   │   ├── entradas.js      # Lógica de negocio
│   │   └── main.js          # Funciones principales UI
│   └── modals/              # Modales independientes (v2.2)
│       ├── modal-personal.html
│       ├── modal-heredofamiliar.html
│       ├── modal-tumoral.html
│       └── modal-ihc.html
├── data/                    # Datos y backups
│   ├── nodos.csv
│   ├── relaciones.csv
│   └── backups/
├── scripts/                 # Automatización
│   ├── setup.ps1            # Instala dependencias
│   ├── run.ps1              # Arranca servidor
│   └── import_csv.py        # Importa CSV → Neo4j
├── tests/
│   └── test_api.py
├── docs/                    # Documentación
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── SETUP.md
│   └── REESTRUCTURACION_FRONTEND.md  #  Nueva (v2.2)
├── .env.example
├── requirements.txt
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

## Inicio Rápido

###  Primera Vez (Setup Completo)

  **1. Instalar Dependencias**
  ```powershell
  .\scripts\setup.ps1
  ```

  **2. Configurar Variables de Entorno**
  ```powershell
  Copy-Item .env.example .env
  # Editar .env con credenciales Neo4j reales
  ```

  **3. Iniciar Neo4j Desktop**
  - Abrir Neo4j Desktop
  - Seleccionar proyecto → Click "Start" (botón verde)
  - Esperar hasta ver "Running" ✓

  **4. Poblar Base de Datos (solo primera vez)**
  
  Tienes **dos opciones** (elige una):
  
  **Opción A: Importar desde CSV**
  ```powershell
  python .\scripts\import_csv.py
  ```
  
  **Opción B: Restaurar desde dump** (si tienes un archivo `.dump`)
  ```powershell
  # Ver guía completa en docs/DATABASE.md
  neo4j-admin database load neo4j --from-path="data\backups" --overwrite-destination=true
  ```
  
  > **Nota:** Si ya tienes datos en Neo4j, omite este paso. Ver [DATABASE.md](docs/DATABASE.md) para más detalles.

  **5. Arrancar Servidor**
  ```powershell
  .\scripts\run.ps1
  # El servidor estará en http://localhost:5000
  ```

  **6. Abrir Frontend**
  - Click derecho en `frontend/index.html` → "Open with Live Server"
  - O navegar a `http://localhost:5500/frontend/index.html`

###  Uso Diario (Ya hiciste el setup)

  **1. Iniciar Neo4j Desktop**
  - Abrir Neo4j Desktop → Start (botón verde)
  - Esperar "Running" ✓

  **2. Abrir PowerShell NUEVA** 
  ```
  Importante: Si tenías terminales abiertas antes de iniciar Neo4j,
  ciérralas y abre una terminal NUEVA. Esto evita errores de conexión.
  ```

  **3. Arrancar Servidor**
  ```powershell
  .\scripts\run.ps1
  ```

  **4. Abrir Frontend (Live Server)**

  **5. Probar**
  ```powershell
  # En otra terminal
  Invoke-RestMethod http://localhost:5000/
  # Respuesta: "En ejecución"
  ```

### Al Terminar de Trabajar

  **Con Docker:**
  ```powershell
  # Detener contenedores (conserva datos)
  docker compose down
  ```
  Esto libera los puertos y detiene Neo4j/API. Los datos permanecen en el volumen Docker.
  
  Opcionalmente cierra Docker Desktop si no lo usas para otros proyectos.

  **Sin Docker (Local):**
  ```powershell
  # 1. Detener servidor Flask (Ctrl+C en terminal)
  # 2. Detener Neo4j Desktop: Click "Stop" en la aplicación
  # 3. Cerrar Neo4j Desktop si deseas
  ```

### Atajo Rápido (Sin scripts)

  Si prefieres no usar scripts:
  ```powershell
  # 1. Activar entorno
  conda activate biomedicos

  # 2. Arrancar servidor
  python .\backend\run_waitress.py
  ```

## Documentación Completa

Consulte la documentación apropiada según su caso de uso:

  - **[DOCKER.md](docs/DOCKER.md)** - Instalación y uso del proyecto completo con Docker Compose (recomendado)
  - **[SETUP.md](docs/SETUP.md)** - Instalación local sin Docker (Conda + Neo4j Desktop)
  - **[USO_DIARIO_SIN_DOCKER.md](docs/USO_DIARIO_SIN_DOCKER.md)** - Guía de uso diario sin Docker
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

  Crear archivo `.env` (copiar desde `.env.example`):

  ```ini
  # Neo4j
  NEO4J_URI=neo4j://127.0.0.1:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password_here
  
  # API Principal
  HOST=0.0.0.0
  PORT=5000
  ENVIRONMENT=development
  
  # RabbitMQ
  RABBITMQ_HOST=localhost
  RABBITMQ_PORT=5672
  RABBITMQ_USER=guest
  RABBITMQ_PASSWORD=guest
  
  # Microservicios
  RECOMMENDER_HOST=localhost
  RECOMMENDER_PORT=5001
  VALIDATOR_HOST=localhost
  VALIDATOR_PORT=5002
  ```
  **Nota:** No commitear `.env` a Git (contiene credenciales). Usar `.env.example` como template.

## Requisitos

  - Windows/Linux/macOS
  - Python 3.11+
  - Miniforge/Conda (recomendado)
  - Neo4j 5.x ejecutándose
  - 500MB espacio en disco

## Instalar Manualmente (sin script setup.ps1)

  ```powershell
  # Crear y activar entorno
  conda create -n biomedicos python=3.11 -y
  conda activate biomedicos

  # Instalar dependencias (binarias, sin compilar)
  conda install -c conda-forge numpy pandas -y
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt

  # Arrancar servidor
  python .\backend\run_waitress.py
  ```

## Testing (test api)

  ```powershell
  conda activate biomedicos
  pip install pytest
  python -m pytest tests/test_api.py -v
  ```

## Gestión de Datos Neo4j

  ### Opción A: Importar desde CSV
  ```powershell
  python .\scripts\import_csv.py
  ```
  Script automatizado que:
  1. Lee `data/nodos.csv` y `data/relaciones.csv`
  2. Conecta a Neo4j usando credenciales de `.env`
  3. Crea todos los nodos y relaciones en Neo4j

  ### Opción B: Restaurar desde Dump
  ```powershell
  # Neo4j debe estar DETENIDO
  neo4j-admin database load neo4j --from-path="data\backups" --overwrite-destination=true
  # Luego iniciar Neo4j
  ```

  > **Ver [DATABASE.md](docs/DATABASE.md) para guía completa** sobre cuándo usar cada opción, crear backups, y limpiar datos.

## Desarrollo

  ### Agregar nuevo endpoint

  Editar `backend/api.py`:

  ```python
  @app.route('/mi_endpoint', methods=['GET'])
  def mi_endpoint():
      # Tu lógica aquí
      return {'resultado': 'OK'}, 200
  ```

  ### Modificar frontend

  Editar `frontend/index.html` y `frontend/js/entradas.js`:

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

  Editar `requirements.txt`, luego:
  ```powershell
  pip install -r requirements.txt
  ```

## Solucionar Problemas

  ### "Port 5000 already in use"
  ```powershell
  # Cambiar puerto en .env:
  # PORT=5001

  # O matar proceso:
  Get-Process python | Stop-Process -Force
  ```

  ### "Neo4j connection refused" o "Unable to retrieve routing information"
  - **Verificar Neo4j está corriendo:** Abrir Neo4j Desktop → Start → "Running" ✓
  - **Verificar web UI:** `http://localhost:7474`
  - **Validar credenciales en `.env`**
  - **Si ya estaba corriendo:** Cerrar terminal y abrir una NUEVA

  ### "Terminal no detecta Neo4j"
  ```
  IMPORTANTE: Si abriste PowerShell ANTES de iniciar Neo4j,
  la terminal no detectará que Neo4j está activo.
  
  Solución:
  1. Cerrar TODAS las terminales
  2. Abrir PowerShell NUEVA
  3. Ejecutar .\scripts\run.ps1
  ```

  ### "CORS error" en frontend
  - Asegurar backend está corriendo
  - Verificar URL en `entradas.js` es `http://127.0.0.1:5000`

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
