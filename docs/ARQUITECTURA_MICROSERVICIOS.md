# Arquitectura de Microservicios con Docker

**Última actualización:** 4 de marzo de 2026

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Componentes](#componentes)
3. [Flujo de Datos](#flujo-de-datos)
4. [Cómo Ejecutar](#cómo-ejecutar)
5. [Monitoreo y Debugging](#monitoreo-y-debugging)
6. [Agregar Cambios](#agregar-cambios)
7. [Troubleshooting](#troubleshooting)

---

##  Visión General

El proyecto utiliza una **arquitectura de microservicios asincrónica** para procesar solicitudes TNM (Tumor, Node, Metástasis). En lugar de procesar todo en un único script, el trabajo se divide en servicios independientes que se comunican a través de colas de mensajes.

### ¿Por qué microservicios?

- **Escalabilidad:** Cada servicio puede crecer independientemente
- **Mantenibilidad:** Cambios en un servicio no afectan otros
- **Resiliencia:** Si falla un servicio, otros continúan funcionando
- **Flexibilidad:** Fácil agregar nuevos servicios

### Arquitectura en Diagrama

```
┌─────────────────┐
│    FRONTEND     │ (HTML/CSS/JS en navegador)
│  index.html     │
└────────┬────────┘
         │ HTTP POST /pipeline/submit
         │ (TNM: T1, N0, M0)
         │
    ┌────▼────────────────────────────────────────┐
    │         DOCKER CONTAINER: API               │
    │  (backend/api.py - Flask)                   │
    │                                              │
    │  - Recibe TNM del frontend                  │
    │  - Publica mensaje a cola: REQUEST          │
    │  - Escucha cola: RESULT                     │
    │  - Retorna resultado al cliente (polling)   │
    └────┬─────────────────────┬──────────────────┘
         │                     │
    ┌────▼──────────────┐     │
    │   RabbitMQ        │     │
    │  (Cola de msgs)   │     │
    │                   │     │
    │ ├─ REQUEST queue  │     │
    │ └─ RESULT queue   │     │
    └────┬──────────────┘     │
         │                     │
    ┌────▼─────────────────────▼─────────────────┐
    │  DOCKER CONTAINER: RECOMMENDER_SERVICE     │
    │                                             │
    │ 1. Consume mensaje TNM de REQUEST queue    │
    │ 2. Conecta a Neo4j                        │
    │ 3. Ejecuta Cypher: MATCH stages + tests   │
    │ 4. Publica en VALIDATION queue            │
    └─────────────────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │  DOCKER CONTAINER: ML_VALIDATOR_SERVICE   │
    │                                           │
    │ 1. Consume recomendaciones                │
    │ 2. Valida cada tratamiento                │
    │ 3. Filtra: aprobadas vs rechazadas       │
    │ 4. Publica en RESULT queue                │
    └────┬──────────────────────────────────────┘
         │
    ┌────▼───────────────────────────────────┐
    │  API recibe resultado en RESULT queue   │
    │  Guarda en jobs_store con job_id        │
    │  Frontend obtiene resultado vía polling │
    └────────────────────────────────────────┘
```

---

##  Componentes

### 1. **Docker & Docker Compose**

**¿Qué es Docker?**
- Contenedor: Es como una "máquina virtual ligera" que incluye todo lo necesario para ejecutar un servicio (código + dependencias + configuración)
- **Ventaja:** Funciona igual en Windows, Mac, Linux sin "pero en mi máquina funcionaba"

**¿Qué es Docker Compose?**
- Archivo `docker-compose.yml` que orquesta MÚLTIPLES contenedores
- Define: Qué imágenes usar, puertos, variables de entorno, redes, volúmenes

**Archivo: `docker-compose.yml`**

```yaml
version: '3.8'
services:
  rabbitmq:     # Servicio 1
    image: rabbitmq:3-management
    ports:
      - "5672:5672"   # Puerto broker (comunicación entre servicios)
      - "15672:15672" # Puerto management (interfaz web)
    
  neo4j:        # Servicio 2
    image: neo4j:5-enterprise
    ports:
      - "7687:7687"   # Puerto Bolt (consultas desde Python)
      - "7474:7474"   # Puerto HTTP (interfaz web)
    environment:
      - NEO4J_AUTH=neo4j/admin123
    
  api:          # Servicio 3 - Gateway
    build: .    # Usa Dockerfile en raíz
    command: python ./backend/run_waitress.py
    ports:
      - "5000:5000"
    depends_on:
      - rabbitmq
      - neo4j
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - NEO4J_URI=bolt://neo4j:7687
    
  recommender:  # Servicio 4
    build: .
    command: python ./services/recommender_service.py
    depends_on:
      - rabbitmq
      - neo4j
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - NEO4J_URI=bolt://neo4j:7687
    
  ml-validator: # Servicio 5
    build: .
    command: python ./services/ml_validator_service.py
    depends_on:
      - rabbitmq
      - neo4j
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

**¿Cómo se comunican los servicios?**
- Docker crea una red interna
- `rabbitmq:5672` = nombre del servicio + puerto (Docker resuelve el IP automáticamente)
- `neo4j:7687` = lo mismo

---

### 2. **RabbitMQ - Cola de Mensajes**

**¿Qué es RabbitMQ?**
- Sistema de filas (queues) que almacena mensajes
- Los productores PUBLICAN mensajes
- Los consumidores CONSUMEN mensajes
- Es **asincrónico:** No necesitas esperar al consumidor

**¿Cómo funciona en nuestro proyecto?**

```
Flujo de 3 colas:

1. tnm.recommendation.request
   - Productor: API (cuando recibe TNM del frontend)
   - Consumidor: Recommender (procesa y consulta Neo4j)
   - Mensaje: {"job_id": "xxxxx", "tnm": {"t_label": "T1", ...}}

2. tnm.validation.request
   - Productor: Recommender (después de consultar Neo4j)
   - Consumidor: ML Validator (valida recomendaciones)
   - Mensaje: {"job_id": "xxxxx", "recommendations": [...]}

3. tnm.validation.result
   - Productor: ML Validator (después de validar)
   - Consumidor: API (recibe resultado y lo guarda)
   - Mensaje: {"job_id": "xxxxx", "final_recommendations": [...], "status": "completed"}
```

**Interfaz Web de RabbitMQ:**
- URL: `http://localhost:15672`
- Usuario: `guest`
- Contraseña: `guest`
- Ver: Colas, mensajes, tasa de procesamiento

---

### 3. **Neo4j - Base de Datos**

**¿Qué es Neo4j?**
- Base de datos de **grafos** (nodes + relationships)
- Perfecto para: Clasificaciones médicas, rutas de tratamiento, datos relacionales

**Nuestro modelo:**
- T_Stage_Finding, N_Stage_Finding, M_Stage_Finding → Nodos
- Has_Stage → Relación
- Has_Treatment_Option, Has_Recommended_Test → Relaciones

**Consulta Cypher típica:**
```cypher
MATCH (t:T_Stage_Finding {label: "T1"}),
      (n:N_Stage_Finding {label: "N0"}),
      (m:M_Stage_Finding {label: "M0"})
MATCH (t)-[:Has_Stage]->(stage)
      (stage)-[:Has_Treatment_Option]->(treatment)
RETURN stage.label, treatment.label
```

**Interfaz Web de Neo4j:**
- URL: `http://localhost:7474`
- Usuario: `neo4j`
- Contraseña: `admin123`

---

### 4. **Servicios Python**

#### **backend/api.py - API Gateway**

**Responsabilidades:**
- Recibir solicitudes HTTP del frontend
- Publicar mensajes en cola de REQUEST
- Escuchar cola de RESULT en background thread
- Retornar resultados cuando estén listos

**Endpoints principales:**

```python
POST /pipeline/submit
{
  "tnm": {
    "t_label": "T1",
    "n_label": "N0",
    "m_label": "M0"
  }
}
→ Retorna: {"job_id": "xxxxx", "status": "processing"} (HTTP 202)

GET /pipeline/result/<job_id>
→ Retorna: {"status": "completed", "result": {...}} (HTTP 200)

GET /pipeline/health
→ Retorna: {"rabbitmq": "up", "consumer": "running", ...}

GET /pipeline/debug
→ Retorna: {"total_jobs": 3, "jobs": {...}} (para debugging)
```

**Cómo maneja jobs:**
```python
jobs_store = {
  "job_id_123": {
    "status": "processing",  # processing | completed | failed
    "updated_at": 1234567890,
    "result": null  # Se llena cuando RESULT queue publica
  }
}
```

---

#### **services/recommender_service.py - Servicio Recomendador**

**Responsabilidades:**
1. Conectarse a RabbitMQ
2. Consumir mensajes de: `tnm.recommendation.request`
3. Para cada mensaje:
   - Extraer job_id y TNM (T, N, M labels)
   - Conectarse a Neo4j
   - Ejecutar query Cypher
   - Publicar en: `tnm.validation.request` (con recomendaciones)

**Pseudocódigo:**
```python
while True:
    mensaje = consumir_de_cola("tnm.recommendation.request")
    job_id = mensaje["job_id"]
    t, n, m = mensaje["tnm"]["t_label"], ...
    
    neo4j = Neo4JDatabase(uri, user, password)
    recomendaciones = neo4j.query(t, n, m)
    
    publicar_en_cola("tnm.validation.request", {
        "job_id": job_id,
        "recommendations": recomendaciones
    })
```

**Reconnection Logic:**
- Si RabbitMQ no está disponible, espera 5 segundos e intenta de nuevo
- Garantiza resiliencia ante caídas temporales

---

#### **services/ml_validator_service.py - Servicio Validador**

**Responsabilidades:**
1. Consumir mensajes de: `tnm.validation.request`
2. Para cada mensaje:
   - Validar cada recomendación (actualmente mock, listo para ML real)
   - Separar: aprobadas vs rechazadas
   - Publicar en: `tnm.validation.result` (solo los aprobados)

**Lógica de validación (mock):**
```python
def evaluate_treatment(option):
    # Si contiene palabras "experimentales" o "no recomendado" → rechaza
    # Caso contrario → aprueba
    if "experimental" in option.lower():
        return False
    return True
```

**Fácil de reemplazar con ML real:**
```python
# Simplemente cambiar la función:
def evaluate_treatment(option):
    # Llamar a modelo ML entrenado
    probabilidad = ml_model.predict(option)
    return probabilidad > 0.7  # Si prob > 70% → aprueba
```

---

### 5. **Frontend (HTML/JS)**

**Archivo: `frontend/js/entradas.js`**

**Lo que hace:**
1. Recibe datos del formulario (edad, TNM, etc.)
2. Llama a `POST /pipeline/submit`
3. Obtiene `job_id`
4. **Inicia polling:**
   ```javascript
   setInterval(() => {
     GET /pipeline/result/<job_id>
     if (status === "completed") {
       mostrar_resultados()
       clearInterval(poller)
     }
   }, 2000)  // Cada 2 segundos
   ```
5. Si microservicios fallan, fallback a sincrónico: `GET /get_stage_info?t=T1&n=N0&m=M0`

---

##  Flujo de Datos (Paso a Paso)

### Escenario: Usuario envía TNM (T1, N0, M0)

```
TIEMPO 0ms:
├─ Frontend: Click en "Enviar"
├─ Payload: {t_label: "T1", n_label: "N0", m_label: "M0"}
└─ HTTP POST http://localhost:5000/pipeline/submit

TIEMPO 10ms:
├─ API recibe solicitud
├─ Genera job_id: "620d271b-30ea-4e8e-aad9-35457dba1df0"
├─ Publica en cola: tnm.recommendation.request
│   └─ Mensaje: {"job_id": "620d...", "tnm": {"t_label": "T1", ...}}
└─ Retorna HTTP 202: {"job_id": "620d...", "status": "processing"}

TIEMPO 15ms:
├─ Frontend inicia polling cada 2 segundos
└─ GET /pipeline/result/620d...

TIEMPO 20ms:
├─ Recommender consume de tnm.recommendation.request
├─ Conecta a Neo4j
├─ Ejecuta: MATCH (T1)-[:Has_Stage]->(stage) ...
└─ Obtiene: [Stage IIA, Stage IA] con tratamientos

TIEMPO 30ms:
├─ Recommender publica en tnm.validation.request
│   └─ {"job_id": "620d...", "recommendations": [...]}
└─ Reconoce el mensaje

TIEMPO 35ms:
├─ ML Validator consume de tnm.validation.request
├─ Evalúa cada tratamiento
│   └─ "Surgery" → aprobado
│   └─ "Radiation Therapy" → aprobado
└─ Filtra rechazados (en este caso: 0)

TIEMPO 40ms:
├─ ML Validator publica en tnm.validation.result
│   └─ {"job_id": "620d...", "final_recommendations": [...], "status": "completed"}
└─ Reconoce el mensaje

TIEMPO 45ms:
├─ API escucha tnm.validation.result (thread background)
├─ Recibe resultado
└─ Actualiza: jobs_store["620d..."]["status"] = "completed"

TIEMPO 50ms (Frontend polling):
├─ GET /pipeline/result/620d...
├─ API retorna: {"status": "completed", "result": {...}}
├─ Frontend renderiza tratamientos en pantalla
└─ clearInterval(poller)
```

**Tiempo total: ~50ms** (en producción puede ser 100-500ms dependiendo de Neo4j)

---

##  Cómo Ejecutar

### Opción 1: Docker Compose (RECOMENDADO)

```powershell
# 1. Ir al directorio del proyecto
cd D:\Proyecto_Practica\biomedicos

# 2. Construir imágenes y ejecutar servicios
docker compose up --build

# 3. Verificar que todos los servicios están UP
docker compose ps

# 4. Ver logs en tiempo real
docker compose logs -f

# 5. Para cuando termines
docker compose down

# 6. Para eliminar volúmenes también (limpiar datos)
docker compose down -v
```

### Opción 2: Verificar el Pipeline

```powershell
# Script de prueba incluido
.\scripts\test-pipeline.ps1

# Qué hace:
# 1. Verifica salud del pipeline
# 2. Envía TNM (T1, N0, M0)
# 3. Muestra logs de microservicios
# 4. Espera resultado (polling)
# 5. Valida que todo funcionó
```

### Opción 3: Prueba Manual con cURL

```bash
# 1. Enviar TNM
curl -X POST http://localhost:5000/pipeline/submit \
  -H "Content-Type: application/json" \
  -d '{
    "tnm": {
      "t_label": "T1",
      "n_label": "N0",
      "m_label": "M0"
    }
  }'

# Obtendrás:
# {"job_id": "xxxxx", "status": "processing"}

# 2. Obtener resultado (repetir hasta status=completed)
curl http://localhost:5000/pipeline/result/xxxxx

# 3. Ver logs de un servicio específico
docker compose logs recommender
```

---

##  Monitoreo y Debugging

### 1. **Dashboard de RabbitMQ**

```
http://localhost:15672
Usuario: guest
Contraseña: guest

Ver:
- Colas activas
- Mensajes no procesados
- Tasa de procesamiento (msgs/segundo)
- Conexiones activas
```

### 2. **Dashboard de Neo4j**

```
http://localhost:7474
Usuario: neo4j
Contraseña: admin123

Ver:
- Ejecutar queries Cypher
- Inspeccionar nodos y relaciones
- Métricas de performance
```

### 3. **Logs de API Gateway**

```powershell
docker compose logs api -f

Buscar líneas:
✓ Consumidor escuchando cola: tnm.validation.result
✓ Resultado recibido para job_id=xxxxx
✗ Error publicando mensaje
```

### 4. **Logs del Recommender**

```powershell
docker compose logs recommender -f

Buscar líneas:
Esperando mensajes en: tnm.recommendation.request
[recommender] job_id=xxxxx enviado a validación
[recommender] Broker desconectado o error
```

### 5. **Logs del ML Validator**

```powershell
docker compose logs ml-validator -f

Buscar líneas:
[ml-validator] Esperando mensajes en: tnm.validation.request
[ml-validator] job_id=xxxxx validado y publicado
[ml-validator] aprobado/rechazado
```

### 6. **Endpoint de Debug**

```
http://localhost:5000/pipeline/debug

Retorna:
{
  "total_jobs": 3,
  "jobs": {
    "job_id_123": {
      "status": "completed",
      "updated_at": 1234567890,
      "result": {...}
    }
  }
}
```

---

##  Agregar Cambios

### Escenario 1: Cambiar la lógica del Recommender

```python
# Archivo: services/recommender_service.py
# Línea: ~38

def get_stage_treatment_and_tests(self, t_label, n_label, m_label):
    query = """
    MATCH (t:T_Stage_Finding {label: $t_label})
    ...
    """
    # EDITAR AQUÍ la query Cypher
```

**Pasos:**
1. Editar el archivo
2. `docker compose up --build` (reconstruye la imagen)
3. Testear con: `.\scripts\test-pipeline.ps1`

---

### Escenario 2: Agregar Validación Real en ML Validator

```python
# Archivo: services/ml_validator_service.py
# Línea: ~45

def evaluate_treatment(option):
    # Reemplazar:
    # return "experimental" not in option.lower()
    
    # Con:
    import pickle
    model = pickle.load(open("ml_model.pkl", "rb"))
    features = extract_features(option)
    probability = model.predict_proba([features])[0][1]
    return probability > 0.7
```

**Pasos:**
1. Entrenar modelo ML
2. Guardar como `ml_model.pkl` en `/app/models/`
3. Copiar en Dockerfile: `COPY models ./models`
4. Editar función `evaluate_treatment()`
5. `docker compose up --build`

---

### Escenario 3: Agregar un Nuevo Servicio

```dockerfile
# En docker-compose.yml, agregar:

  data-enricher:  # Nuevo servicio
    build: .
    command: python ./services/data_enricher_service.py
    depends_on:
      - rabbitmq
      - neo4j
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - NEO4J_URI=bolt://neo4j:7687
```

```python
# Crear: services/data_enricher_service.py

# Consumir de: tnm.validation.result (resultado final)
# Enriquecer con: datos adicionales desde API externa
# Publicar en: tnm.enriched.result (nueva cola)
```

---

##  Troubleshooting

### Problema: "Connection refused" en RabbitMQ

```
ERROR: ConnectionRefusedError(111, 'Connection refused')
```

**Solución:**
1. Verificar que RabbitMQ está corriendo: `docker compose ps`
2. Si dice "Exit", ver logs: `docker compose logs rabbitmq`
3. Reiniciar: `docker compose restart rabbitmq`

---

### Problema: Neo4j no contesta

```
ERROR: Cannot connect to bolt://neo4j:7687
```

**Solución:**
1. Verificar estado: `docker compose ps`
2. Ver logs: `docker compose logs neo4j`
3. Verificar credenciales en `backend/config.py`
4. Probar conexión manual: `docker compose exec neo4j cypher-shell`

---

### Problema: Polling no obtiene resultado después de 30 segundos

**Causas posibles:**
1. ML Validator crashed → Ver: `docker compose logs ml-validator`
2. RabbitMQ no entrega mensajes → Ver: `http://localhost:15672` (dashboard)
3. Neo4j query es muy lenta → Optimizar índices

**Debug:**
```bash
# Ver estado del job
curl http://localhost:5000/pipeline/debug

# Ver si hay mensajes en colas
docker logs bio-rabbitmq

# Reiniciar todo
docker compose restart
```

---

### Problema: "ModuleNotFoundError: No module named 'backend'"

**Solución:**
- Ya está arreglado en Dockerfile: `ENV PYTHONPATH=/app:$PYTHONPATH`
- Si de todas formas falla: `docker compose up --build`

---

### Problema: Queremos probar sin Docker

```python
# Para ejecutar servicios localmente (sin Docker):

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar RabbitMQ localmente (windows)
# Descargar: https://www.rabbitmq.com/download.html
# O usando WSL: wsl apt-get install rabbitmq-server

# 3. Iniciar cada servicio en terminal diferente
python backend/run_waitress.py  # API en puerto 5000
python services/recommender_service.py
python services/ml_validator_service.py

# NOTA: Esto es para desarrollo. En producción usar Docker.
```

---

##  Archivos Importantes

| Archivo | Propósito |
|---------  |-----------|
| `docker-compose.yml` | Orquesta los 5 servicios |
| `Dockerfile` | Define imagen Docker (Python + dependencias) |
| `backend/api.py` | API Gateway (Flask) |
| `services/recommender_service.py` | Consulta Neo4j |
| `services/ml_validator_service.py` | Valida recomendaciones |
| `backend/config.py` | Variables de configuración |
| `frontend/js/entradas.js` | Lógica del formulario y polling |
| `requirements.txt` | Dependencias Python |

---

##  Variables de Entorno

**Archivo: `.env.example`**

```powershell
# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=admin123

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

---

##  Checklist de Producción

Antes de desplegar a producción:

- [ ] ¿MLValidator tiene modelo ML real, no mock?
- [ ] ¿Credenciales cambiadadas en RabbitMQ y Neo4j?
- [ ] ¿Job store migrado a Redis/PostgreSQL (no en memoria)?
- [ ] ¿Logging agregado a cada servicio?
- [ ] ¿Backups de Neo4j configurados?
- [ ] ¿Monitoring en place (alertas si un servicio cae)?
- [ ] ¿Rate limiting en /pipeline endpoints?
- [ ] ¿Autenticación JWT en API?

---

##  Preguntas Comunes

**P: ¿Por qué 3 colas y no 1?**
R: Feedback, metricas y escalabilidad. Si solo tuviera 1 cola, cada servicio tendría que saber qué hacer con cada mensaje.

**P: ¿Qué pasa si ML Validator se cae?**
R: Los mensajes quedan en la cola. Cuando se reinicia, consume los pendientes. Garantizado al menos una vez.

**P: ¿Por qué polling y no WebSocket?**
R: Polling es simple y stateless. WebSocket requeriría persistencia de conexiones.

**P: ¿Cómo escalo a 100 usuarios simultáneos?**
R: Ejecutar N instancias del Recommender y ML Validator. RabbitMQ distribuye automáticamente.

---

**Última contribución:** Eduardo Fco. Cortés Navarro
**Preguntas?** Revisa los logs con `docker compose logs -f`
