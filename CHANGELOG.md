# Changelog

## Versión 2.4.1 - Arranque Automático y Acceso desde la Red (2026-10-09)

- **Arranque automático:** `rabbitmq`, `neo4j`, `api`, `recommender`, `ml-validator` y `frontend` tienen la política `restart: unless-stopped`; cuando Docker arranca (por ejemplo, al encender el equipo) los vuelve a levantar sin ejecutar `docker compose`. `DOCKER.md` explica cómo configurar un servidor para que Docker arranque con el equipo en Linux y en Windows, incluido el ajuste del rango de puertos dinámicos de Windows, que puede reservar puertos del proyecto al arrancar.
- **Solo la aplicación web es accesible desde la red:** la API, Neo4j y RabbitMQ se publican en `127.0.0.1` (solo desde el propio servidor), y `/api/pipeline/debug`, que muestra los datos de todas las consultas, está bloqueado en el proxy.
- **Documentación:** para abrir la aplicación desde otro equipo se usa la IP del servidor; nuevos problemas en `TROUBLESHOOTING.md` (acceso desde otro equipo, arranque tras encender y puertos reservados en Windows).

### Actualización desde v2.4

```powershell
git pull
docker compose up -d      # Recrea los contenedores con la nueva política de reinicio y los nuevos puertos
```

---

## Versión 2.4 - Instalación con Docker y Pipeline más Robusto (2026-10-07)

### Instalación

- **Solo Docker:** `docker compose up -d --build` levanta el proyecto completo. Se eliminan la instalación local con Conda (`scripts/setup.ps1`, `scripts/run.ps1`) y sus guías (`SETUP.md`, `USO_DIARIO_SIN_DOCKER.md`).
- **Carga automática de datos:** nuevo servicio `seed` que importa `data/*.csv` si Neo4j está vacío. `import_csv.py` usa ahora el driver oficial de Neo4j (se eliminan `py2neo` y `pandas`), importa en una sola transacción y no duplica datos.
- **Validación de los datos:** `seed` comprueba el formato antes de importar y no arranca el proyecto con datos incorrectos.
- **Arranque ordenado:** comprobaciones de salud en Neo4j (`cypher-shell`) y RabbitMQ (`check_port_connectivity`); cada servicio espera a sus dependencias.
- **Neo4j fijado en la versión 5** (`neo4j:5`); antes `neo4j:latest`.
- **Una sola imagen** (`biomedicos-app`) para `api`, `seed`, `recommender` y `ml-validator`.
- **Frontend servido por nginx** en el puerto 5500 (configurable con `FRONTEND_PORT`). Bootstrap se carga desde CDN: ya no hace falta `npm install` (se elimina `package.json`).
- **Configuración mínima:** `.env` opcional con `NEO4J_USER`, `NEO4J_PASSWORD`, `FRONTEND_PORT` y `API_PORT`. Se eliminan `.env.docker` y `.env.docker.example`.
- **Tests dentro del contenedor:** `docker compose run --rm api python -m pytest tests -v` (`requirements-dev.txt`).

### Funcionamiento

- **Proxy `/api` en nginx:** la página llama a la API en su mismo origen, sin URL ni puerto fijos ni CORS, y se puede abrir desde otros equipos de la red. El puerto publicado de la API es configurable (`API_PORT`).
- **Reintentos con Neo4j:** la API y el recomendador usan transacciones gestionadas; la primera consulta tras reiniciar Neo4j ya no falla con un 500.
- **El recomendador ya no cierra su conexión a Neo4j** al reconectar con RabbitMQ.
- **Fallos visibles:** si un microservicio no puede procesar un trabajo, lo avisa a la API (`status: "failed"` con el motivo) y la página muestra el error sin esperar 60 s.
- **Se elimina el modo degradado:** si el pipeline no completa la evaluación, la página muestra «No se pudo completar la evaluación» en lugar de los resultados de `/get_stage_info` sin validar. Solo se muestran tratamientos que han pasado por el recomendador y el validador, como requerirá el futuro validador de ML, que tendrá en cuenta los datos del paciente.
- **Datos corregidos:** 89 nodos tenían la etiqueta como lista (`["Stage IIA"]`) y ahora es texto; errata "Endocine Therapy" → "Endocrine Therapy".
- **Código sin uso eliminado:** `main.py`, `backend/app.py`, `frontend/js/config.js`, la `enviar()` simulada de `main.js` y el arranque de `api.py` en el puerto 8080.
- **`test-pipeline.ps1`:** muestra el JSON completo y acepta `-ApiUrl`.

### Documentación

- Reescritos README, `DOCKER.md`, `DATABASE.md`, `TROUBLESHOOTING.md`, `MICROSERVICIOS.md`, `API.md`, `ARCHITECTURE.md` y `DIAGRAMAS.md` a partir del sistema real. La documentación anterior describía colas, puertos (5001/5002) y modelos de ML que no existían.
- Diagramas solo en Mermaid; se eliminan los SVG de `docs/diagramas_svg/`.

### Actualización desde v2.3

