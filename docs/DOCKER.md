# Instalación y Uso con Docker Compose

Esta guía describe cómo instalar y ejecutar el proyecto completo con Docker Compose. Es la única forma de instalación: no hace falta instalar Python, Neo4j ni Node.js en el equipo.

## Requisitos Previos

1. **Docker Desktop** (incluye Docker Engine y Docker Compose)
   - Descargar desde: https://www.docker.com/products/docker-desktop
   - En Windows utiliza WSL2; el instalador lo configura.
   - Verificar instalación: `docker --version` y `docker compose version`

2. **Git** (para clonar el repositorio)
   - Descargar desde: https://git-scm.com/
   - Verificar instalación: `git --version`

3. **Recursos del sistema:**
   - Al menos 4 GB de RAM asignados a Docker
   - Unos 2 GB de disco para las imágenes
   - Puertos libres: 5000, 5500, 5672, 7474, 7687, 15672 (el 5500 se puede cambiar, ver [Variables de entorno](#paso-2-opcional-crear-el-archivo-env))
   - Conexión a internet: la primera vez se descargan las imágenes, y la página carga Bootstrap, jQuery y Toastr desde CDN

## Servicios Incluidos

El archivo `docker-compose.yml` define los siguientes servicios:

| Servicio | Contenedor | Puerto en el equipo | Descripción |
|----------|------------|---------------------|-------------|
| `frontend` | biomedicos-frontend | 5500 | nginx que sirve la carpeta `frontend/` |
| `api` | biomedicos-api | 5000 | API Flask: recibe las consultas y publica los trabajos en RabbitMQ |
| `recommender` | biomedicos-recommender | — | Consulta Neo4j y genera las recomendaciones |
| `ml-validator` | biomedicos-ml-validator | — | Validador **simulado** de tratamientos (el modelo de ML real es trabajo futuro) |
| `seed` | biomedicos-seed | — | Carga `data/*.csv` en Neo4j si está vacío y termina |
| `rabbitmq` | biomedicos-rabbitmq | 5672 (AMQP) / 15672 (administración) | Gestor de mensajes entre la API y los microservicios |
| `neo4j` | biomedicos-neo4j | 7474 (Browser) / 7687 (Bolt) | Base de datos de grafos (Neo4j 5) |

- `recommender` y `ml-validator` no exponen puertos: solo se comunican a través de RabbitMQ.
- `api`, `seed`, `recommender` y `ml-validator` comparten la misma imagen (`biomedicos-app`), construida desde el `Dockerfile`; cada uno arranca con su propio comando.

Ver [MICROSERVICIOS.md](MICROSERVICIOS.md) para la arquitectura y el flujo de mensajes.

## Instalación Inicial

### Paso 1: Clonar el Repositorio

```powershell
git clone https://github.com/EduardoCN1/biomedicos.git
cd biomedicos
```

### Paso 2 (opcional): Crear el archivo .env

Sin `.env` el proyecto funciona con los valores por defecto. Solo hace falta para personalizar alguno de ellos:

```powershell
cp .env.example .env
```

| Variable | Por defecto | Uso |
|----------|-------------|-----|
| `NEO4J_USER` | `neo4j` | Usuario de Neo4j |
| `NEO4J_PASSWORD` | `password` | Contraseña de Neo4j (mínimo 8 caracteres) |
| `FRONTEND_PORT` | `5500` | Puerto de la aplicación web en el equipo |

La contraseña de Neo4j solo se aplica la primera vez que se crea su volumen. Para cambiarla después hay que recrear el volumen (ver [Limpiar y Resetear](#limpiar-y-resetear)).

### Paso 3: Construir y Levantar los Servicios

```powershell
docker compose up -d --build
```

Este comando, en orden:
1. Descarga las imágenes de Neo4j, RabbitMQ y nginx, y construye la imagen del proyecto (`biomedicos-app`).
2. Arranca Neo4j y RabbitMQ y espera a que superen sus comprobaciones de salud (unos 20-30 segundos).
3. Ejecuta `seed`, que carga los datos en Neo4j si la base está vacía.
4. Arranca `api`, `recommender`, `ml-validator` y `frontend`.

**Tiempo estimado:** 3-5 minutos la primera vez (depende de la velocidad de descarga); unos 30 segundos en los arranques siguientes.

Sin la opción `-d`, los registros de todos los servicios se muestran en la terminal y `Ctrl+C` detiene el proyecto.

### Paso 4: Verificar la Instalación

```powershell
docker compose ps -a
```

Debe mostrar algo similar a:

```
NAME                      STATUS
biomedicos-api            Up 2 minutes
biomedicos-frontend       Up 2 minutes
biomedicos-ml-validator   Up 2 minutes
biomedicos-neo4j          Up 2 minutes (healthy)
biomedicos-rabbitmq       Up 2 minutes (healthy)
biomedicos-recommender    Up 2 minutes
biomedicos-seed           Exited (0) 2 minutes ago
```

Que `seed` aparezca como `Exited (0)` es lo esperado: termina en cuanto carga los datos.

Los registros de arranque deben incluir estos mensajes (`docker compose logs seed api recommender ml-validator`):

```
biomedicos-seed          | [✓] Datos importados exitosamente a Neo4j
biomedicos-api           | ✓ Servidor Waitress iniciado en http://0.0.0.0:5000
biomedicos-api           | ✓ Consumidor escuchando cola: tnm.validation.result
biomedicos-recommender   | [recommender] Esperando mensajes en: tnm.recommendation.request
biomedicos-ml-validator  | [ml-validator] Esperando mensajes en: tnm.validation.request
```

En los arranques siguientes, `seed` indica en su lugar: `La base de datos ya tiene 134 nodos; no se importa nada`.

Para comprobar que la API responde:

```powershell
Invoke-RestMethod http://localhost:5000/
# Resultado esperado: "En ejecución"
```

## Prueba del Proyecto

### Aplicación Web

1. Abrir **http://localhost:5500** en el navegador.
2. Completar al menos:
   - **Antecedentes Personales:** edad, sexo, altura y peso.
   - **Estadía Tumoral:** T, N y M (por ejemplo T1, N0, M0).
3. Hacer click en **Consultar**.
4. Se muestran los estadios encontrados con sus pruebas recomendadas y opciones de tratamiento.

Si en Estadía Tumoral se indica que la paciente **no** desea cirugía, se excluyen los tratamientos quirúrgicos (Surgery, Lumpectomy, Mastectomy).

Si el pipeline de microservicios no responde, la página consulta directamente a la API y muestra el aviso «Modo degradado» (resultados sin validar).

### Prueba Automática del Pipeline

```powershell
.\scripts\test-pipeline.ps1
```

Envía una consulta TNM (T1, N0, M0), sigue el trabajo a través del recomendador y el validador, y muestra el resultado. Requiere PowerShell (en Linux/macOS, `pwsh`).

### Tests

```powershell
docker compose run --rm api python -m pytest tests -v
```

Los tests usan Neo4j con datos, así que el proyecto debe estar levantado.

### Monitorear los Servicios

**Consola de administración de RabbitMQ:**
```
http://localhost:15672/
Usuario: guest
Contraseña: guest
```

En la pestaña **Queues** se ven las tres colas del pipeline (`tnm.recommendation.request`, `tnm.validation.request`, `tnm.validation.result`), sus mensajes y sus consumidores.

**Neo4j Browser:**
```
http://localhost:7474/browser
Usuario: neo4j
Contraseña: password (o los valores de .env)
```

Aquí puede ejecutar consultas Cypher sobre la base de datos TNM:
```cypher
MATCH (n) RETURN n LIMIT 25
```

## Uso Diario

```powershell
docker compose up -d             # Iniciar (los datos de Neo4j se conservan)
docker compose down              # Detener
docker compose logs -f           # Ver registros de todos los servicios
docker compose logs -f api       # Ver registros de un servicio
docker compose restart api       # Reiniciar un servicio
```

## Aplicar Cambios de Código

| Cambio en | Qué hacer |
|-----------|-----------|
| `frontend/` | Recargar el navegador (la carpeta está montada en el contenedor) |
| `backend/`, `services/`, `scripts/`, `tests/` | `docker compose up -d --build` |
| `requirements.txt`, `requirements-dev.txt`, `Dockerfile` | `docker compose up -d --build` |
| `docker-compose.yml` o `.env` | `docker compose up -d` |
| `data/*.csv` | `docker compose down -v` y `docker compose up -d` (recarga los datos) |

## Gestión de Datos

Los datos se cargan automáticamente con el servicio `seed`. Para recargarlos, hacer copias de seguridad o restaurarlas, ver [DATABASE.md](DATABASE.md).

## Limpiar y Resetear

### Detener el Proyecto (Conservar Datos)

```powershell
docker compose down
```

### Borrar los Datos de Neo4j

```powershell
docker compose down -v
```

Elimina el volumen de Neo4j. Al volver a levantar el proyecto, `seed` recarga los datos desde los CSV. También es la forma de aplicar un cambio de contraseña de Neo4j.

### Borrar la Imagen del Proyecto

```powershell
docker image rm biomedicos-app
```

Se vuelve a construir en el siguiente `docker compose up`. Evite `docker image prune -a` si usa Docker para otros proyectos: borra todas las imágenes que no estén en uso, no solo las de este.

## Solucionar Problemas

### Error: "Cannot connect to the Docker daemon"

**Causa:** Docker Desktop no está en ejecución.

**Solución:** Abrir Docker Desktop, esperar a que indique que está en ejecución e intentar nuevamente.

### Error: "ports are not available" o "port is already allocated"

**Causa:** Otro programa usa uno de los puertos del proyecto. En Windows el mensaje completo termina en `bind: Only one usage of each socket address ... is normally permitted`.

**Solución:**
- **5500 (aplicación web):** cambiar `FRONTEND_PORT` en `.env` y ejecutar `docker compose up -d`.
- **Resto de puertos:** cerrar el programa que lo usa. Para identificarlo en Windows:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 5000 -State Listen).OwningProcess
  ```
- En macOS, el puerto 5000 lo usa el Receptor AirPlay (se desactiva en Ajustes del Sistema → General → AirDrop y Handoff).

### Error: "dependency failed to start: container biomedicos-neo4j ..."

El mensaje termina en `is unhealthy` o en `exited (1)`.

**Causas habituales:**
- La contraseña de `.env` tiene menos de 8 caracteres: Neo4j no arranca.
- La contraseña de `.env` cambió después de crear el volumen: Neo4j conserva la anterior. Ejecutar `docker compose down -v` y volver a levantar.

**Diagnóstico:**
```powershell
docker compose logs neo4j
```

### `seed` termina con error

```powershell
docker compose logs seed
```

El mensaje `[ERROR]` indica la causa (CSV no encontrado o fallo al importar). La importación se hace en una sola transacción, así que un error no deja datos a medias.

### Los cambios de código no se reflejan

**Causa:** La imagen se construyó antes del cambio.

**Solución:** `docker compose up -d --build`

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para más casos.

## Referencias Adicionales

- [MICROSERVICIOS.md](MICROSERVICIOS.md) - Arquitectura de microservicios y RabbitMQ
- [DATABASE.md](DATABASE.md) - Gestión de datos en Neo4j
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solución de problemas
- [Documentación oficial de Docker](https://docs.docker.com/)
- [Documentación oficial de Docker Compose](https://docs.docker.com/compose/)
