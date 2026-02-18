# Diagrama de Arquitectura
# Editar codigo mermaid segun modificacinoes realizadas respecto al proyecto y generar un nuevo .SVG en https://mermaid.ai/web/ y remplazar en carpeta docs/diagramas_svg
## Flujo de Datos General

```mermaid
graph TB
    subgraph Frontend["FRONTEND"]
        HTML[frontend/index.html]
        JS[frontend/js/entradas.js]
        CSS[frontend/css/stilous.css]
        HTML -->|Lee estilo| CSS
        HTML -->|Carga scripts| JS
    end
    
    subgraph Backend["BACKEND"]
        Config[backend/config.py]
        API[backend/api.py]
        App[backend/app.py]
        Waitress[backend/run_waitress.py]
        Config -->|Lee env| API
        App -->|Define flask app| API
        Waitress -->|Arranca| App
    end
    
    subgraph Database["BASE DATOS"]
        Neo4j["Neo4j 5.x"]
        CSV["data/nodos.csv<br/>data/relaciones.csv"]
        CSV -->|Importa| Neo4j
    end
    
    subgraph Config_Files["CONFIGURACIÓN"]
        Env[".env<br/>(credenciales)"]
        EnvExample[".env.example<br/>(template)"]
    end
    
    subgraph Scripts["SCRIPTS"]
        Setup["scripts/setup.ps1<br/>(instala)"]
        Run["scripts/run.ps1<br/>(arranca)"]
        Import["scripts/import_csv.py<br/>(carga datos)"]
    end
    
    JS -->|AJAX|API
    API -->|Cypher|Neo4j
    Neo4j -->|JSON|API
    API -->|JSON|JS
    JS -->|Actualiza DOM|HTML
    
    Env -->|Credenciales|Config
    EnvExample -->|Plantilla|Env
    Setup -->|Instala|Backend
    Run -->|Activa env + arranca|Waitress
    Import -->|Carga CSV|Neo4j
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff3e0
    style Database fill:#e8f5e9
    style Config_Files fill:#f3e5f5
    style Scripts fill:#fce4ec
```

## Diagrama de Endpoints

```mermaid
graph LR
    Client[" Cliente<br/>(Browser/PowerShell)"]
    
    Client -->|GET /| Health["✓ Salud<br/>En ejecución"]
    Client -->|GET /labels/t| LabelT[" Etiquetas T<br/>T0, T1, T2..."]
    Client -->|GET /labels/n| LabelN[" Etiquetas N<br/>N0, N1, N2..."]
    Client -->|GET /labels/m| LabelM[" Etiquetas M<br/>M0, M1, Mx..."]
    Client -->|GET /get_stage_info| StageInfo[" Tratamientos<br/>Stage + Tests + Tratamientos"]
    Client -->|POST /entradas| Submit[" Confirma<br/>Datos recibidos"]
    
    Health -->|200 OK|Client
    LabelT -->|200 OK: JSON array|Client
    LabelN -->|200 OK: JSON array|Client
    LabelM -->|200 OK: JSON array|Client
    StageInfo -->|200 OK: JSON|Client
    StageInfo -->|404 if no match|Client
    Submit -->|201 Created|Client
```

## Estructura de Carpetas Completa

```mermaid
graph TD
    Root[" biomedicos/"]
    
    Root -->|Documentación| README[" README.md"]
    Root -->|Dependencias| Req[" requirements.txt"]
    Root -->|Configuración| Env[" .env.example"]
    Root -->|Git| GitIgnore[" .gitignore"]
    
    Root -->|Backend| Backend[" backend/"]
    Backend --> BInit["__init__.py"]
    Backend --> BConfig["config.py"]
    Backend --> BAPI["api.py"]
    Backend --> BApp["app.py"]
    Backend --> BWaitress["run_waitress.py"]
    
    Root -->|Frontend| Frontend[" frontend/"]
    Frontend --> FIndex["index.html"]
    Frontend --> FJS[" js/"]
    FJS --> FEntradas["entradas.js"]
    FJS --> FConfig["config.js"]
    Frontend --> FCSS[" css/"]
    FCSS --> FCss["stilous.css"]
    FCSS --> FScss["stilous.scss"]
    
    Root -->|Datos| Data[" data/"]
    Data --> DNodos["nodos.csv"]
    Data --> DRel["relaciones.csv"]
    Data --> DBackup[" backups/"]
    
    Root -->|Scripts| Scripts[" scripts/"]
    Scripts --> SSetup["setup.ps1"]
    Scripts --> SRun["run.ps1"]
    Scripts --> SImport["import_csv.py"]
    
    Root -->|Tests| Tests[" tests/"]
    Tests --> TTest["test_api.py"]
    
    Root -->|Documentación| Docs[" docs/"]
    Docs --> DArch["ARCHITECTURE.md"]
    Docs --> DAPI["API.md"]
    Docs --> DSetup["SETUP.md"]
    Docs --> DEstado["ESTADO_FINAL.md"]
    
    style Root fill:#fff9c4
    style Backend fill:#fff3e0
    style Frontend fill:#e1f5ff
    style Data fill:#e8f5e9
    style Scripts fill:#fce4ec
    style Tests fill:#f1f8e9
    style Docs fill:#f3e5f5
```

