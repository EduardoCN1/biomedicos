# Troubleshooting

Problemas frecuentes al instalar y usar el proyecto con Docker Compose. Para la instalación, ver [DOCKER.md](DOCKER.md).

## Herramientas de Diagnóstico

Antes de buscar un problema concreto, estas herramientas suelen indicar la causa:

```powershell
docker compose ps -a                        # Estado de los servicios (seed debe estar "Exited (0)")
docker compose logs -f                      # Registros de todos los servicios
docker compose logs api recommender ml-validator
Invoke-RestMethod http://localhost:5000/pipeline/health   # RabbitMQ y consumidor de la API
```

- **Consola de RabbitMQ** (http://localhost:15672, `guest`/`guest`): pestaña **Queues** para ver si los mensajes se acumulan en alguna cola.
- **Neo4j Browser** (http://localhost:7474): para comprobar los datos (ver [DATABASE.md](DATABASE.md#verificar-los-datos)).
- **Herramientas de desarrollo del navegador** (F12): pestañas **Console** y **Network** para ver errores de JavaScript y las llamadas a la API.

---

## Instalación y Arranque

### 1. Error: "Cannot connect to the Docker daemon"

**Causa:** Docker Desktop no está en ejecución.

**Solución:** Abrir Docker Desktop, esperar a que indique que está en ejecución y repetir el comando.

### 2. Error: "ports are not available" o "port is already allocated"

**Síntomas (Windows):**
```
ports are not available: exposing port TCP 0.0.0.0:5500 -> 127.0.0.1:0:
listen tcp 0.0.0.0:5500: bind: Only one usage of each socket address
(protocol/network address/port) is normally permitted.
```

**Causa:** Otro programa usa ese puerto.

**Soluciones:**

a) **Puerto 5500 (aplicación web):** cambiarlo en `.env` y volver a levantar:
```ini
FRONTEND_PORT=5501
```
```powershell
docker compose up -d
```

b) **Resto de puertos (5000, 5672, 7474, 7687, 15672):** identificar el programa y cerrarlo:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000 -State Listen).OwningProcess
```

c) **macOS, puerto 5000:** lo usa el Receptor AirPlay. Se desactiva en Ajustes del Sistema → General → AirDrop y Handoff.

### 3. Error: "dependency failed to start: container biomedicos-neo4j ..."

**Síntomas:** El mensaje termina en `is unhealthy` o en `exited (1)`, y el resto de servicios no arranca.

**Causas y soluciones:**
- **Contraseña de menos de 8 caracteres** en `.env`: Neo4j 5 no arranca. Usar una más larga.
- **Contraseña cambiada después de crear el volumen:** Neo4j conserva la original y la comprobación de salud falla. Recrear el volumen (los datos se recargan desde los CSV):
  ```powershell
  docker compose down -v
  docker compose up -d
  ```
- **Otros casos:** revisar `docker compose logs neo4j`.

### 4. `seed` termina con error

**Diagnóstico:**
```powershell
docker compose logs seed
```

El mensaje `[ERROR]` indica la causa: CSV no encontrado o fallo al importar. La importación se hace en una sola transacción, así que un error no deja datos a medias. Corregir la causa y ejecutar `docker compose up -d`.

### 5. Los cambios de código no se reflejan

- **Backend, microservicios, scripts o dependencias:** la imagen se construyó antes del cambio. Ejecutar `docker compose up -d --build`.
- **Frontend:** el navegador puede estar usando una copia en caché. Recargar con `Ctrl+F5`.

---

## Funcionamiento

### 6. La API devuelve error 500 con "Unable to retrieve routing information"

**Síntomas:** En `docker compose logs api`:
```
neo4j.exceptions.ServiceUnavailable: Unable to retrieve routing information
```

**Causa:** Neo4j se reinició (o aún estaba arrancando) mientras la API seguía en marcha. La primera consulta posterior falla porque la API intenta usar la conexión anterior; las siguientes ya funcionan. No tiene relación con la terminal desde la que se ejecutan los comandos.

**Solución:** Repetir la consulta. Si persiste, comprobar que Neo4j está `healthy` (`docker compose ps`) y reiniciar la API:
```powershell
docker compose restart api
```

### 7. Aviso "Modo degradado" en la página

**Causa:** El pipeline de microservicios no respondió (RabbitMQ, el recomendador o el validador no están disponibles, o el trabajo no terminó en 60 segundos). La página consultó directamente a la API y muestra resultados **sin validar**.

**Diagnóstico:**
```powershell
docker compose ps
Invoke-RestMethod http://localhost:5000/pipeline/health
docker compose logs recommender ml-validator
```

`/pipeline/health` debe indicar `"rabbitmq": "up"` y `"consumer": "running"`. Si algún servicio está detenido: `docker compose up -d`.

### 8. "No se encontraron tratamientos para estos parámetros"

**Causas posibles:**
- **Neo4j no tiene datos:** comprobar `docker compose logs seed` y el conteo de nodos (ver [DATABASE.md](DATABASE.md#verificar-los-datos)).
- **La combinación T/N/M no tiene estadios con tratamientos en los datos.** Probar con una combinación conocida, por ejemplo T1, N0, M0.
- **Todos los tratamientos eran quirúrgicos** y se indicó que la paciente no desea cirugía: se filtran Surgery, Lumpectomy y Mastectomy.

### 9. La página se ve sin estilos o no responde al pulsar botones

**Causa:** No se pudieron cargar Bootstrap, jQuery o Toastr, que se descargan desde CDN.

**Solución:** Comprobar la conexión a internet y, en la pestaña **Network** de las herramientas de desarrollo (F12), que no haya errores al cargar `cdnjs.cloudflare.com` o `code.jquery.com` (pueden estar bloqueados por un proxy o un bloqueador de contenido).

### 10. La página no se conecta a la API (error de red o CORS)

**Síntomas:** En la consola del navegador aparecen errores al llamar a `http://127.0.0.1:5000/...`.