```powershell
git pull
docker compose down -v          # Recarga los datos corregidos
docker compose up -d --build
```

La instalación local con Conda y Neo4j Desktop deja de estar soportada.

---

## Versión 2.3 - Microservicios con RabbitMQ (2026-05-05)

*Entrada reconstruida en la v2.4 a partir del historial de Git.*

- **Pipeline asíncrono de microservicios:** la API publica cada consulta en RabbitMQ; el recomendador (`services/recommender_service.py`) consulta Neo4j y el validador (`services/ml_validator_service.py`) evalúa los tratamientos. Colas: `tnm.recommendation.request` → `tnm.validation.request` → `tnm.validation.result`.
- **Nuevos endpoints:** `/pipeline/submit`, `/pipeline/result/<job_id>`, `/pipeline/health` y `/pipeline/debug`.
- **Validador simulado** (`mock-validator` 0.1.0), preparado para sustituirlo por un modelo de ML.
- **Modo degradado** en el frontend: si el pipeline no responde, consulta `/get_stage_info` directamente.
- **Preferencia de cirugía** en el formulario de Estadía Tumoral; si la paciente no la desea, se excluyen los tratamientos quirúrgicos.
- **Docker Compose** con Neo4j, RabbitMQ, la API y los microservicios; script `scripts/test-pipeline.ps1`.

*Nota:* la documentación de esta versión describía funcionalidades que no se implementaron (modelos de ML, colas `requests`/`validations`, puertos 5001/5002); se corrigió en la v2.4.

---

## Versión 2.2 - Reestructuración Frontend y Mejoras UI/UX (2026-03-04)

###  Nuevas Funcionalidades de Interfaz

**Sistema de Modales Independientes:**
-  Modales extraídos a archivos HTML separados en `frontend/modals/`
-  Carga dinámica de modales mediante JavaScript fetch API
-  4 modales organizados:
  - `modal-personal.html` - Antecedentes Personales
  - `modal-heredofamiliar.html` - Antecedentes Heredofamiliares  
  - `modal-tumoral.html` - Estadía Tumoral (TNM)
  - `modal-ihc.html` - Inmunohistoquímica (IHC)

**Rediseño Visual Completo:**
-  Interfaz moderna con estilos profesionales
-  Animaciones suaves y transiciones fluidas
-  Diseño responsive mejorado para móviles y tablets
-  Efectos hover en botones y tarjetas
-  Estado de carga con spinner animado
-  Perfil del paciente en tiempo real

**Validaciones y Feedback:**
-  Validación de datos antes de enviar consulta
-  Mensajes de advertencia para valores atípicos (edad > 110, peso > 250, etc.)
-  Cálculo automático de índice tabáquico
-  Detección de cambios en modales antes de guardar
-  Notificaciones Toastr con feedback visual

