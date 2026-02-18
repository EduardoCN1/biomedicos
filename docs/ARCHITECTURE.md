# Arquitectura del Proyecto

## Estructura de Carpetas

```
biomedicos/
├── backend/              # Lógica del servidor (Flask + Neo4j)
│   ├── __init__.py
│   ├── app.py           # Instancia Flask (importa desde api.py)
│   ├── api.py           # Rutas y lógica principal
│   ├── config.py        # Configuración centralizada (env vars)
│   └── run_waitress.py  # Script de arranque con Waitress
│
├── frontend/            # UI (HTML + JS + CSS)
│   ├── index.html       # Formulario principal
│   ├── js/
│   │   ├── entradas.js  # Lógica de formulario y AJAX
│   │   └── config.js    # Configuración frontend
│   └── css/
│       ├── stilous.css
│       └── stilous.scss
│
├── data/                # Datos y backups
│   ├── nodos.csv
│   ├── relaciones.csv
│   └── backups/         # Dumps de Neo4j
│
├── scripts/             # Utilidades y automatización
│   ├── setup.ps1        # Instala Miniforge + dependencias
│   └── run.ps1          # Arranca el servidor
│
├── tests/               # Tests unitarios
│   └── test_api.py
│
├── docs/                # Documentación
│   ├── ARCHITECTURE.md  # Este archivo
│   ├── API.md           # Documentación de endpoints
│   └── SETUP.md         # Pasos de instalación
│
└── README.md            # Guía principal del proyecto
```

## Flujo de Datos

### Frontend → Backend

```
main.html (formulario)
    ↓ (JavaScript)
entradas.js (recopila datos, envía AJAX)
    ↓ (fetch/AJAX a http://localhost:5000)
backend/api.py (endpoints Flask)
    ↓
backend/config.py (credenciales)
    ↓
Neo4j Database (consultas Cypher)
    ↓
JSON response → Frontend (muestra resultados)
```

## Flujos de Ejecución

### Setup Inicial (Windows)
```powershell
.\scripts\setup.ps1
→ Instala Miniforge + Python3.11
→ Crea entorno conda
→ Instala dependencias (pip install -r requirements.txt)
```

### Ejecutar Servidor
```powershell
.\scripts\run.ps1
→ Activa entorno conda
→ Lee .env (si existe)
→ Arranca Waitress en puerto 5000
```

### Frontend en Desarrollo
```
Live Server en VSCode
→ Abre http://localhost:5500/frontend/index.html
→ entradas.js hace AJAX a http://localhost:5000
```

## Endpoints Principales

| Método | Ruta             | Parámetros                      | Descripción                        |
|--------|------------------|---------------------------------|------------------------------------|
| GET    | `/`              | -                               | Salud (devuelve "En ejecución")    |
| GET    | `/labels/t`      | -                               | Listar todas las etiquetas T       |
| GET    | `/labels/n`      | -                               | Listar todas las etiquetas N       |
| GET    | `/labels/m`      | -                               | Listar todas las etiquetas M       |
| GET    | `/get_stage_info`| `t_label`, `n_label`, `m_label` | Obtener info de tratamientos/tests |
| POST   | `/entradas`      | JSON body                       | Recibir datos del formulario       |

## Configuración (Variables de Entorno)

### .env.example

```ini
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
HOST=0.0.0.0
PORT=5000
ENVIRONMENT=development
```

### Cómo usarla

1. Copiar `.env.example` a `.env`
2. Editar credenciales
3. Ejecutar `scripts/run.ps1` — cargará automáticamente

## Dependencias Principales

| Package    | Versión | Propósito         |
|------------|---------|-------------------|
| Flask      | 3.0.0   | Framework web     |
| neo4j      | 5.15.0  | Driver Neo4j      |
| waitress   | 2.1.2   | Servidor WSGI     |
| pandas     | 2.1.3   | Análisis de datos |
| flask-cors | 4.0.0   | Soporte CORS      |

## Testing

Ejecutar tests (requiere pytest):

```powershell
conda activate biomedicos
pip install pytest
python -m pytest tests/test_api.py -v
```

## Próximos Pasos

1. Dockerizar (Dockerfile + docker-compose.yml)
2. Agregar métodos POST para guardar datos en Neo4j
3. Implementar autenticación (JWT)
4. Crear migración de datos desde CSV
5. Mejorar frontend (React/Vue en futuro)