## Proceso de Deployment

```mermaid
graph LR
    A[" Developer"] -->|Clone repo| B[" Clonar proyecto"]
    B -->|Ejecutar| C["▶ scripts/setup.ps1"]
    C -->|Instala| D[" Conda + Dependencias"]
    D -->|Copiar| E[" .env.example → .env"]
    E -->|Editar| F[" Credenciales Neo4j"]
    F -->|Ejecutar| G["▶ scripts/run.ps1"]
    G -->|Carga env| H[" Variables de entorno"]
    H -->|Arranca| I[" Waitress en :5000"]
    I -->|Frontend abre| J[" Live Server en :5500"]
    J -->|AJAX| I
    I -->|Cypher| K[" Neo4j"]
    K -->|JSON| I
    I -->|JSON| J
    J -->|Muestra| L[" Resultados"]
    
    style A fill:#c8e6c9
    style C fill:#fce4ec
    style G fill:#fce4ec
    style I fill:#fff3e0
    style K fill:#e8f5e9
    style L fill:#c8e6c9
```

## Variables de Entorno (Config Flow)

```mermaid
graph LR
    A[" .env file<br/>(local)"] -->|load| B["backend/config.py"]
    C[" Sistema ENV<br/>(Windows vars)"] -->|read| B
    B -->|export| D["NEO4J_URI"]
    B -->|export| E["NEO4J_USER"]
    B -->|export| F["NEO4J_PASSWORD"]
    B -->|export| G["HOST"]
    B -->|export| H["PORT"]
    B -->|export| I["ENVIRONMENT"]
    
    D -->|uso| J["backend/api.py"]
    E -->|uso| J
    F -->|uso| J
    G -->|uso| K["backend/run_waitress.py"]
    H -->|uso| K
    I -->|uso| J
    
    J -->|conecta| L["Neo4j DB"]
    K -->|sirve en| M["Waitress Server"]
    
    style A fill:#f3e5f5
    style B fill:#fff3e0
    style J fill:#fff3e0
    style K fill:#fff3e0
    style L fill:#e8f5e9
    style M fill:#c8e6c9
```

## Ciclo de Requeste (Ejemplo)

```mermaid
sequenceDiagram
    participant Browser as  Browser
    participant JS as  entradas.js
    participant API as  api.py
    participant Neo4j as  Neo4j
    
    Browser->>JavaScript: Usuario llena formulario
    JavaScript->>Browser: Valida campos
    JavaScript->>API: AJAX GET /get_stage_info?t=T2&n=N1&m=M0
    API->>API: Lee .env (credenciales)
    API->>Neo4j: MATCH (n:T2), (no:N1)... RETURN
    Neo4j-->>API: Resultados Cypher
    API->>API: Formatea JSON
    API-->>JavaScript: {"Stage":"IIIA", "Tests":[...], ...}
    JavaScript->>Browser: Actualiza DOM (res1, res2, res3)
    Browser->>Browser: Muestra resultados al usuario
```

## Stack Tecnológico

```mermaid
graph TB
    subgraph Frontend["Frontend Stack"]
        HTML5["HTML5"]
        JS["JavaScript<br/>(jQuery)"]
        CSS["CSS3<br/>(Bootstrap 5)"]
        HTML5 -.-> Bootstrap["Bootstrap 5.3.3"]
        JS -.-> jQuery["jQuery 3.6.0"]
        JS -.-> Toastr["Toastr.js"]
    end
    
    subgraph Backend["Backend Stack"]
        Python["Python 3.11"]
        Flask["Flask 3.0.0"]
        CORS["Flask-CORS 4.0.0"]
        Waitress["Waitress 2.1.2"]
        Python --> Flask
        Flask --> CORS
        Flask --> Waitress
    end
    
    subgraph Database["Database Stack"]
        Neo4j["Neo4j 5.x"]
        PY2Neo["py2neo 2021.2.4"]
        Pandas["pandas 2.1.3"]
        Neo4j -.-> PY2Neo
        Neo4j -.-> Pandas
    end
    
    subgraph DevTools["Dev Tools"]
        Conda["Miniforge/Conda"]
        PowerShell["PowerShell"]
        VSCode["VS Code"]
        LiveServer["Live Server Ext"]
    end
    
    Frontend -.->|AJAX| Backend
    Backend -.->|py2neo| Database
    Conda -.->|manage| Backend
    PowerShell -.->|scripts| Backend
    VSCode -.->|edit| Frontend
    LiveServer -.->|serve| Frontend
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff3e0
    style Database fill:#e8f5e9
    style DevTools fill:#f3e5f5
```