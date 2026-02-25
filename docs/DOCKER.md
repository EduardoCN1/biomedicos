# Guia de Docker

Esta guia explica como ejecutar el proyecto con Docker y Docker Compose y como usarlo en el dia a dia.

## Dos caminos disponibles

Camino A. Usar Docker
- No necesitas conda ni Neo4j Desktop
- Todo corre en contenedores

Camino B. Sin Docker
- Usas conda y Neo4j Desktop
- Ver [SETUP.md](SETUP.md) y [USO_DIARIO_SIN_DOCKER.md](USO_DIARIO_SIN_DOCKER.md)

## Requisitos (Docker)

- Docker Desktop instalado y corriendo
- Docker Compose v2
- Puertos libres: 5000 (API), 7474 (Neo4j Browser), 7687 (Neo4j Bolt)

## Archivos Docker en el proyecto

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.docker.example`

## Configuracion inicial (primera vez con Docker)

1. Crear archivo de variables para Docker:
```powershell
Copy-Item .env.docker.example .env.docker
```

2. Levantar contenedores:
```powershell
docker compose --env-file .env.docker up --build
```

3. Verificar servicios:
- Neo4j Browser: http://localhost:7474
- API: http://localhost:5000/

## Uso diario con Docker

### Iniciar todo
```powershell
docker compose --env-file .env.docker up
```

### Detener todo (al terminar de trabajar)
```powershell
docker compose down
```
Esto detiene los contenedores Neo4j y API, y libera los puertos 5000, 7474 y 7687.
Los datos permanecen en el volumen Docker `biomedicos_neo4j_data`.

Opcionalmente, cierra Docker Desktop si no lo usas para otros proyectos.

**Importante:** Si quieres eliminar los datos tambien:
```powershell
# Detener y eliminar volumenes (BORRA DATOS)
docker compose down -v
```

### Reiniciar solo la API
```powershell
docker compose restart api
```

### Ver logs
```powershell
docker compose logs -f
```

## Carga de datos con Docker

### Opcion A: Importar desde CSV
```powershell
docker compose exec api python scripts/import_csv.py
```

### Opcion B: Restaurar dump
1. Copia el dump a `data/backups/`.
2. Deten Neo4j:
```powershell
docker compose stop neo4j
```
3. Restaura el dump:
```powershell
docker compose run --rm neo4j neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true
```
4. Inicia Neo4j:
```powershell
docker compose start neo4j
```

## Verificacion rapida

```powershell
Invoke-RestMethod http://localhost:5000/
Invoke-RestMethod http://localhost:5000/labels/t
```

## Problemas comunes con Docker

- La API arranca antes de Neo4j:
  - Espera 10-20 segundos o ejecuta `docker compose restart api`.
- Codigo 137 en el contenedor api:
  - Falta de memoria. Aumenta RAM en Docker Desktop.
- Cambios de credenciales:
  - Actualiza `.env.docker` y reinicia contenedores.

## Uso sin Docker (resumen)

Si no usas Docker, el flujo recomendado es:
- Crear entorno conda
- Iniciar Neo4j Desktop
- Ejecutar `scripts/run.ps1`
- Ver [SETUP.md](SETUP.md) para primera vez
- Ver [USO_DIARIO.md](USO_DIARIO.md) para uso diario

## Notas

- El frontend puede seguir ejecutandose con Live Server en local.
- Para produccion, considera un reverse proxy y variables seguras.
