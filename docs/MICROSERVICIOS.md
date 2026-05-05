# Arquitectura de Microservicios y Mensajería

## Visión General

El proyecto utiliza una **arquitectura de microservicios desacoplados** que se comunican a través de **RabbitMQ**, un message broker confiable y escalable. En lugar de procesar todo en un único script, el trabajo se divide en servicios independientes que se comunican a través de colas de mensajes.

### Beneficios de la Arquitectura de Microservicios

- **Escalabilidad:** Cada servicio puede crecer independientemente sin afectar a otros
- **Resiliencia:** Si un servicio falla, otros continúan funcionando correctamente
- **Asincronía:** Los servicios procesan en paralelo sin bloqueos de espera
- **Mantenibilidad:** Código modular y especializado por dominio
- **Flexibilidad:** Fácil agregar, modificar o remover servicios sin impactar el sistema completo
- **Independencia:** Cada servicio puede usar sus propias tecnologías y bases de datos

## Topología de Servicios

```
                    ┌──────────────────────────────────────────────┐
                    │        Frontend (puerto 5500)                │
                    │      HTML + JavaScript + CSS                │
                    └────────────────┬─────────────────────────────┘
                                     │ HTTP REST POST /pipeline/submit
                                     ▼
                    ┌──────────────────────────────────────────────┐
                    │    API Principal - biomedicos-api             │
                    │         (puerto 5000)                        │
                    │   • POST /pipeline/submit                    │
                    │   • GET /pipeline/result/<job_id>            │
                    │   • GET /pipeline/health                     │
                    │   • Orquestación de eventos                  │
                    └────────────────┬─────────────────────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │   RabbitMQ (puerto 5672)      │
                     │   Message Broker              │
                     │   • tnm.recommendation.request│
                     │   • tnm.validation.request    │
                     │   • tnm.validation.result     │
                     │   • Admin (puerto 15672)      │
                     └──────┬──────────────────┬─────┘
                            │                  │
                 ┌──────────▼──────┐  ┌───────▼──────────┐
                 │  Recommender    │  │  ML Validator    │
                 │  (puerto 5001)  │  │  (puerto 5002)   │
                 │                 │  │                  │
                 │ • Consulta Neo4j│  │ • Valida         │
                 │ • Genera ttos   │  │   recomendaciones│
                 │ • ML models     │  │ • Filtra riesgos │
                 └────────────────┘  └──────────────────┘
                         │                    │
                         └────────┬───────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   Neo4j (puerto 7474/7687)  │
                    │   • Base de datos TNM        │
                    │   • Nodos y relaciones       │
                    │   • Consultas Cypher         │
                    └─────────────────────────────┘
```

## Componentes Técnicos

### Docker y Docker Compose

**¿Qué es Docker?**

Docker es un sistema de contenedores que empaqueta una aplicación con todas sus dependencias en una "máquina virtual ligera". Esto garantiza que funcione identicamente en Windows, Mac y Linux.

**¿Qué es Docker Compose?**

Docker Compose es una herramienta que orquesta múltiples contenedores. El archivo `docker-compose.yml` define:
- Qué imágenes usar
- Puertos a exponer
- Variables de entorno
- Dependencias entre servicios
- Volúmenes de almacenamiento

**Estructura del docker-compose.yml:**

```yaml
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"      # Puerto AMQP (comunicación entre servicios)
      - "15672:15672"    # Puerto Web (panel de administración)
    
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"      # Puerto HTTP (interfaz web)
      - "7687:7687"      # Puerto Bolt (protocolo binario)
    environment:
      - NEO4J_AUTH=neo4j/password
    
  api:
    build: .             # Construye desde Dockerfile
    ports:
      - "5000:5000"
    depends_on:
      - rabbitmq
      - neo4j
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - NEO4J_URI=neo4j://neo4j:7687
    
  recommender:
    build: .
    command: python services/recommender_service.py
    depends_on:
      - rabbitmq
      - neo4j
    
  ml-validator:
    build: .
    command: python services/ml_validator_service.py
    depends_on:
      - rabbitmq
```

**Red Interna de Docker:**

