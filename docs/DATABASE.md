# Gestión de Base de Datos Neo4j

Esta guía explica cómo poblar y respaldar tu base de datos Neo4j.

##  Dos Formas de Poblar Neo4j

Tienes **dos opciones** para cargar datos en Neo4j. **No necesitas hacer ambas**, elige la que aplique:

### Opción A: Importar desde CSV (Desarrollo)

**Cuándo usar:**
-  Primera instalación y solo tienes archivos CSV
-  Actualizaste los CSVs con nuevos datos
-  Estás desarrollando y modificando datos frecuentemente

**Cómo hacerlo:**
```powershell
# Asegúrate que Neo4j está corriendo
python .\scripts\import_csv.py
```

**¿Qué hace?**
- Lee `data/nodos.csv` y `data/relaciones.csv`
- Crea nodos y relaciones en Neo4j
- Tarda 1-5 minutos dependiendo del tamaño

---

### Opción B: Restaurar desde Dump (Producción/Respaldo)

**Cuándo usar:**
-  Tienes un archivo `.dump` de respaldo
-  Quieres restaurar datos de producción
-  Otro desarrollador te compartió un dump
-  Más rápido que importar CSVs

**Cómo hacerlo:**

#### Paso 1: Detener Neo4j
```powershell
# En Neo4j Desktop: Click "Stop"
# O en terminal:
neo4j stop
```

#### Paso 2: Restaurar el dump
```powershell
# Si usas Neo4j Desktop
# Buscar la ruta de instalación (ej: C:\Users\...\Neo4jDesktop\...)
cd "C:\...\Neo4jDesktop\relate-data\dbmss\dbms-xxx\bin"

# Restaurar dump
neo4j-admin database load neo4j --from-path="D:\Proyecto_Practica\biomedicos\data\backups" --overwrite-destination=true

# Reemplaza 'neo4j' con tu nombre de base datos si es diferente
```

#### Paso 3: Reiniciar Neo4j
```powershell
# En Neo4j Desktop: Click "Start"
neo4j start
```

---

##  Crear un Dump (Backup)

### Cuándo crear backups:

- Antes de actualizaciones importantes
- Después de importar datos nuevos
- Semanalmente (producción)
- Antes de limpiar la base de datos

### Cómo crear un dump:

#### Opción 1: Desde Neo4j Desktop

1. Detener la instancia (Stop)
2. Click en los 3 puntos (•••) → "Create Dump"
3. Elegir ubicación (recomendado: `data/backups/`)

#### Opción 2: Desde línea de comandos

```powershell
# Detener Neo4j primero
neo4j stop

# Crear dump
cd "C:\...\Neo4jDesktop\relate-data\dbmss\dbms-xxx\bin"
neo4j-admin database dump neo4j --to-path="D:\Proyecto_Practica\biomedicos\data\backups"

# Esto crea: biomedicos\data\backups\neo4j.dump

# Renombrar con fecha (opcional)
Rename-Item "D:\Proyecto_Practica\biomedicos\data\backups\neo4j.dump" "biomedicos-2026-02-13.dump"

# Reiniciar Neo4j
neo4j start
```

---

##  Flujo Completo: Primera Instalación

### Escenario 1: Solo tienes CSVs

```powershell
# 1. Iniciar Neo4j Desktop
# 2. Abrir terminal
python .\scripts\import_csv.py
# 3. Listo, datos cargados
```

### Escenario 2: Tienes un dump

```powershell
# 1. Asegurarse que Neo4j está DETENIDO
# 2. Restaurar dump
neo4j-admin database load neo4j --from-path="...\data\backups" --overwrite-destination=true
# 3. Iniciar Neo4j Desktop
# 4. Listo, datos restaurados
```

### Escenario 3: Ya tienes datos en Neo4j

```powershell
# ¡No hagas nada!
# Solo inicia Neo4j Desktop y comienza a trabajar
```

---

##  Limpiar Base de Datos (Cuidado)

Si quieres **borrar todos los datos** y empezar de cero:

