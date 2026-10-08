# Gestión de Base de Datos Neo4j

Esta guía explica cómo se cargan los datos en Neo4j y cómo recargarlos, respaldarlos y restaurarlos con Docker.

Los comandos están escritos para PowerShell. En Git Bash, los que contienen rutas del contenedor (`/backups`) necesitan el prefijo `MSYS_NO_PATHCONV=1` (ver [Troubleshooting](#troubleshooting)).

## Carga Automática de Datos

Los datos de origen son `data/nodos.csv` y `data/relaciones.csv` (134 nodos y 310 relaciones), versionados en Git.

Cada vez que se levanta el proyecto, el servicio `seed` ejecuta `scripts/import_csv.py`:
- **Si Neo4j está vacío**, importa todos los nodos y relaciones en una sola transacción (si algo falla, no deja datos a medias).
- **Si Neo4j ya tiene datos**, no hace nada. Por eso es seguro levantar el proyecto tantas veces como se quiera: los datos no se duplican.

Los datos se guardan en el volumen de Docker `biomedicos_neo4j_data` y se conservan entre `docker compose down` y `docker compose up`.

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

### La API devuelve error justo después de reiniciar Neo4j

La primera consulta tras `docker compose start neo4j` puede fallar con `Unable to retrieve routing information`. La API se reconecta sola: repetir la consulta (o ejecutar `docker compose restart api`).

### Los datos están duplicados

Puede ocurrir con bases importadas con la versión antigua del script, que no comprobaba si ya había datos. Solución: `docker compose down -v` y `docker compose up -d`.

---

**Última actualización:** 2026-10-07
