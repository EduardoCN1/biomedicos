# Instalación y Uso con Docker Compose

Esta guía describe cómo instalar y ejecutar el proyecto completo (incluyendo todos los microservicios) utilizando Docker y Docker Compose.

## Requisitos Previos

Antes de comenzar, debe instalar:

1. **Docker Desktop** (incluye Docker Engine y Docker Compose)
   - Descargar desde: https://www.docker.com/products/docker-desktop
   - Instalar siguiendo las instrucciones de instalación estándar
   - Verificar instalación: `docker --version` y `docker compose version`

2. **Git** (para clonar el repositorio)
   - Descargar desde: https://git-scm.com/
   - Verificar instalación: `git --version`

3. **Recursos del sistema:**
   - Mínimo 4 GB de RAM disponibles para Docker
   - Puertos libres: 5000, 5001, 5002, 5672, 7474, 7687, 15672
   - Al menos 1 GB de espacio en disco

## Contenedores Incluidos

El archivo `docker-compose.yml` configura automáticamente los siguientes servicios:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| API Principal | 5000 | Flask + Neo4j (orquestación) |
| Recommender Service | 5001 | Generador de recomendaciones (ML) |
| ML Validator Service | 5002 | Validador de patrones oncológicos |
| RabbitMQ | 5672 (AMQP) / 15672 (Admin) | Message broker para comunicación asincrónica |
| Neo4j | 7474 (Browser) / 7687 (Bolt) | Base de datos de grafos TNM |

## Instalación Inicial

### Paso 1: Clonar el Repositorio

```powershell
git clone https://github.com/EduardoCN1/biomedicos.git
cd biomedicos
```

### Paso 2: Crear Archivo de Configuración

Copiar el archivo de ejemplo a `.env`:

```powershell
Copy-Item .env.example .env
```

El archivo `.env` contiene las variables de entorno necesarias. Los valores por defecto son adecuados para una instalación local con Docker.

### Paso 3: Construir y Levantar los Servicios

```powershell
docker compose up --build
```

Este comando realiza las siguientes acciones:
- Descarga las imágenes de Docker necesarias (RabbitMQ, Neo4j)
- Construye la imagen personalizada del proyecto
- Crea y levanta todos los contenedores
- Configura las redes de comunicación entre servicios

**Tiempo estimado:** 3-5 minutos (depende de la velocidad de descarga)

Una vez completado, debe ver en la terminal mensajes similares a:

```
biomedicos-rabbitmq      | Ready to accept connections
biomedicos-neo4j         | Started
biomedicos-api           | Running on http://0.0.0.0:5000
biomedicos-recommender   | Connected to RabbitMQ
biomedicos-ml-validator  | Connected to RabbitMQ
```

### Paso 4: Verificar la Instalación

Verificar que todos los servicios están en ejecución:

```powershell
docker ps
```

Debe mostrar 5 contenedores activos. Alternativamente, probar la conectividad:

```powershell
# Verificar que la API responde
Invoke-RestMethod http://localhost:5000/

# Resultado esperado: "En ejecución"
```

## Prueba del Proyecto

### Acceder a la Aplicación Web

Abrir en el navegador:

```
http://localhost:5500/frontend/index.html
```

**Nota:** El frontend requiere tener un servidor HTTP local. Si no está disponible, puede acceder directamente a través de:
- Click derecho en `frontend/index.html` → "Open with Live Server" (en VS Code)
- O usar Python: `python -m http.server 5500 --directory frontend`

### Realizar una Prueba Funcional

1. En la aplicación web, llenar el formulario con valores TNM:
   - T (Tumor): Seleccionar T1 o T2
   - N (Nódulos): Seleccionar N0 o N1
   - M (Metástasis): Seleccionar M0

2. Hacer click en el botón "Enviar"

3. Observar los resultados:
   - Recomendaciones médicas
   - Pruebas recomendadas
   - Opciones de tratamiento

### Monitorear los Servicios

**RabbitMQ Admin Console:**
```
http://localhost:15672/
Usuario: guest
Contraseña: guest
```

Aquí puede observar:
- Colas de mensajes activas
- Mensajes procesados por cada cola
- Consumidores conectados