### Opción 1: Desde Neo4j Browser (Web UI)

```cypher
// Abrir http://localhost:7474/
// En el query editor, ejecutar:

MATCH (n) DETACH DELETE n;
```

### Opción 2: Borrar archivos de datos

```powershell
#  CUIDADO: Esto borra TODOS los datos permanentemente

# 1. Detener Neo4j
neo4j stop

# 2. Borrar carpeta de datos
# En Neo4j Desktop, buscar la ruta de datos
# Ejemplo: C:\Users\...\Neo4jDesktop\relate-data\dbmss\dbms-xxx\data\databases\neo4j
Remove-Item -Recurse -Force "C:\...\data\databases\neo4j"

# 3. Reiniciar Neo4j
neo4j start
```

---

##  Verificar Datos en Neo4j

### Desde Neo4j Browser (http://localhost:7474/)

```cypher
// Contar nodos
MATCH (n) RETURN count(n) as total_nodos;

// Contar relaciones
MATCH ()-[r]->() RETURN count(r) as total_relaciones;

// Ver tipos de nodos
MATCH (n) RETURN DISTINCT labels(n), count(*);

// Ver algunos nodos de ejemplo
MATCH (n) RETURN n LIMIT 25;
```

### Desde la API

```powershell
# Ver etiquetas T disponibles
Invoke-RestMethod http://localhost:5000/labels/t

# Ver etiquetas N disponibles
Invoke-RestMethod http://localhost:5000/labels/n

# Test de datos
Invoke-RestMethod "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0"
```

---

##  Decisión Rápida: ¿Qué Método Usar?

### ¿Tienes un archivo `.dump`?
-  SÍ → Usa **Opción B** (Restaurar desde dump)
-  NO → Continúa...

### ¿Tienes archivos CSV (`data/nodos.csv`, `data/relaciones.csv`)?
-  SÍ → Usa **Opción A** (Importar desde CSV)
-  NO → Necesitas obtener datos (contacta al equipo)

### ¿Ya tienes datos cargados en Neo4j?
-  SÍ → ¡No hagas nada! Solo úsalo
-  NO → Usa Opción A o B según lo que tengas

---

##  Mejores Prácticas

### 1. Backups Regulares
```powershell
# Crear backup semanal
neo4j-admin database dump neo4j --to-path="...\backups\backup-$(Get-Date -Format 'yyyy-MM-dd').dump"
```

### 2. Versionado de Dumps
```
data/backups/
├── biomedicos-2026-02-01.dump  # Versión inicial
├── biomedicos-2026-02-07.dump  # Después de agregar datos
├── biomedicos-2026-02-13.dump  # Versión actual
└── LATEST.dump                 # Symlink o copia del último
```

### 3. NO Duplicar Datos
```
 Si importas CSV dos veces, duplicarás los datos
 Si restauras dump sobre datos existentes, usa --overwrite-destination=true
```

### 4. Verificar Siempre
```powershell
# Después de cualquier operación, verificar:
Invoke-RestMethod http://localhost:5000/labels/t
```

---

## Troubleshooting

### Error: "Database 'neo4j' already exists"

Al restaurar dump:
```powershell
# Agregar flag --overwrite-destination=true
neo4j-admin database load neo4j --from-path="..." --overwrite-destination=true
```

### Error: "Cannot load database while running"

```powershell
# Primero detener Neo4j
neo4j stop
# Luego intentar de nuevo
```

### CSV Import duplica datos

```cypher
// Limpiar antes de reimportar
MATCH (n) DETACH DELETE n;
```

Luego ejecutar `import_csv.py`

---

##  Estructura de Backups Recomendada

```
data/backups/
├── dumps/
│   ├── biomedicos-YYYY-MM-DD.dump
│   └── LATEST.dump
├── csv/
│   ├── nodos-backup.csv
│   └── relaciones-backup.csv
└── README.txt  # Notas sobre cada backup
```

---


**Última actualización:** 2026-02-13
