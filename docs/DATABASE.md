# Gestión de Base de Datos Neo4j

Esta guía explica cómo se cargan los datos en Neo4j y cómo recargarlos, respaldarlos y restaurarlos con Docker.

Los comandos están escritos para PowerShell. En Git Bash, los que contienen rutas del contenedor (`/backups`) necesitan el prefijo `MSYS_NO_PATHCONV=1` (ver [Troubleshooting](#troubleshooting)).

## Carga Automática de Datos

Los datos de origen son `data/nodos.csv` y `data/relaciones.csv` (134 nodos y 310 relaciones), versionados en Git.

Cada vez que se levanta el proyecto, el servicio `seed` ejecuta `scripts/import_csv.py`:
- **Primero valida el formato** de los datos (ver [Formato de los Datos](#formato-de-los-datos)). Si no es correcto, no importa nada y termina con error; `api` y `recommender` no arrancan hasta que se corrija el CSV.
- **Si Neo4j está vacío**, importa todos los nodos y relaciones en una sola transacción (si algo falla, no deja datos a medias).
- **Si Neo4j ya tiene datos**, no hace nada. Por eso es seguro levantar el proyecto tantas veces como se quiera: los datos no se duplican.

Los datos se guardan en el volumen de Docker `biomedicos_neo4j_data` y se conservan entre `docker compose down` y `docker compose up`.

## Formato de los Datos

Los CSV son la **fuente de verdad** de los datos: lo que contienen es exactamente lo que se carga en Neo4j, sin transformaciones. Si se corrige o amplía algún dato, se hace en el CSV.

Ambos archivos tienen una sola columna (encabezado `"n"` en nodos y `"r"` en relaciones). Cada fila es un objeto JSON, con las comillas dobles escapadas según el formato CSV (`""`), tal como los exporta Neo4j:

```
"n"
"{""id"":1,""labels"":[""Class"",""Sub_N_Stage_Finding""],""properties"":{""label"":""N1mi"", ...}}"
```

**Nodos** (`data/nodos.csv`):

| Campo | Contenido |
|-------|-----------|
| `id` | Identificador numérico único; las relaciones lo usan para enlazar nodos |
| `labels` | Lista de tipos del nodo en Neo4j (por ejemplo `["Class", "T_Stage_Finding"]`) |
| `properties` | Propiedades del nodo. `label` es su nombre (`"T1"`, `"Stage IIA"`, `"Surgery"`…) |

**Relaciones** (`data/relaciones.csv`):

| Campo | Contenido |
|-------|-----------|
| `id` | Identificador de la relación |
| `type` | Tipo de relación (`Has_Stage`, `Has_Recommended_Test`, `Has_Treatment_Option`…) |
| `start`, `end` | `id` de los nodos de origen y destino |
| `properties` | Propiedades de la relación (hoy, siempre vacías) |

**Regla que valida `seed`:** la propiedad `label` de cada nodo debe ser **texto**, no una lista. Las exportaciones de la ontología a veces la guardan como lista de un elemento (`"label":["Stage IIA"]`); en ese caso la API devolvería listas y las búsquedas por nombre en Neo4j no encontrarían el nodo. Hay que corregirlo en el CSV (`"label":"Stage IIA"`) antes de cargarlo.

Ver [MICROSERVICIOS.md](MICROSERVICIOS.md#modelo-de-datos-en-neo4j) para qué nodos y relaciones usan las consultas.

## Recargar los Datos desde los CSV

Por ejemplo, después de editar los CSV:

```powershell
docker compose down -v      # Borra el volumen de Neo4j
docker compose up -d        # seed vuelve a importar los CSV
```

**Advertencia:** `down -v` borra todos los datos de Neo4j, incluidos los cambios hechos a mano desde Neo4j Browser. Si se quieren conservar, crear antes una copia de seguridad.

Para ejecutar la importación manualmente (solo importa si Neo4j está vacío):

```powershell
docker compose run --rm seed
```

## Crear una Copia de Seguridad (Dump)

Neo4j Community solo permite hacer el dump con la base de datos **detenida**; con Neo4j en marcha falla con `Dump failed for databases: 'neo4j'`.

```powershell
docker compose stop neo4j
docker compose run --rm --no-deps neo4j neo4j-admin database dump neo4j --to-path=/backups
docker compose start neo4j
```

El archivo se guarda en el equipo como `data/backups/neo4j.dump` (la carpeta está montada en el contenedor como `/backups`). Si ya existe un `neo4j.dump`, renombrarlo antes para conservarlo:

```powershell
Rename-Item data/backups/neo4j.dump "neo4j-$(Get-Date -Format 'yyyy-MM-dd').dump"
```

Los archivos `.dump` no se suben a Git (están en `.gitignore`).

## Restaurar una Copia de Seguridad

1. Colocar el archivo en `data/backups/` con el nombre `neo4j.dump`.
2. Ejecutar:

```powershell
docker compose stop neo4j
docker compose run --rm --no-deps neo4j neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true
docker compose start neo4j
```

Tras restaurar, `seed` no modifica nada porque la base ya tiene datos.

**Nota:** un dump creado con una versión de Neo4j más nueva que la 5 (por ejemplo, las 2025.x) no se puede cargar en Neo4j 5.

## Borrar los Datos sin Borrar el Volumen

Desde Neo4j Browser (http://localhost:7474):

```cypher
MATCH (n) DETACH DELETE n;
```

Para volver a cargar los CSV después: `docker compose run --rm seed`.

## Verificar los Datos

### Desde Neo4j Browser (http://localhost:7474)

```cypher
// Contar nodos (esperado: 134)
MATCH (n) RETURN count(n) AS total_nodos;

// Contar relaciones (esperado: 310)
MATCH ()-[r]->() RETURN count(r) AS total_relaciones;

// Ver tipos de nodos
MATCH (n) RETURN DISTINCT labels(n), count(*);

// Ver algunos nodos de ejemplo
MATCH (n) RETURN n LIMIT 25;
```

### Desde la Terminal

```powershell
# Conteo de nodos sin abrir el navegador
docker compose exec neo4j sh -c 'cypher-shell -u "${NEO4J_AUTH%%/*}" -p "${NEO4J_AUTH#*/}" "MATCH (n) RETURN count(n)"'
```

### Desde la API

```powershell
# Etiquetas T disponibles
Invoke-RestMethod http://localhost:5000/labels/t

# Consulta completa de un TNM
Invoke-RestMethod "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0"
```

## Troubleshooting

### Error: "Dump failed for databases: 'neo4j'"

Neo4j está en marcha. Detenerlo antes con `docker compose stop neo4j`.

### Error: "C:/Program Files/Git/backups is not an existing directory"

Git Bash convierte las rutas que empiezan por `/` en rutas de Windows. Usar PowerShell, o anteponer `MSYS_NO_PATHCONV=1` al comando:

```bash
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps neo4j neo4j-admin database dump neo4j --to-path=/backups
```

### La primera consulta tras reiniciar Neo4j tarda unos segundos

Es normal: la API y el recomendador reintentan automáticamente mientras restablecen la conexión con Neo4j, y después responden con normalidad.

### `seed` falla con "'label' que no es texto"

Algún nodo de `data/nodos.csv` no cumple el [formato de los datos](#formato-de-los-datos). El mensaje enumera los nodos afectados (`nodo id=6: label=["Stage IB"]`); corregirlos en el CSV (`"label":"Stage IB"`) y volver a ejecutar `docker compose up -d`.

### Los datos están duplicados

Puede ocurrir con bases importadas con la versión antigua del script, que no comprobaba si ya había datos. Solución: `docker compose down -v` y `docker compose up -d`.

---

**Última actualización:** 2026-10-07