Docker crea una red interna donde los servicios pueden comunicarse usando sus nombres:
- `rabbitmq:5672` → Resuelve automáticamente a la IP del contenedor RabbitMQ
- `neo4j:7687` → Resuelve automáticamente a la IP del contenedor Neo4j

### RabbitMQ - Message Broker

**¿Qué es RabbitMQ?**

RabbitMQ es un sistema de colas (queues) que almacena y distribuye mensajes entre productores y consumidores. Funciona de forma asincrónica: no requiere que el consumidor esté disponible en el momento de la publicación.

**Modelo de Comunicación:**

```
Productor (publica)
         ↓
   [COLA]  (almacena mensajes)
         ↓
Consumidor (consume)
```

**Ventajas:**
- Desacoplamiento: El productor no conoce al consumidor
- Confiabilidad: Los mensajes se guardan si el consumidor falla
- Escalabilidad: Múltiples consumidores pueden procesar mensajes en paralelo

### Neo4j - Base de Datos de Grafos

**¿Qué es Neo4j?**

Neo4j es una base de datos especializada en almacenar y consultar grafos (nodos conectados por relaciones). Es perfecta para datos médicos donde hay muchas relaciones complejas.

**Nuestro Modelo TNM:**

```
T_Stage_Finding (T1, T2, T3...)
        │
        └─[Has_Stage]──> Stage (IIIA, IIIB...)
                              │
                              ├─[Has_Treatment_Option] → Treatment
                              └─[Has_Recommended_Test] → Test

N_Stage_Finding (N0, N1, N2...)
        │
        └─[Has_Stage]──> Stage (mismos nodos)

M_Stage_Finding (M0, M1...)
        │
        └─[Has_Stage]──> Stage (mismos nodos)
```

**Ejemplo de Consulta Cypher:**

```cypher
MATCH (t:T_Stage_Finding {label: "T1"}),
      (n:N_Stage_Finding {label: "N0"}),
      (m:M_Stage_Finding {label: "M0"})
MATCH (t)-[:Has_Stage]->(stage),
      (n)-[:Has_Stage]->(stage),
      (m)-[:Has_Stage]->(stage)
MATCH (stage)-[:Has_Treatment_Option]->(treatment),
      (stage)-[:Has_Recommended_Test]->(test)
RETURN stage.label, treatment.label, test.label
```

### Servicios Python

#### **backend/api.py - API Gateway**

**Responsabilidades:**
1. Recibir solicitudes HTTP del frontend
2. Validar datos TNM
3. Publicar mensajes en RabbitMQ (cola: `tnm.recommendation.request`)
4. Escuchar respuestas en RabbitMQ (cola: `tnm.validation.result`)
5. Mantener estado de trabajos (jobs)
6. Retornar resultados a través de polling

**Endpoints:**

| Método | Ruta | Parámetros | Descripción |
|--------|------|-----------|-------------|
| POST | `/pipeline/submit` | `{"tnm": {"t_label": "T1", "n_label": "N0", "m_label": "M0"}}` | Inicia procesamiento asincrónico, retorna `job_id` |
| GET | `/pipeline/result/<job_id>` | `job_id` (path parameter) | Obtiene resultado cuando esté listo |
| GET | `/pipeline/health` | - | Verifica estado del pipeline (RabbitMQ, consumidores) |

**Ejemplo de Solicitud:**

```bash
curl -X POST http://localhost:5000/pipeline/submit \
  -H "Content-Type: application/json" \
  -d '{
    "tnm": {
      "t_label": "T1",
      "n_label": "N0",
      "m_label": "M0"
    }
  }'
```

**Respuesta (HTTP 202 Accepted):**

```json
{
  "job_id": "620d271b-30ea-4e8e-aad9-35457dba1df0",
  "status": "processing"
}
```

**Polling para Obtener Resultado:**

```bash
curl http://localhost:5000/pipeline/result/620d271b-30ea-4e8e-aad9-35457dba1df0
```

**Respuesta cuando está listo (HTTP 200):**

