# Changelog

## Versión 2.1 - Mejoras de Documentación y Flujo Diario (2026-02-13)

### Nuevas Funcionalidades

**Documentación de Uso Diario:**
-  [USO_DIARIO.md](docs/USO_DIARIO.md) - Guía completa para uso día a día (después del setup inicial)
  - Checklist rápido de 5 minutos
  - 6 pasos detallados con outputs esperados
  - Troubleshooting específico para problemas diarios
  - Tips productivos (múltiples terminales, atajos)

**Gestión de Base de Datos:**
-  [DATABASE.md](docs/DATABASE.md) - Guía completa de gestión de datos Neo4j
  - Opción A: Importar desde CSV (desarrollo)
  - Opción B: Restaurar desde Dump (producción/respaldo)
  - Cómo crear backups regulares
  - Cómo limpiar la base de datos
  - Decisión rápida: ¿Qué método usar?
  
###  Mejoras

**README.md:**
- Separación clara entre "Primera Vez (Setup Completo)" y "Uso Diario"
- Documentación de dos métodos para poblar Neo4j (CSV vs Dump)
- Nueva sección "Gestión de Datos Neo4j" con opciones A y B
- Problema de "terminal vieja" documentado y solucionado

**backend/run_waitress.py:**
- Agregado `sys.path.insert()` para resolver imports desde carpeta raíz
- Mensajes informativos al iniciar servidor
- Mejor manejo de errores de conexión Neo4j

**Troubleshooting Mejorado:**
- Documentado: "Terminal no detecta Neo4j si fue abierta antes de iniciar Neo4j"
- Solución clara: Cerrar terminales viejas → Abrir terminal NUEVA
- Agregado problema común "Unable to retrieve routing information"

###  Correcciones

**Flujo de Inicio:**
- Problema identificado: Terminales abiertas antes de Neo4j no detectan el estado "Running"
- Solución: Documentado en USO_DIARIO.md y README.md
- Agregado advertencia  en secciones relevantes

**Confusión CSV vs Dump:**
- Clarificado: NO necesitas importar CSV si ya tienes un dump
- Documentado: Cuándo usar cada método
- Agregada tabla de decisión rápida

###  Cambios en Documentación

| Archivo            | Cambio                | Impacto                              |
|--------------------|-----------------------|--------------------------------------|
| USO_DIARIO.md      | Creado (348 líneas)   | Alto - Guía esencial para uso diario |
| DATABASE.md        | Creado (280 líneas)   | Alto - Gestión completa de datos     |
| README.md          | Actualizado           | Medio - Mejor claridad setup vs uso  |
| TROUBLESHOOTING.md | Referencias agregadas | Bajo - Más contexto                  |

###  Impacto en Usuarios

**Para Nuevos Desarrolladores:**
- Ahora entienden claramente la diferencia entre setup inicial y uso diario
- Saben elegir entre CSV o dump para poblar Neo4j
- Tienen checklist rápido de 5 minutos

**Para Desarrolladores Existentes:**
- Ya no confusión sobre si ejecutar `setup.ps1` cada vez
- Solución documentada al problema de "terminal vieja"
- Guía de backups para proteger datos

---

## Versión 2.0 - Reorganización Profesional (2026-02-13)

### Nuevas Funcionalidades

**Estructura de Carpetas:**
-  Reorganización completa a estructura profesional (Opción A)
-  Separación clara: backend/ | frontend/ | data/ | scripts/ | tests/ | docs/

