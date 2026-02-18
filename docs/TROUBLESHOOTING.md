# Troubleshooting Avanzado

## Problemas Comunes y Soluciones

### 1. Error: "Conda no encontrado" o "conda: el término no se reconoce"

**Síntomas:**
```
conda: el término no se reconoce como el nombre de un cmdlet, función, script
```

**Soluciones:**

a) **Reiniciar VS Code completamente:**
```powershell
# Cerrar todas las instancias de PowerShell
# Cerrar VS Code
# Abrir VS Code nuevamente
# Abrir PowerShell integrada
```

b) **Ejecutar conda init:**
```powershell
# Si tienes Miniforge/Anaconda instalado
python -m conda init powershell
# Luego cerrar y abrir PowerShell
```

c) **Agregar a PATH manualmente:**
- En Windows, buscar "Variables de entorno"
- Editar Path
- Agregar: `C:\Users\[TuUsuario]\Miniforge3\Scripts`

d) **Verificar instalación:**
```powershell
# Si conda no funciona, verificar python
python --version

# Si python funciona, usar:
python -m conda --version
```

---

### 2. Error: "OSError: [WinError 10013] Access denied"

**Síntomas:**
```
An attempt was made to access a socket in a way forbidden by its access permissions
Port 5000: [WinError 10013] An attempt could not bind
```

**Causa:** Otra aplicación usa puerto 5000 o está bloqueado por firewall

**Soluciones:**

a) **Cambiar puerto:**
Editar `.env`:
```ini
PORT=5001
```

b) **Encontrar y matar proceso:** 
```powershell
# Encontrar qué usa puerto 5000
Get-NetTCPConnection -LocalPort 5000

# Matar ese proceso
Stop-Process -Id [PID] -Force
```

c) **Permitir firewall:**
- Windows Defender → Firewall → Permitir app → Python

d) **Usar otro puerto:**
En `frontend/js/entradas.js`, cambiar:
```javascript
// De:
url: 'http://127.0.0.1:5000/...'
// A:
url: 'http://127.0.0.1:5001/...'
```

---

### 3. Error: "ModuleNotFoundError: No module named 'py2neo'"

**Síntomas:**
```python
ModuleNotFoundError: No module named 'py2neo'
```

**Causa:** Dependencia no instalada en el entorno activado

**Soluciones:**

a) **Reinstalar dependencias:**
```powershell
conda activate biomedicos
pip install -r requirements.txt
```

b) **Verificar entorno activado:**
```powershell
# Debe mostrar (biomedicos) al inicio
conda env list
```

c) **Si sigue sin funcionar:**
```powershell
# Eliminar y recrear entorno
conda remove -n biomedicos --all
.\scripts\setup.ps1
```

---

### 4. Error: "Neo4j connection refused" o timeout

**Síntomas:**
```
Connection refused
[Errno 111] Connection refused  
socket.timeout: timed out
```

**Causa:** Neo4j no está corriendo o credenciales incorrectas

**Soluciones:**

a) **Verificar Neo4j está corriendo:**
```powershell
# Abrir navegador
http://localhost:7474/

# Debe mostrar la interfaz web de Neo4j
```

b) **Si no abre:**
```powershell
# Si Neo4j está instalado localmente
neo4j start

# O si está en Docker
docker start neo4j
```

c) **Verificar credenciales en .env:**
```ini
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tucontraseña123
```

d) **Cambiar contraseña:**
- Ir a http://localhost:7474
- Login default: neo4j / neo4j
- Cambiar contraseña
- Actualizar `.env` con nueva contraseña

e) **Verificar URI format:**
```
 Correcto: neo4j://127.0.0.1:7687
 Incorrecto: bolt://127.0.0.1:7687 (versiones antiguas)
 Incorrecto: http://127.0.0.1:7474 (web UI, no DB)
```

---

### 5. Error: "No module named 'backend.config'" en backend/api.py

**Síntomas:**
```python
ModuleNotFoundError: No module named 'backend.config'
```

**Solución:**

a) **Verificar `__init__.py` existe:**
```powershell
# Debe existir:
ls backend/__init__.py

# Si no existe:
echo "" > backend/__init__.py
```

b) **Ejecutar desde directorio correcto:**
```powershell
#  INCORRECTO - desde subfolder
cd backend
python run_waitress.py

#  CORRECTO - desde raíz
cd ..
python backend/run_waitress.py

#  O usar script:
.\scripts\run.ps1
```

---

### 6. Frontend no se conecta a Backend (error 404 o CORS)

**Síntomas:**
```javascript
// En consola del navegador:
Access to XMLHttpRequest at 'http://127.0.0.1:5000/...' from origin 'http://localhost:5500' 
has been blocked by CORS policy
```

**Soluciones:**

a) **Verificar Backend está corriendo:**
```powershell
# En una terminal
.\scripts\run.ps1

# En otra terminal, verificar
Invoke-RestMethod http://localhost:5000/
```