```json
{
  "job_id": "620d271b-30ea-4e8e-aad9-35457dba1df0",
  "status": "completed",
  "result": {
    "stage": "IA",
    "recommendations": ["Surgery", "Hormone Therapy"],
    "tests": ["IHC", "ER/PR"]
  }
}
```

#### **services/recommender_service.py - Servicio Recomendador**

**Responsabilidades:**

1. Conectarse a RabbitMQ y escuchar la cola `tnm.recommendation.request`
2. Para cada mensaje recibido:
   - Extraer el `job_id` y valores TNM
   - Conectar a Neo4j
   - Ejecutar consulta Cypher para obtener opciones de tratamiento
   - Publicar resultados en la cola `tnm.validation.request`

**Pseudocódigo:**

```python
while True:
    mensaje = canal_rabbitmq.consumir("tnm.recommendation.request")
    
    job_id = mensaje["job_id"]
    t_label = mensaje["tnm"]["t_label"]
    n_label = mensaje["tnm"]["n_label"]
    m_label = mensaje["tnm"]["m_label"]
    
    # Conectar a Neo4j y ejecutar consulta
    neo4j = Neo4JDatabase()
    resultados = neo4j.obtener_recomendaciones(t_label, n_label, m_label)
    
    # Publicar en la siguiente cola
    canal_rabbitmq.publicar("tnm.validation.request", {
        "job_id": job_id,
        "recommendations": resultados
    })
```

#### **services/ml_validator_service.py - Servicio Validador**

**Responsabilidades:**

1. Conectarse a RabbitMQ y escuchar la cola `tnm.validation.request`
2. Para cada recomendación recibida:
   - Validar cada opción de tratamiento
   - Filtrar rechazados (experimentales, riesgosos)
   - Publicar solo las aprobadas en la cola `tnm.validation.result`

**Lógica de Validación (Actualmente Mock, Listo para ML Real):**

```python
def evaluar_tratamiento(opcion):
    # Pseudocodigo: rechazar si contiene ciertos términos
    palabras_rechazadas = ["experimental", "no recomendado", "alto riesgo"]
    
    if any(palabra in opcion.lower() for palabra in palabras_rechazadas):
        return False  # Rechazar
    return True       # Aprobar
```

**Reemplazar con ML Real:**

```python
# Simplemente cambiar la función a:
def evaluar_tratamiento(opcion):
    # Cargar modelo entrenado
    probabilidad = ml_model.predict(opcion)
    return probabilidad > 0.75  # Si probabilidad > 75% → aprobar
```

### Frontend (JavaScript)

**Archivo: `frontend/js/entradas.js`**

**Flujo:**

1. Usuario llena formulario TNM (T, N, M)
2. Hace click en "Enviar"
3. JavaScript envía `POST /pipeline/submit`
4. Obtiene `job_id`
5. Inicia polling cada 2 segundos a `GET /pipeline/result/<job_id>`
6. Cuando `status === "completed"`, muestra resultados
7. Fallback: Si microservicios fallan, llama directamente a `GET /get_stage_info`

```javascript
// Pseudocódigo
const respuesta = await fetch("http://localhost:5000/pipeline/submit", {
    method: "POST",
    body: JSON.stringify({
        tnm: {
            t_label: "T1",
            n_label: "N0",
            m_label: "M0"
        }
    })
});

const { job_id } = await respuesta.json();

// Iniciar polling
const poll = setInterval(async () => {
    const resultado = await fetch(`/pipeline/result/${job_id}`);
    const datos = await resultado.json();
    
    if (datos.status === "completed") {
        mostrarResultados(datos.result);
        clearInterval(poll);
    }
}, 2000);  // Cada 2 segundos
```

## Topología de Servicios

## Colas de RabbitMQ

Las colas implementan un patrón **productor-consumidor**:

### 1. `requests` (Request Queue)
- **Publicador**: API Principal
- **Consumidor**: Validator + Recommender
- **Contenido**: Datos del formulario del usuario
- **Propósito**: Distribuir tareas de validación y recomendación

```json
{
  "request_id": "uuid-123",
  "user_id": "user-456",
  "timestamp": "2026-05-05T10:30:00Z",
  "t_label": "T2",
  "n_label": "N1",
  "m_label": "M0",
  "patient_data": {
    "edad": 45,
    "genero": "F",
    "historial": "cancer_mama"
  }
}
```

