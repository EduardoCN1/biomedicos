# Diagramas de Arquitectura

Diagramas en [Mermaid](https://mermaid.js.org/). GitHub los dibuja directamente al ver este archivo; en VS Code, con una extensión de vista previa de Mermaid. Para modificarlos basta con editar el código de cada bloque: no hay imágenes aparte que mantener.

## Servicios y Comunicación

```mermaid
flowchart LR
    Browser["Navegador"]

    subgraph Docker["docker compose"]
        Frontend["frontend<br/>nginx :5500"]
        API["api<br/>Flask + Waitress :5000"]
        RabbitMQ[("rabbitmq<br/>:5672 / :15672")]
        Recommender["recommender"]
        Validator["ml-validator<br/>validador simulado"]
        Neo4j[("neo4j<br/>:7474 / :7687")]
        Seed["seed<br/>carga los CSV y termina"]
    end

    CSV[/"data/nodos.csv<br/>data/relaciones.csv"/]

    Browser -->|página y /api/...| Frontend
    Frontend -->|proxy /api/| API
    API -->|tnm.recommendation.request| RabbitMQ
    RabbitMQ --> Recommender
    Recommender -->|consulta Cypher| Neo4j
    Recommender -->|tnm.validation.request| RabbitMQ
    RabbitMQ --> Validator
    Validator -->|tnm.validation.result| RabbitMQ
    RabbitMQ -->|resultados| API
    API -->|/get_stage_info y /labels: diagnóstico| Neo4j
    CSV --> Seed --> Neo4j
```

Desde otros equipos de la red solo es accesible `frontend` (:5500). Los puertos de `api`, `rabbitmq` y `neo4j` se publican en `127.0.0.1`: solo responden en el propio servidor.

## Secuencia de una Consulta

```mermaid
sequenceDiagram
    actor U as Usuario
    participant P as Página (entradas.js)
    participant A as API
    participant Q as RabbitMQ
    participant R as Recomendador
    participant V as Validador
    participant N as Neo4j

    U->>P: Pulsa Consultar
    P->>A: POST /api/pipeline/submit (TNM + context)
    A->>A: Guarda job_id en memoria (processing)
    A->>Q: Publica en tnm.recommendation.request
    A-->>P: 202 con job_id
    Q->>R: Entrega el mensaje
    R->>N: Consulta estadios, pruebas y tratamientos
    N-->>R: Estadios
    R->>R: Filtra cirugía si surgery_preference es No
    R->>Q: Publica en tnm.validation.request
    Q->>V: Entrega el mensaje
    V->>V: Evalúa cada tratamiento
    V->>Q: Publica en tnm.validation.result
    Q->>A: Entrega el resultado
    A->>A: Marca el trabajo como completed

    loop Cada 2 s, hasta 30 veces
        P->>A: GET /api/pipeline/result/job_id
        A-->>P: status
    end

    alt completed
        P->>U: Muestra hasta 3 estadios con pruebas y tratamientos
    else failed o 60 s sin resultado
        P->>U: Aviso No se pudo completar la evaluación, sin mostrar tratamientos
    end
```

Si el recomendador o el validador fallan, publican un aviso en `tnm.validation.result` y el trabajo pasa a `failed` sin esperar los 60 s.

## Orden de Arranque

```mermaid
flowchart TB
    Neo4j["neo4j<br/>healthcheck: cypher-shell"]
    RabbitMQ["rabbitmq<br/>healthcheck: check_port_connectivity"]
    Seed["seed<br/>valida e importa los CSV"]
    API["api"]
    Recommender["recommender"]
    Validator["ml-validator"]
    Frontend["frontend"]

    Neo4j -->|healthy| Seed
    Seed -->|terminó bien| API
    Seed -->|terminó bien| Recommender
    Neo4j -->|healthy| API
    Neo4j -->|healthy| Recommender
    RabbitMQ -->|healthy| API
    RabbitMQ -->|healthy| Recommender
    RabbitMQ -->|healthy| Validator
    API -->|iniciado| Frontend
```

Este orden se aplica con `docker compose up`. Cuando Docker arranca por su cuenta (al encender el equipo), levanta los servicios sin orden y estos reintentan la conexión hasta que Neo4j y RabbitMQ están listos; `seed` no se ejecuta.

## Modelo de Datos

Solo los nodos y relaciones que usan las consultas (ver [MICROSERVICIOS.md](MICROSERVICIOS.md#modelo-de-datos-en-neo4j)).

```mermaid
flowchart LR
    T["T_Stage_Finding<br/>T0 … T4, Tx, Tis"]
    N["N_Stage_Finding<br/>N0 … N4, Nx"]
    M["M_Stage_Finding<br/>M0, M1, MX"]
    S7["Estadios AJCC 7.ª edición<br/>R7_Stage, Sub_R7_Stage"]
    S8["Estadios AJCC 8.ª edición<br/>R8_Stage, Sub_R8_Stage"]
    Test["Test<br/>9 pruebas"]
    Treatment["Treatment<br/>8 tratamientos"]

    T -->|Has_Stage| S7
    T -->|Has_Stage| S8
    N -->|Has_Stage| S7
    N -->|Has_Stage| S8
    M -->|Has_Stage| S7
    M -->|Has_Stage| S8
    S8 -->|Has_Recommended_Test| Test
    S8 -->|Has_Treatment_Option| Treatment
```

La consulta devuelve los estadios a los que apuntan a la vez los valores T, N y M elegidos y que tienen pruebas y tratamientos, es decir, solo estadios de la 8.ª edición.