**Neo4j Browser:**
```
http://localhost:7474/browser
Usuario: neo4j
Contraseña: password
```

Aquí puede ejecutar consultas Cypher sobre la base de datos TNM:
```cypher
MATCH (n) RETURN n LIMIT 25
```

## Uso Diario

### Iniciar los Servicios

```powershell
docker compose up
```

Sin la opción `--build`, utiliza las imágenes ya construidas, lo que es más rápido.

### Detener los Servicios

```powershell
docker compose down
```

Esto detiene todos los contenedores pero conserva los datos en los volúmenes de Docker.

### Ver Logs en Tiempo Real

```powershell
# Todos los servicios
docker compose logs -f

# Un servicio específico
docker compose logs -f api
docker compose logs -f recommender
docker compose logs -f neo4j
```

### Reiniciar un Servicio Específico

```powershell
docker compose restart api
```

## Gestión de Datos

### Importar Datos desde CSV

```powershell
docker compose exec api python scripts/import_csv.py
```

Este script:
1. Lee los archivos CSV desde `data/nodos.csv` y `data/relaciones.csv`
2. Conecta a Neo4j
3. Crea todos los nodos y relaciones en la base de datos

### Restaurar desde Copia de Seguridad

1. Colocar el archivo `.dump` en `data/backups/`

2. Detener el servicio Neo4j:
```powershell
docker compose stop neo4j
```

3. Restaurar la copia de seguridad:
```powershell
docker compose run --rm neo4j neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true
```

4. Reiniciar Neo4j:
```powershell
docker compose start neo4j
```

### Crear Copia de Seguridad

```powershell
docker compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups
```

El archivo será guardado en `data/backups/` con el nombre `neo4j.dump`.

## Limpiar y Resetear

### Detener y Eliminar Todo (Conservar Datos)

```powershell
docker compose down
```

### Detener y Borrar Todo (Incluir Datos)

```powershell
docker compose down -v
```

**Advertencia:** Este comando elimina todos los volúmenes, incluyendo los datos de Neo4j. Use solo si desea empezar desde cero.

### Limpiar Imágenes no Utilizadas

```powershell
docker image prune -a
```

## Solucionar Problemas

### Error: "Cannot connect to Docker daemon"

**Causa:** Docker Desktop no está ejecutándose.

**Solución:**
- Abrir Docker Desktop
- Esperar a que aparezca el ícono de Docker en la bandeja del sistema
- Intentar nuevamente

### Error: "Port 5000 is already in use"

**Causa:** Otro proceso está usando el puerto 5000.

**Solución opción 1:** Cambiar el puerto en `.env`:
```ini
PORT=5001
```

**Solución opción 2:** Terminar el proceso que ocupa el puerto:
```powershell
Get-NetTCPConnection -LocalPort 5000 | Stop-Process -Force
```

### Error: "Timeout waiting for Neo4j"

**Causa:** Neo4j tarda en inicializarse.

**Solución:** Esperar 30-60 segundos adicionales y revisar logs:
```powershell
docker compose logs neo4j
```

### Los microservicios no se conectan a RabbitMQ

**Causa:** RabbitMQ no ha terminado de inicializarse.

**Solución:** Reiniciar los servicios:
```powershell
docker compose restart recommender ml-validator
```

### Cambios de código no se reflejan

**Causa:** Las imágenes fueron construidas antes del cambio.

**Solución:** Reconstruir:
```powershell
docker compose down
docker compose up --build
```

## Alternativa: Instalación Sin Docker

Si prefiere instalar el proyecto sin Docker, consulte:
- [SETUP.md](SETUP.md) - Instalación inicial con Conda y Neo4j Desktop
- [USO_DIARIO_SIN_DOCKER.md](USO_DIARIO_SIN_DOCKER.md) - Uso diario sin Docker

## Referencias Adicionales

- [MICROSERVICIOS.md](MICROSERVICIOS.md) - Arquitectura detallada de microservicios y RabbitMQ
- [DATABASE.md](DATABASE.md) - Gestión de datos en Neo4j
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solución de problemas avanzados
- [Documentación oficial Docker](https://docs.docker.com/)
- [Documentación oficial Docker Compose](https://docs.docker.com/compose/)