**Documentación:**
-  [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Diagramas de flujo
-  [API.md](docs/API.md) - Documentación de endpoints (30+ ejemplos)
-  [SETUP.md](docs/SETUP.md) - Guía de instalación completa (15 pasos)
-  [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Soluciones a 10 problemas comunes
-  [DIAGRAMAS.md](docs/DIAGRAMAS.md) - 5 diagramas Mermaid de arquitectura
-  [ESTADO_FINAL.md](docs/ESTADO_FINAL.md) - Resumen de cambios
-  [README.md](README.md) - Reescrito para nueva estructura

**Scripts de Automatización:**
-  [scripts/setup.ps1](scripts/setup.ps1) - Instala Miniforge + dependencias (PowerShell)
-  [scripts/run.ps1](scripts/run.ps1) - Arranca servidor con .env loading (PowerShell)
-  [scripts/import_csv.py](scripts/import_csv.py) - Importa CSV → Neo4j (mejorado)

**Testing:**
-  [tests/test_api.py](tests/test_api.py) - 8 test cases con pytest

**Configuración:**
-  [.env.example](.env.example) - Template de variables de entorno
-  [backend/config.py](backend/config.py) - Gestión centralizada de configuración
-  [.gitignore](.gitignore) - Excluye .env, cache, credenciales

###  Cambios en Backend

**backend/api.py:**
- Importa configuración desde `backend.config` en lugar de `os.getenv()`
- Mejora: Centralización de credenciales

**backend/run_waitress.py:**
- Corregido: Import de `API` → `backend.api`
- Corregido: Puerto default 8080 → 5000
- Mejora: Configurable via ENV

**backend/config.py (NUEVO):**
- Lee NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD de .env
- Lee HOST, PORT, ENVIRONMENT de variables
- Fallbacks sensatos para desarrollo

###  Cambios en Frontend

**frontend/index.html:**
- Corregido: Ruta Bootstrap `../node_modules/...`
- Corregido: Script src `js/entradas.js`
- Mejora: Estructurado en carpeta separada

**frontend/js/entradas.js:**
```javascript
// Ya validado y funcional desde v1.5
// Cambios documentados en ESTADO_FINAL.md
```

###  Cambios en Datos

**data/ (NUEVO):**
- `nodos.csv` - Ya presente (sin cambios)
- `relaciones.csv` - Ya presente (sin cambios)
- `backups/` - Carpeta para dumps Neo4j

###  Cambios en Configuración

**.env.example (NUEVO):**
```ini
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
HOST=0.0.0.0
PORT=5000
ENVIRONMENT=development
```

**.gitignore (NUEVO):**
- Excluye `.env` (credenciales)
- Excluye `__pycache__/`, `*.pyc`
- Excluye `node_modules/`
- Excluye logs y dumps

###  Cambios en Dependencias

**requirements.txt:**
- Sin cambios en versiones
- Confirmado: py2neo 2021.2.4, Flask 3.0.0, Neo4j 5.15.0

### Validaciones Completadas

-  Backend arranca sin import errors
-  Frontend carga sin 404s
-  Todos los endpoints funcionan
-  API responde JSON válido
-  Credenciales se leen desde .env
-  Scripts PowerShell son ejecutables

---

## Versión 1.5 - Últimas Correcciones (Sesiones Anteriores)

### Correcciones Previas

**entradas.js:**
- Agregadas 5 funciones faltantes: updateAgeOutput(), updateWeightOutput(), updateHeightOutput(), updateTumorCount(), updateNodeCount()
- Corregidos selectores: #Talla → #talla, #Peso → #peso
- Actualizada URL AJAX: hardcoded IP → http://127.0.0.1:5000

**API/API.py:**
- Corregida respuesta de /get_stage_info: objeto con keys numéricas → array de objetos
- Los endpoint /labels/t, /labels/n, /labels/m funcionan correctamente

**run_waitress.py:**
- Cambio de puerto: 8080 → 5000 (sin conflictos)

---

## Versión 1.0 - Setup Inicial (Primera Sesión)

### Instalación Inicial

-  Instalación de Miniforge + Python 3.11
-  Creación entorno conda `biomedicos`
-  Resolución de dependencias (numpy/pandas via conda)
-  Instalación requirements.txt (py2neo, Flask, etc)
-  Conexión a Neo4j 5.x verificada
-  Primeros tests de API exitosos

### Pruebas Funcionales

-  GET / - Devuelve "En ejecución"
-  GET /get_stage_info?t_label=T2&n_label=N1&m_label=M0 - Devuelve tratamientos
-  GET /labels/* - Devuelve listas de etiquetas
-  POST /entradas - Acepta datos desde formulario
-  frontend/index.html carga sin errores
-  Formulario interactivo funciona

---

## Roadmap - Próximas Versiones

### v2.1 (Planeado)
- [ ] Docker + docker-compose para Neo4j + App
- [ ] GitHub Actions CI/CD (tests automáticos)
- [ ] Validación de tipos con TypeScript (frontend)

### v2.5 (Planeado)
- [ ] Frontend React SPA
- [ ] Autenticación JWT
- [ ] Endpoints POST para guardar datos

### v3.0 (Futuro)
- [ ] Migración a FastAPI
- [ ] Modelo Machine Learning para predicciones
- [ ] WebSockets para actualizaciones en tiempo real

## Guía de Actualización v1.5 → v2.0

### Para Desarrolladores Existentes:

```powershell
# 1. Actualizar estructura (copiar archivos manualmente)
# - Copiar backend/api.py, backend/config.py, etc.

# 2. Crear .env desde .env.example
Copy-Item .env.example .env

# 3. Actualizar rutas en scripts personalizados
# - Cambiar: API/API.py → backend/api.py
# - Cambiar: API/run_waitress.py → backend/run_waitress.py

# 4. Revisar importes si tienes código adicional
# - Cambiar: from API import app → from backend.api import app

# 5. Usar nuevos scripts
.\scripts\setup.ps1
.\scripts\run.ps1
```

### Para Nuevos Desarrolladores:

```powershell
# Simplemente:
git clone <repo>
.\scripts\setup.ps1
.\scripts\run.ps1
```

---

## Notas de Versión


## Contribuciones y Créditos

- **v2.0 Reorganización:** Eduardo Cortes (Restructuring Specialist)
- **v1.5 Correcciones:** Eduardo Cortes (Debugging & Testing)
- **v1.0 Setup:** Eduardo Cortes (Initial Setup & Dependencies)

---

**Última actualización:** 2026-02-13
**Versión actual:** 2.0
**Status:** Listo para producción