**Soluciones:**
- Comprobar que la API responde: `Invoke-RestMethod http://localhost:5000/` debe devolver `"En ejecución"`.
- El frontend llama a la API en `http://127.0.0.1:5000`, así que la página debe abrirse en el mismo equipo donde corre Docker.

---

## Tests

### 11. Fallan los tests de `pytest`

Los tests usan Neo4j con datos. Levantar el proyecto antes de ejecutarlos:
```powershell
docker compose up -d
docker compose run --rm api python -m pytest tests -v
```

### 12. `test-pipeline.ps1` termina con "TIMEOUT"

El trabajo no llegó a completarse en 30 segundos. Revisar los registros que el propio script muestra en el paso 3 y el estado de los servicios (ver [problema 7](#7-aviso-modo-degradado-en-la-página)).

---

## Git Bash

### 13. Error: "C:/Program Files/Git/... is not an existing directory"

**Causa:** Git Bash convierte los argumentos que empiezan por `/` en rutas de Windows, por ejemplo `--to-path=/backups`.

**Solución:** Usar PowerShell o anteponer `MSYS_NO_PATHCONV=1` al comando:
```bash
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps neo4j neo4j-admin database dump neo4j --to-path=/backups
```

---

## Checklist de Diagnóstico

- [ ] Docker Desktop está en ejecución
- [ ] `docker compose ps -a` muestra todos los servicios en marcha y `seed` como `Exited (0)`
- [ ] `biomedicos-neo4j` y `biomedicos-rabbitmq` aparecen como `(healthy)`
- [ ] `Invoke-RestMethod http://localhost:5000/` responde `"En ejecución"`
- [ ] `Invoke-RestMethod http://localhost:5000/pipeline/health` indica `"rabbitmq": "up"`
- [ ] Neo4j tiene 134 nodos (ver [DATABASE.md](DATABASE.md#verificar-los-datos))
- [ ] La página abre en http://localhost:5500 (o el puerto de `FRONTEND_PORT`)
- [ ] La consola del navegador (F12) no muestra errores

Si todo pasa el checklist pero sigue sin funcionar, guardar la salida de `docker compose ps -a` y `docker compose logs` para analizarla.