### 2. `validations` (Validation Results)
- **Publicador**: ML Validator
- **Consumidor**: API Principal
- **Contenido**: Resultados de validación
- **Propósito**: Retornar validaciones al API

```json
{
  "request_id": "uuid-123",
  "status": "valid",
  "errors": [],
  "warnings": ["TNM stage might be unusual for age"],
  "validation_score": 0.95
}
```

### 3. `recommendations` (Recommendation Results)
- **Publicador**: Recommender Service
- **Consumidor**: API Principal
- **Contenido**: Recomendaciones basadas en ML
- **Propósito**: Retornar recomendaciones al API

```json
{
  "request_id": "uuid-123",
  "recommended_tests": ["IHC", "ER/PR", "HER2"],
  "treatment_options": ["Cirugía", "Radioterapia", "Hormonoterapia"],
  "confidence": 0.88,
  "ml_model_version": "v1.2.3"
}
```

### 4. `responses` (Final Response Queue)
- **Publicador**: API Principal
- **Consumidor**: Frontend (vía polling AJAX)
- **Contenido**: Respuesta completa (validación + recomendación + datos Neo4j)
- **Propósito**: Enviar resultado final al usuario

```json
{
  "request_id": "uuid-123",
  "status": "success",
  "stage_info": {
    "stage": "IIIA",
    "recommended_tests": ["IHC", "ER/PR"],
    "treatment_options": ["Cirugía", "Quimioterapia"]
  },
  "validation": {
    "status": "valid",
    "score": 0.95
  },
  "ml_recommendations": {
    "tests": ["IHC", "ER/PR", "HER2"],
    "confidence": 0.88
  }
}
```

## Flujo de Ejecución

### Paso 1: Usuario Envía Formulario
```
Frontend
  ↓ (fetch/AJAX POST /entradas)
API (recibe JSON)
```

### Paso 2: API Publica Evento
```
API
  ↓ (publica a cola 'requests')
RabbitMQ
```

### Paso 3: Validator Procesa
```
RabbitMQ (cola 'requests')
  ↓ (consume)
ML Validator
  ↓ (valida patrones TNM)
RabbitMQ (publica a cola 'validations')
```

### Paso 4: Recommender Procesa
```
RabbitMQ (cola 'requests')
  ↓ (consume)
Recommender
  ↓ (ejecuta modelos ML)
RabbitMQ (publica a cola 'recommendations')
```

### Paso 5: API Agrega Resultados
```
RabbitMQ (colas 'validations' + 'recommendations')
  ↓ (consume ambas)
API
  ↓ (consulta Neo4j para datos estadios)
API
  ↓ (publica respuesta final a cola 'responses')
RabbitMQ
```

### Paso 6: Frontend Recibe Respuesta
```
RabbitMQ (cola 'responses')
  ↓ (polling AJAX cada 1-2 segundos)
Frontend
  ↓ (actualiza DOM, muestra resultados)
Usuario (ve recomendaciones + tests + tratamientos)
```

## Configuración de RabbitMQ

### Variables de Entorno (.env)

```ini
# RabbitMQ Broker
RABBITMQ_HOST=rabbitmq          # o 'localhost' si es local
RABBITMQ_PORT=5672              # Puerto AMQP
RABBITMQ_USER=guest             # Usuario por defecto
RABBITMQ_PASSWORD=guest         # Contraseña por defecto
RABBITMQ_VHOST=/                # Virtual host

# Colas
RABBITMQ_REQUEST_QUEUE=requests
RABBITMQ_VALIDATION_QUEUE=validations
RABBITMQ_RECOMMENDATION_QUEUE=recommendations
RABBITMQ_RESPONSE_QUEUE=responses

# Timeouts
RABBITMQ_TIMEOUT=30             # segundos
MESSAGE_TTL=3600000             # 1 hora en ms
```

### Admin Console

Para monitorear colas en tiempo real:

```
http://localhost:15672/
Usuario: guest
Contraseña: guest
```