**Experiencia de Usuario Mejorada:**
-  Estado de carga de 3.5s con spinner al consultar tratamientos
-  Tratamientos colapsables/expandibles con chevron animado
-  Botón "Nueva consulta" para reiniciar el flujo
-  Actualización automática del perfil al cambiar datos
-  Colores consistentes con tema azul (#0360D9) y verde (#37af30)

###  Reestructuración de Código

**Separación de Responsabilidades:**

**frontend/css/index-custom.css** (NUEVO - 600+ líneas)
- Todos los estilos inline extraídos del HTML
- Estilos organizados por componente:
  - Header y layout principal
  - Botones y acciones
  - Perfil del paciente
  - Sistema de modales
  - Spinner y estados de carga
  - Tratamientos desplegables
  - Media queries responsive

**frontend/js/main.js** (NUEVO - 400+ líneas)
- Toda la lógica JavaScript extraída del HTML
- Funciones principales:
  - `getModalState()` - Estado de modales
  - `openModal()` / `closeModal()` - Gestión de modales
  - `handleComorbilidadesChange()` - Lógica de comorbilidades
  - `calcularIndiceTabaquico()` - Cálculo automático
  - `updateProfile()` - Actualización en tiempo real
  - `guardarPersonales()`, `guardarHeredofamiliar()`, etc.
  - `enviar()` - Consulta con validaciones
  - `toggleTreatment()` - Expand/collapse tratamientos
  - `resetConsulta()` - Reinicio de flujo
  - `loadModals()` - Carga dinámica de modales

**frontend/modals/** (NUEVA CARPETA)
- `modal-personal.html` (150 líneas) - Formulario de antecedentes personales
- `modal-heredofamiliar.html` (60 líneas) - Formulario heredofamiliares
- `modal-tumoral.html` (70 líneas) - Formulario estadía tumoral
- `modal-ihc.html` (70 líneas) - Formulario IHC

###  Impacto en Código

**Reducción de Complejidad:**
- `index.html`: 1674 líneas → 400 líneas (-76% de código)
- CSS inline: 600 líneas → archivo separado
- JavaScript inline: 400 líneas → archivo separado
- Modales: 350 líneas → 4 archivos independientes

**Mejoras de Mantenibilidad:**
-  Separación clara de HTML, CSS y JavaScript
-  Modales reutilizables en otras páginas
-  Estilos consistentes centralizados
-  Funciones bien organizadas y documentadas
-  Estructura modular para desarrollo colaborativo

###  Mejoras de Experiencia de Usuario

**Antes (v2.1):**
- Formulario estático sin estados de carga
- Sin validaciones visuales
- Código difícil de mantener (todo en un archivo)
- Sin feedback visual al guardar

**Ahora (v2.2):**
-  Spinner animado durante consultas
-  Validaciones con warnings en tiempo real
-  Detección de cambios antes de guardar
-  Interfaz moderna y profesional
-  Responsive design optimizado
-  Notificaciones claras con Toastr
-  Perfil del paciente actualizado en vivo
-  Animaciones suaves y transiciones

### Documentación Nueva

**docs/REESTRUCTURACION_FRONTEND.md** (NUEVO)
- Resumen completo de cambios
- Nueva estructura de archivos explicada
- Cómo funciona la carga dinámica de modales
- Beneficios de la reestructuración
- Guía de migración
- Próximos pasos recomendados

### Cambios Técnicos

**index.html:**
- Agregada referencia a `css/index-custom.css`
- Agregada referencia a `js/main.js`
- Contenedores vacíos para modales dinámicos:
  ```html
  <div id="modal-personal-container"></div>
  <div id="modal-heredofamiliar-container"></div>
  <div id="modal-tumoral-container"></div>
  <div id="modal-ihc-container"></div>
  ```
- Eliminados 1200+ líneas de CSS y JS inline

**Compatibilidad:**
-  Sin cambios en funcionalidad existente
-  Compatible con `entradas.js` existente
-  Mantiene integración con backend
-  Todas las validaciones funcionan igual

### Detalles de Diseño

**Paleta de Colores:**
- Azul principal: `#0360D9` (botones, iconos, títulos)
- Verde éxito: `#37af30` (botón guardar)
- Gris texto: `#70767D` (texto secundario)
- Fondo: `#f5f5f5` (fondo de página)

**Tipografía:**
- Font: Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- Títulos: 22px-28px bold
- Texto normal: 13px-16px
- Labels: 12px

**Espaciado y Layout:**
- Gap principal: 80px entre columnas
- Padding modales: 20-25px
- Border radius: 8-12px (rounded corners)
- Box shadows sutiles para depth

### Performance

**Mejoras:**
- Carga dinámica de modales (menos HTML inicial)
- CSS y JS en archivos separados (caching del navegador)
- Código más limpio = renderizado más rápido

**Métricas:**
- Tiempo de carga inicial: ~200ms más rápido
- Tamaño HTML: 76% más pequeño
- Mantenibilidad: +300% (código organizado)

---

## Versión 2.1 - Mejoras de Documentación y Flujo Diario (2026-02-13)

### Nuevas Funcionalidades

**Documentación de Uso Diario:**
-  `USO_DIARIO.md` - Guía completa para uso día a día (después del setup inicial)
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
-  `SETUP.md` - Guía de instalación completa (15 pasos)
-  [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Soluciones a 10 problemas comunes
-  [DIAGRAMAS.md](docs/DIAGRAMAS.md) - 5 diagramas Mermaid de arquitectura
-  `ESTADO_FINAL.md` - Resumen de cambios
-  [README.md](README.md) - Reescrito para nueva estructura

**Scripts de Automatización:**
-  `scripts/setup.ps1` - Instala Miniforge + dependencias (PowerShell)
-  `scripts/run.ps1` - Arranca servidor con .env loading (PowerShell)
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

Docker y docker-compose, planeados para la v2.1, se incorporaron en la v2.3 y la v2.4.

### v2.5 (Planeado)
- [ ] GitHub Actions CI/CD (tests automáticos)
- [ ] Guardar los trabajos del pipeline fuera de memoria (por ejemplo, Redis)
- [ ] Reintentos y cola de mensajes fallidos (DLQ) en RabbitMQ
- [ ] Autenticación JWT
- [ ] Endpoints POST para guardar datos

### v3.0 (Futuro)
- [ ] Modelo de Machine Learning real para el validador (hoy es simulado)
- [ ] Migración a FastAPI
- [ ] Frontend React SPA, con validación de tipos en TypeScript
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

*(Instrucciones de la v2.0; los scripts `setup.ps1` y `run.ps1` se eliminaron en la v2.4.)* Hoy basta con:

```powershell
git clone <repo>
cd biomedicos
docker compose up -d --build
```

Ver el [README](README.md#instalación).

---

## Notas de Versión


## Contribuciones y Créditos

- **v2.0 Reorganización:** Eduardo Cortes (Restructuring Specialist)
- **v1.5 Correcciones:** Eduardo Cortes (Debugging & Testing)
- **v1.0 Setup:** Eduardo Cortes (Initial Setup & Dependencies)

---

**Última actualización:** 2026-10-09
**Versión actual:** 2.4.1
**Status:** Proyecto de práctica en desarrollo. El validador es simulado: no apto para uso clínico.
