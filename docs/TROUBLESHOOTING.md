# Troubleshooting

Problemas frecuentes al instalar y usar el proyecto con Docker Compose. Para la instalación, ver [DOCKER.md](DOCKER.md).

## Herramientas de Diagnóstico

Antes de buscar un problema concreto, estas herramientas suelen indicar la causa:

```powershell
docker compose ps -a                        # Estado de los servicios (seed debe estar "Exited (0)")
docker compose logs -f                      # Registros de todos los servicios
docker compose logs api recommender ml-validator
Invoke-RestMethod http://localhost:5000/pipeline/health   # RabbitMQ y consumidor de la API
Invoke-RestMethod http://localhost:5000/pipeline/debug    # Todos los trabajos y su estado
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

a) **Puerto 5500 (aplicación web) o 5000 (API):** cambiarlo en `.env` y volver a levantar. En macOS, el 5000 suele estar ocupado por el Receptor AirPlay.
```ini
FRONTEND_PORT=5501
API_PORT=5001
```
```powershell
docker compose up -d
```
La página no se ve afectada por `API_PORT`, porque llama a la API a través de `/api`. Para `test-pipeline.ps1`, indicar el nuevo puerto: `.\scripts\test-pipeline.ps1 -ApiUrl http://localhost:5001`.

b) **Resto de puertos (5672, 7474, 7687, 15672):** identificar el programa y cerrarlo:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 7474 -State Listen).OwningProcess
```

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

El mensaje `[ERROR]` indica la causa:
- **"... con 'label' que no es texto":** el CSV no cumple el [formato de los datos](DATABASE.md#formato-de-los-datos). El mensaje enumera los nodos afectados; hay que corregirlos en `data/nodos.csv`. No se importa nada, y `api` y `recommender` no arrancan hasta que se corrija.
- **CSV no encontrado o fallo al importar.** La importación se hace en una sola transacción, así que un error no deja datos a medias.

Corregir la causa y ejecutar `docker compose up -d`.

### 5. Los cambios de código no se reflejan

- **Backend, microservicios, scripts o dependencias:** la imagen se construyó antes del cambio. Ejecutar `docker compose up -d --build`.
- **Frontend:** el navegador puede estar usando una copia en caché. Recargar con `Ctrl+F5`.
- **`nginx/default.conf`:** Compose no detecta cambios en archivos montados. Ejecutar `docker compose restart frontend`.

---

## Funcionamiento

### 6. Errores "Unable to retrieve routing information" o "Cannot resolve address neo4j:7687"

**Síntomas:** La API devuelve error 500 en `/get_stage_info` o `/labels/*`, o los trabajos del pipeline terminan como `failed` con `recommender: ...` en el campo `error`. En los registros aparece `neo4j.exceptions.ServiceUnavailable`.

**Causa:** Neo4j no está disponible. Si solo se reinició, la API y el recomendador reintentan automáticamente durante unos segundos y la consulta termina bien (solo tarda un poco más). Si el error persiste, Neo4j está detenido o no arranca. No tiene relación con la terminal desde la que se ejecutan los comandos.

**Solución:** Comprobar que Neo4j está `healthy` (`docker compose ps`) y, si no, levantarlo y revisar sus registros:
```powershell
docker compose up -d
docker compose logs neo4j
```

### 7. Aviso "No se pudo completar la evaluación" en la página

**Causa:** El pipeline de microservicios no completó la consulta: RabbitMQ no estaba disponible, un microservicio falló al procesarla (y lo avisó), o el trabajo no terminó en 60 segundos (por ejemplo, porque un microservicio está detenido). La página no muestra tratamientos para no presentar resultados sin evaluar. El motivo técnico aparece en la consola del navegador (F12).

**Diagnóstico:**
```powershell
docker compose ps
Invoke-RestMethod http://localhost:5000/pipeline/health
docker compose logs api recommender ml-validator
```

- `/pipeline/health` debe indicar `"rabbitmq": "up"` y `"consumer": "running"`.
- Si un microservicio falló, la API registra `✗ Fallo recibido para job_id=...` con el motivo, que también aparece en el campo `error` de `/pipeline/result/<job_id>`.
- Si algún servicio está detenido: `docker compose up -d`.

### 8. "No se encontraron tratamientos para estos parámetros"

**Causas posibles:**
- **Neo4j no tiene datos:** comprobar `docker compose logs seed` y el conteo de nodos (ver [DATABASE.md](DATABASE.md#verificar-los-datos)).
- **La combinación T/N/M no tiene estadios con tratamientos en los datos.** Probar con una combinación conocida, por ejemplo T1, N0, M0.
- **Todos los tratamientos eran quirúrgicos** y se indicó que la paciente no desea cirugía: se filtran Surgery, Lumpectomy y Mastectomy.

### 9. La página se ve sin estilos o no responde al pulsar botones

**Causa:** No se pudieron cargar Bootstrap, jQuery o Toastr, que se descargan desde CDN.

**Solución:** Comprobar la conexión a internet y, en la pestaña **Network** de las herramientas de desarrollo (F12), que no haya errores al cargar `cdnjs.cloudflare.com` o `code.jquery.com` (pueden estar bloqueados por un proxy o un bloqueador de contenido).

### 10. La página no se conecta a la API (error 502)

**Síntomas:** En la pestaña **Network** del navegador, las llamadas a `/api/...` responden `502 Bad Gateway`.

**Causa:** nginx no puede llegar a la API: el servicio `api` está detenido o no ha terminado de arrancar (por ejemplo, porque `seed` falló).

**Soluciones:**
- Comprobar el estado: `docker compose ps -a`. Si `api` no está en marcha, revisar `docker compose logs seed api` y ejecutar `docker compose up -d`.
- Comprobar que la API responde directamente: `Invoke-RestMethod http://localhost:5000/` debe devolver `"En ejecución"`.
- Si se modificó `nginx/default.conf`, reiniciar nginx: `docker compose restart frontend`.

---

## Tests

### 11. Fallan los tests de `pytest`

Los tests usan Neo4j con datos. Levantar el proyecto antes de ejecutarlos:
```powershell
docker compose up -d
docker compose run --rm api python -m pytest tests -v
```

### 12. `test-pipeline.ps1` termina con "TIMEOUT"

El trabajo no llegó a completarse en 30 segundos. Revisar los registros que el propio script muestra en el paso 3 y el estado de los servicios (ver [problema 7](#7-aviso-no-se-pudo-completar-la-evaluación-en-la-página)).

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