**Vistas útiles:**
- **Queues**: Ver colas, mensajes pendientes, consumidores
- **Connections**: Conexiones activas de microservicios
- **Channels**: Canales de comunicación

## Manejo de Errores

### Dead-Letter Queue (DLQ)

Si un mensaje falla 3 veces, se envía a:
- **Cola**: `requests_dlq` / `validations_dlq` / `recommendations_dlq`
- **TTL**: 24 horas (después se descarta)

```python
# Ejemplo en ML Validator
try:
    validate_tnm_stage(message)
except ValidationError as e:
    # Reintento automático (hasta 3 veces)
    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
except Exception as e:
    # Enviar a DLQ
    publish_to_dlq(message, error=str(e))
```

### Logging Centralizado

Cada servicio registra:
- Request ID (para rastreo end-to-end)
- Timestamp
- Acción (publish, consume, error)
- Detalles

```python
logger.info(f"[{request_id}] Validating TNM stage: T={t}, N={n}, M={m}")
logger.error(f"[{request_id}] Validation failed: {error}")
```

## Docker Compose

### Arrancar con Docker

```bash
docker-compose up -d
```

Servicios incluidos:
- `neo4j` - Base de datos Neo4j
- `api` - API Principal (Flask)
- `recommender` - Microservicio Recommender
- `ml-validator` - Microservicio Validator
- `rabbitmq` - RabbitMQ Message Broker

### Verificar Estado

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver contenedores activos
docker ps

# Verificar conectividad RabbitMQ
docker exec biomedicos-rabbitmq rabbitmq-diagnostics status
```

### Detener Servicios

```bash
# Detener (conserva datos)
docker-compose down

# Detener y limpiar volúmenes (CUIDADO: borra datos)
docker-compose down -v
```

## Escalabilidad Horizontal

Para escalar un microservicio específico:

```bash
# En docker-compose.yml, aumentar réplicas
recommender:
  deploy:
    replicas: 3  # 3 instancias del Recommender

ml-validator:
  deploy:
    replicas: 2  # 2 instancias del Validator
```

RabbitMQ distribuye automáticamente los mensajes entre réplicas.

## Monitoreo y Debugging

### Ver Colas en Tiempo Real

```python
import pika

conn = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        credentials=pika.PlainCredentials('guest', 'guest')
    )
)
ch = conn.channel()

# Contar mensajes en cola
method = ch.queue_declare(queue='requests', passive=True)
print(f"Mensajes pendientes: {method.method.message_count}")
```

### Simular Request

```bash
# Publicar mensaje de prueba a 'requests'
curl -u guest:guest -H "content-type:application/json" \
  -XPOST http://localhost:15672/api/exchanges/%2F/amq.default/publish \
  -d'{"properties":{},"routing_key":"requests","payload":"test","payload_encoding":"string"}'
```

## Seguridad

### En Producción

```ini
# .env (nunca en Git)
RABBITMQ_USER=biomedicos_user
RABBITMQ_PASSWORD=StrongPassword123!
RABBITMQ_VHOST=/biomedicos

# TLS
RABBITMQ_PORT=5671              # AMQP + TLS
RABBITMQ_CERT=/path/to/cert.pem
RABBITMQ_KEY=/path/to/key.pem
```

### Validación de Mensajes

Cada consumidor valida:
- Esquema JSON (request_id, timestamp, etc)
- Datos requeridos
- Rangos válidos (edad, TNM labels, etc)

```python
def validate_message(message):
    required_fields = ['request_id', 'timestamp', 't_label', 'n_label', 'm_label']
    for field in required_fields:
        if field not in message:
            raise ValueError(f"Missing required field: {field}")
    
    # Validar rangos
    if message['t_label'] not in ['T0', 'T1', 'T2', 'T3', 'T4', 'Tx']:
        raise ValueError(f"Invalid T stage: {message['t_label']}")
```

## Referencias

- [RabbitMQ Official Docs](https://www.rabbitmq.com/documentation.html)
- [AMQP Protocol](https://www.amqp.org/)
- [Microservices Patterns](https://microservices.io/)
- [Event-Driven Architecture](https://en.wikipedia.org/wiki/Event-driven_architecture)