b) **Verificar URL en entradas.js:**
```javascript
// frontend/js/entradas.js
// Buscar y verificar sea:
url: 'http://127.0.0.1:5000'

// NO:
url: 'localhost:5000'      # Incorrecto (no es local)
url: 'example.com:5000'    # Incorrecto
url: '27.0.0.1:5000'       # Incorrecto (typo)
```

c) **Verificar CORS está habilitado:**
```python
# En backend/api.py debe estar:
from flask_cors import CORS
CORS(app)
```

d) **Verificar Live Server puerto:**
```javascript
// Live Server suele usar puerto 5500
// Si no, verificar en VSCode:
// Preferences → Extensions → Live Server → Settings
```

---

### 7. Error: "could not be translated to a valid SQL statement" (Neo4j)

**Síntomas:**
```
Syntax error in Cypher query
Invalid property
```

**Causa:** Query Cypher malformada o propiedades no existen

**Soluciones:**

a) **Verificar propiedades existen:**
```powershell
# En Neo4j Browser (http://localhost:7474)
MATCH (n:T2) RETURN n LIMIT 1
# Examina el output para ver qué propiedades tiene

# O desde PowerShell:
Invoke-RestMethod "http://localhost:5000/labels/t" | ConvertTo-Json
```

b) **Recargar datos:**
Si las propiedades faltaron al importar:
```powershell
# Limpiar Neo4j y reintentar
python scripts/import_csv.py
```

---

### 8. Error: "Errno 10048: Only one usage of each socket address"

**Síntomas:**
```
Address already in use
[Errno 10048] Only one usage of each socket address
```

**similar a #2 pero mensaje diferente**

**Soluciones:**

a) **Esperar SO libere el puerto (30 seg):**
```powershell
# Esperar y reintentar
Start-Sleep -Seconds 30
.\scripts\run.ps1
```

b) **Forzar liberar puerto:**
```powershell
# Encontrar proceso
netstat -ano | findstr :5000

# Terminar (cambiar con PID real)
taskkill /PID 12345 /F
```

---

### 9. Error: numpy/pandas compilation error en Windows

**Síntomas:**
```
error: Microsoft Visual C++ 14.0 or greater is required
fatal error C1083: Cannot open include file
```

**Solución (Usar Conda):**
```powershell
# Desinstalar una versión rota
pip uninstall numpy pandas

# Instalar desde conda-forge (binarias)
conda install -c conda-forge numpy pandas

# Verificar:
python -c "import numpy; print(numpy.__version__)"
```

---

### 10. Error: "MIME type ... is not supported" en frontend

**Síntomas:**
```
The script from "file:///C:/path/to/file.js" was not loaded because its MIME type 
is not text/javascript
```

**Causa:** Rutas relativas incorrectas en HTML

**Solución:**

a) **Usar Live Server (no file://):**
-  Click directo en index.html
-  Click derecho en index.html → "Open with Live Server"

b) **Verificar rutas en index.html:**
```html
<!-- Si index.html está en frontend/ -->
<!--  CORRECTO -->
<link href="css/stilous.css" rel="stylesheet">
<script src="js/entradas.js"></script>

<!--  INCORRECTO -->
<link href="/css/stilous.css" rel="stylesheet">
<link href="../css/stilous.css" rel="stylesheet">
```

---

## Herramientas de Debugging

### 1. Verificar salud del Backend

```powershell
# Test básico
Invoke-RestMethod http://localhost:5000/

# Test completo
$response = Invoke-RestMethod "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0"
$response | ConvertTo-Json -Depth 10
```

### 2. Ver logs de Neo4j

```powershell
# Si Neo4j está en carpeta local
Get-Content $env:NEO4J_HOME\logs\debug.log -Tail 50
```

### 3. Debug en navegador
```javascript
// Abrir Console en Developer Tools (F12)
// Ver errores en red (Network tab)
// Ver AJAX calls y respuestas
```

### 4. Verificar puertos en uso

```powershell
# Ver todos los puertos en uso
Get-NetTCPConnection -State Listen | ft -AutoSize

# O específico
netstat -ano | findstr :5000 | findstr :5500 | findstr :7687
```

---

## Checklist de Diagnóstico

Antes de reportar un erro, verificar:

- [ ] `conda activate biomedicos` está ejecutado
- [ ] `.env` existe y tiene credenciales correctas
- [ ] `neo4j://127.0.0.1:7687` es accesible (http://localhost:7474)
- [ ] `python .\backend\run_waitress.py` arranca sin errores
- [ ] `Invoke-RestMethod http://localhost:5000/` responde
- [ ] `frontend/index.html` abre con Live Server (no file://)
- [ ] `frontend/js/entradas.js` URL es `http://127.0.0.1:5000`
- [ ] Consola del navegador (F12) no muestra errores JavaScript
- [ ] Network tab (Dev Tools) muestra requests a 5000
- [ ] Neo4j tiene datos (`scripts/import_csv.py` ejecutado)

Si todo pasa el checklist pero sigue no funcionando:
1. Copia ALL output de consola y error
2. Ejecuta: `python --version`, `conda --version`, `pip list`
3. Verifica `.env` (sin credenciales reales)
4. Contacta con output completo
