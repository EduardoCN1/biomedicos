# Arquitectura de Microservicios y Mensajería

## Visión General

El proyecto utiliza una **arquitectura de microservicios desacoplados** que se comunican a través de **RabbitMQ**, un message broker confiable y escalable. Esto permite:

-  **Escalabilidad**: Cada servicio puede escalar independientemente
-  **Resiliencia**: Si un servicio falla, otros continúan funcionando
-  **Asincronía**: Los servicios procesan en paralelo sin bloqueos
-  **Mantenibilidad**: Código modular y especializado por dominio

## Topología de Servicios

```
                    ┌──────────────────────────────────────────────┐
                    │        Frontend (puerto 5500)                │
                    │      HTML + JavaScript + CSS                │
                    └────────────────┬─────────────────────────────┘
                                     │ HTTP REST
                                     ▼
                    ┌──────────────────────────────────────────────┐
                    │    API Principal - biomedicos-api             │
                    │         (puerto 5000)                        │
                    │   • Endpoints REST/AJAX                      │
                    │   • Lógica de orquestación                   │
                    │   • Conexión a Neo4j                         │
                    │   • Publicación de eventos                   │
                    └────────────────┬─────────────────────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │   RabbitMQ (puerto 5672)      │
                     │   Message Broker              │
                     │   • Colas FIFO                │
                     │   • Pub/Sub topics            │
                     │   • Dead-letter exchanges     │
                     │   • Admin (puerto 15672)      │
                     └──────┬──────────────────┬─────┘
                            │                  │
                 ┌──────────▼──────┐  ┌───────▼──────────┐
                 │  Recommender    │  │  ML Validator    │
                 │  (puerto 5001)  │  │  (puerto 5002)   │
                 │                 │  │                  │
                 │ • Modelos ML    │  │ • Validación de  │
                 │ • Recomend.     │  │   patrones       │
                 │ • KNN, etc      │  │ • Reglas oncol.  │
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
