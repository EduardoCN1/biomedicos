# Arquitectura de Microservicios con Mensajería (TNM → Recomendación → Validación ML)

## Objetivo
Desacoplar el flujo clínico para que:
1. Frontend envía TNM.
2. Servicio Recomendador consulta Neo4j y genera tratamientos candidatos.
3. Servicio ML Validador aprueba/descarta candidatos.
4. Resultado validado vuelve al Frontend.

## Componentes
- **API Gateway (backend/api.py)**
  - `POST /pipeline/submit`: crea `job_id` y publica mensaje inicial.
  - `GET /pipeline/result/<job_id>`: retorna estado/resultado por polling.
  - `GET /pipeline/health`: estado básico de broker/consumidor.
- **Recommender Service (services/recommender_service.py)**
  - Consume: `tnm.recommendation.request`
  - Produce: `tnm.validation.request`
- **ML Validator Service (services/ml_validator_service.py)**
  - Consume: `tnm.validation.request`
  - Produce: `tnm.validation.result`
- **Broker**: RabbitMQ
- **Base de conocimiento**: Neo4j

## Flujo de Mensajes
1. Frontend → `POST /pipeline/submit` con `t_label`, `n_label`, `m_label`.
2. API publica mensaje en `tnm.recommendation.request`.
3. Recommender consume, consulta Neo4j y publica en `tnm.validation.request`.
4. ML Validator consume, valida recomendaciones y publica en `tnm.validation.result`.
5. API consume `tnm.validation.result`, guarda resultado en memoria por `job_id`.
6. Frontend hace polling a `GET /pipeline/result/<job_id>` y renderiza `final_recommendations`.

## Contrato Base de Mensajes
### Mensaje de entrada a recomendación
```json
{
  "job_id": "uuid",
  "tnm": {
    "t_label": "T2",
    "n_label": "N1",
    "m_label": "M0"
  },
  "context": {
    "edad": "56",
    "sexo": "Femenino"
  },
  "timestamp": 1741040000
}
```

### Mensaje final de validación
```json
{
  "job_id": "uuid",
  "status": "completed",
  "tnm": { "t_label": "T2", "n_label": "N1", "m_label": "M0" },
  "recommendations": [
    {
      "Stage": "II",
      "RecommendedTests": ["Test A"],
      "TreatmentOptions": ["Tx1", "Tx2"]
    }
  ],
  "final_recommendations": [
    {
      "Stage": "II",
      "RecommendedTests": ["Test A"],
      "TreatmentOptions": ["Tx1"]
    }
  ],
  "validation_details": [],
  "summary": { "approved_count": 1, "rejected_count": 1 },
  "model": {
    "name": "mock-validator",
    "version": "0.1.0",
    "note": "Reemplazar por servicio ML real"
  },
  "timestamp": 1741040002
}
```

## Cómo levantar con Docker
```bash
docker compose up --build
```
Servicios relevantes:
- API: `http://localhost:5000`
- RabbitMQ: `amqp://localhost:5672`
- RabbitMQ UI: `http://localhost:15672` (user/pass: guest/guest)

## Integración futura del ML real
El equipo de ML solo debe reemplazar la lógica de `ml_validator_service.py` manteniendo:
- Entrada desde `VALIDATION_REQUEST_QUEUE`
- Salida a `VALIDATION_RESULT_QUEUE`
- Estructura JSON con `job_id` y `final_recommendations`

## Notas de MVP
- El estado de jobs se guarda en memoria (reinicio del API borra estados).
- Se mantiene fallback frontend al endpoint directo `/get_stage_info` si falla la mensajería.
- Recomendado: agregar Redis/PostgreSQL para persistencia de jobs en siguiente iteración.
