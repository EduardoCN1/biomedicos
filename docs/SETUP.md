# Guía de Instalación y Setup

## Requisitos Previos

- **Windows 10/11** (sistemas similares adaptar comandos)
- **Neo4j 5.x** instalado y ejecutándose en `127.0.0.1:7687`
- **Acceso a Internet** para descargar paquetes

## Paso 1: Descargar Miniforge

Miniforge es un instalador de Conda minimalista y eficiente.

1. Ir a: https://github.com/conda-forge/miniforge/releases
2. Descargar **Miniforge3-Windows-x86_64.exe** (última versión)
3. Ejecutar el instalador
   - Aceptar términos
   - Seleccionar **"Add Miniforge to the system PATH"**
   - Seleccionar **"Initialize Miniforge by running `conda init`"**
   - Completar instalación

## Paso 2: Verificar Conda

Abrir PowerShell y ejecutar:

```powershell
conda --version
```

Debe mostrar algo como: `conda 23.9.0`

Si no funciona:
```powershell
python -m conda --version
```

O si es necesario, reiniciar VS Code y PowerShell.

## Paso 3: Ejecutar Setup Script

En la carpeta del proyecto (`d:\Proyecto_Practica\biomedicos`):

```powershell
.\scripts\setup.ps1
```

Este script:
1. ✓ Verifica Conda está instalado
2. ✓ Crea entorno `biomedicos` con Python 3.11
3. ✓ Instala numpy y pandas desde conda-forge (binarios)
4. ✓ Instala resto de dependencias desde requirements.txt

**Salida esperada:**
```
[✓] Conda encontrado
[✓] Entorno biomedicos creado
[✓] Dependencias instaladas
```

Si hay errores, ver sección **Troubleshooting**.

## Paso 4: Configurar Variables de Entorno

### Opción A: Archivo .env (Recomendado)

1. Copiar `.env.example` a `.env`:

```powershell
Copy-Item .env.example .env
```

2. Editar `.env` con credenciales reales:

```ini
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password_aqui
HOST=0.0.0.0
PORT=5000
ENVIRONMENT=development
```

### Opción B: Variables de Sistema (Alternativa)

En PowerShell como administrador:

```powershell
[System.Environment]::SetEnvironmentVariable("NEO4J_PASSWORD", "tu_password", "User")
[System.Environment]::SetEnvironmentVariable("PORT", "5000", "User")
```

Luego reiniciar VS Code.

## Paso 5: Arrancar la API

### Método 1: Script automático (Recomendado)

```powershell
#Antes de ejecutar debe iniciar la instancia de la base de datos Neo4j
.\scripts\run.ps1
```

Debe mostrar:
```
[✓] Entorno 'biomedicos' activado
[✓] Variables de entorno cargadas
[✓] Iniciando servidor...
Serving on http://0.0.0.0:5000
```

### Método 2: Manual (si falla el script)

```powershell
# Activar entorno
conda activate biomedicos

# Arrancar servidor
python .\backend\run_waitress.py
```

## Paso 6: Verificar API

En otra terminal PowerShell:

```powershell
# Verificar que API está corriendo
Invoke-RestMethod http://localhost:5000/

# Debe responder: "En ejecución"
```

## Paso 7: Probar Frontend

1. Instalar extensión **Live Server** en VS Code (si no tienes)
2. Click derecho en `frontend/index.html` → "Open with Live Server"
3. Se abrirá en navegador (típicamente http://localhost:5500/frontend/index.html)
4. Probar llenando y enviando el formulario

**Validar respuesta:**
- Debe aparecer JSON con Stage, Tests y Treatments

## Paso 8: Ejecutar Tests

```powershell
conda activate biomedicos
pip install pytest  # Si no está instalado
python -m pytest tests/test_api.py -v
```

Debe ver tests PASSED.

## Troubleshooting

### Error: "Conda no encontrado"

**Solución:**
1. Verificar que Miniforge instaló correctamente
2. Reiniciar VS Code completamente
3. Ejecutar: `python -m conda --version`

### Error: "Módulo 'numpy' no encontrado"

**Solución:**
```powershell
    1.conda activate biomedicos
    2.conda install -c conda-forge numpy pandas
```
##  Error: "Unable to retrieve routing information"
**Verificar:** 
```Neo4j
    1. Revisar en interfaz de Neo4j que la instancia de la base de datos esté iniciada
```
**Solución:**
```Powershell
    1. Detener con Ctrl+c en caso de esté ejecutando el servidor
    2. Cerrar terminal 
    3. Abrir una nueva
    4. Ejecutar de nuevo el script '.\scripts\run.ps1'
```
Nota: Esto  puede demorar, esperar un par de minutos y depsues repetir en caso que el mismo error esté presente.

### Error: "Neo4j connection refused"

**Verificar:**
1. Neo4j está corriendo: `http://localhost:7474` (debe abrirse en navegador)
2. Usuario/password correctos en `.env`
3. URI es correcta: `neo4j://127.0.0.1:7687`

### Error: "Port 5000 already in use"

**Soluciones:**
- Cambiar PORT en `.env`:
  ```ini
  PORT=5001
  ```
- O matar proceso:
  ```powershell
  Get-Process -Name "python" | Stop-Process
  ```

### JavaScript error en navegador: "AJAX no funciona"

**Verificar:**
1. API está corriendo en puerto 5000
2. URL en `frontend/js/entradas.js` es `http://127.0.0.1:5000`
3. Backend permite CORS (backend/api.py debe tener `CORS(app)`)

### Error: "OSError: [WinError 10013]"

**Causa:** Puerto bloqueado por otra aplicación
**Solución:** Ver "Port 5000 already in use" arriba

## Estructura de Carpetas

```
biomedicos/
├── backend/              # API y lógica
├── frontend/             # HTML + JS + CSS
├── data/                 # CSVs y backups
├── scripts/              # setup.ps1, run.ps1
├── tests/                # test_api.py
├── docs/                 # Esta documentación
├── .env.example
├── requirements.txt
└── README.md
```

## Siguientes Pasos

Después de completar setup:

1. **Cargar datos**: Si tienes datos en CSV nuevos, actualizar `data/nodos.csv` y `data/relaciones.csv`
2. **Crear cuenta**: Neo4j web UI en http://localhost:7474 si es primera vez
3. **Importar CSVs**: Ejecutar script de importación (no reflejado aún)
4. **Desarrollar**: Editar `backend/api.py` para nuevas rutas
5. **Frontend**: Actualizar `frontend/js/entradas.js` para nuevos campos

## Comandos Útiles

```powershell
# Activar/desactivar entorno
conda activate biomedicos
conda deactivate

# Ver entornos disponibles
conda env list

# Instalar paquete individual
conda install -c conda-forge nombre_paquete

# O usar pip
pip install nombre_paquete

# Ver versión Python
python --version

# Ver paquetes instalados
pip list

# Ejecutar solo backend (sin Live Server)
python .\backend\run_waitress.py

# Tests con output verbose
python -m pytest tests/test_api.py -vvv
```

## Soporte

Para reportar errores:
1. Proporcionar **mensaje de error completo**
2. Indicar **SO y versión Python**
3. Adjuntar **salida de `conda env list`**
4. Verificar que **Neo4j está corriendo**
