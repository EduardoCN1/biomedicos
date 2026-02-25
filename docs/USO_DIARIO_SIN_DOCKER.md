# Guía de Uso Diario

Esta guía es para cuando **ya completaste el setup inicial** y quieres usar el sistema día a día.

##  ¿Cuándo usar esta guía?

-  Ya ejecutaste `setup.ps1` anteriormente
-  Ya tienes el entorno conda `biomedicos` creado
-  Ya tienes `.env` con tus credenciales
-  Ya tienes datos en Neo4j (ya sea por `import_csv.py` o restaurando un dump)
-  Solo quieres arrancar el sistema para trabajar

> **Nota:** Si es tu primera vez, consulta [DATABASE.md](DATABASE.md) para ver cómo poblar Neo4j con datos (CSV o dump).

##  Checklist Rápido (5 minutos)

```
□ Neo4j Desktop iniciado (Start → Running)
□ PowerShell NUEVA abierta
□ Ejecutar .\scripts\run.ps1
□ Abrir Live Server (frontend)
□ Probar http://localhost:5000/
```

---

##  Flujo Paso a Paso

### Paso 1: Iniciar Neo4j Desktop

**1 Abrir Neo4j Desktop**
- Doble click en el ícono de Neo4j Desktop

**2 Seleccionar tu proyecto/instancia**
- En el panel izquierdo, busca tu proyecto (ej: "biomedicos")

**3 Click en "Start" (botón verde ▶)**
- Esperar 20-30 segundos

**4 Verificar estado "Running" ✓**
- Debe mostrar un indicador verde que dice "Running"

**IMPORTANTE:** NO cierres Neo4j Desktop mientras trabajas.

---

### Paso 2: Verificar Neo4j (Opcional pero recomendado)

Abrir navegador:
```
http://localhost:7474/
```

**¿Qué deberías ver?**
-  Interfaz web de Neo4j (Neo4j Browser)
-  Formulario de login

**Si no abre o da error:**
- Neo4j no está corriendo
- Volver al Paso 1 y verificar que dice "Running"

---

### Paso 3:  Abrir PowerShell NUEVA

**PROBLEMA COMÚN:**
```
Si tenías una terminal abierta ANTES de iniciar Neo4j,
esa terminal no detectará que Neo4j ya está activo.
```

**SOLUCIÓN:**
1. Cerrar todas las terminales de PowerShell/VS Code
2. Abrir una terminal COMPLETAMENTE NUEVA
3. Navegar a la carpeta del proyecto

```powershell
cd D:\Proyecto_Practica\biomedicos
```

**¿Por qué es necesario?**
- Las terminales abiertas antes de Neo4j tienen un "estado viejo"
- Cuando intentan conectar, usan información desactualizada
- Una terminal nueva detecta correctamente el estado de Neo4j

---

### Paso 4: Arrancar el Servidor Backend

```powershell
.\scripts\run.ps1
```

**Salida esperada:**
```
================================
Arrancando API Biomedicos
================================
Cargando configuración desde .env...

Configuración:
Neo4j URI: neo4j://127.0.0.1:7687
Neo4j User: neo4j
API Host: 0.0.0.0
API Port: 5000

Activando entorno conda...

Arrancando servidor en http://0.0.0.0:5000...
Presiona Ctrl+C para detener.

✓ Servidor Waitress iniciado en http://0.0.0.0:5000
  Presiona Ctrl+C para detener
```

**Si ves esto → Todo bien, continúa al Paso 5**

**Si ves errores:**

| Error                                            | Causa                            | Solución                                    |
|--------------------------------------------------|----------------------------------|---------------------------------------------|
| `Unable to retrieve routing information`         | Neo4j no está corriendo          | Volver al Paso 1                            |
| `ModuleNotFoundError: No module named 'backend'` | Terminal vieja o path incorrecto | Cerrar terminal y abrir nueva               |
| `conda: command not found`                       | Entorno no activado              | Abrir terminal nueva                        |
| `Port 5000 already in use`                       | Ya tienes un servidor corriendo  | `Get-Process python \| Stop-Process -Force` |
|___________________________________________________________________________________________________________________________________|
---

### Paso 5: Abrir el Frontend

En **VS Code**:

1. Navegar a `frontend/index.html` en el explorador
2. Click derecho → **"Open with Live Server"**

**Alternativa sin Live Server:**
```powershell
# En otra terminal
python -m http.server 5500 --directory frontend
```

**¿Qué deberías ver?**
-  Navegador abre automáticamente
-  Formulario con secciones: Antecedentes, Estadía Tumoral, etc.
-  Sin errores en consola (F12)

---

### Paso 6: Probar que Todo Funciona

**En otra terminal PowerShell:**

```powershell
# Test 1: ¿Backend responde?
Invoke-RestMethod http://localhost:5000/
# Esperado: "En ejecución"

# Test 2: ¿Conecta a Neo4j?
Invoke-RestMethod http://localhost:5000/labels/t
# Esperado: ["T0", "T1", "T2", ...]

# Test 3: ¿Endpoint principal funciona?
Invoke-RestMethod "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0"
# Esperado: Array de objetos JSON con Stage, Tests, Treatments
```

**Todos pasaron?  Listo para trabajar**

---

##  Cómo Detener Todo

### Detener Backend
```
En la terminal donde corre run.ps1:
Presionar Ctrl+C
```

### Detener Frontend (Live Server)
```
En VS Code:
Click en "Port: 5500" en la barra inferior → Stop Server
```

### Detener Neo4j
```
En Neo4j Desktop:
Click en "Stop" (botón rojo)
```

---

##  Flujo Completo (Resumen Visual)

```
┌─────────────────────────────────────────┐
│ 1. Abrir Neo4j Desktop                  │
│    → Start → Esperar "Running"          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 2. Cerrar terminales viejas             │
│    → Abrir PowerShell NUEVA             │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 3. cd D:\Proyecto_Practica\biomedicos   │
│    → .\scripts\run.ps1                  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. Esperar "✓ Servidor iniciado"        │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 5. VS Code → index.html → Live Server   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 6. Probar endpoints (opcional)          │
└─────────────────────────────────────────┘
```

---

##  Atajo para Expertos

Si ya sabes lo que haces:

```powershell
# Terminal 1: Neo4j (manualmente en Desktop)

# Terminal 2: Backend
conda activate biomedicos
python .\backend\run_waitress.py

# VS Code: Live Server en index.html
```

---

##  Troubleshooting Específico

### "Unable to retrieve routing information"

**Causa:** Neo4j NO está corriendo o terminal vieja

**Solución paso a paso:**
1. Verificar Neo4j Desktop muestra "Running" ✓
2. Si no → Click "Start" y esperar 30 segundos
3. Si ya estaba en "Running" → Cerrar terminal y abrir una NUEVA
4. Ejecutar `.\scripts\run.ps1` de nuevo

---

### Frontend no se conecta al Backend

**Síntomas:** Formulario carga pero al enviar no pasa nada

**Verificar:**
```powershell
# ¿Backend está corriendo?
Invoke-RestMethod http://localhost:5000/
```

**Si no responde:**
- Backend no está corriendo
- Ir al Paso 4 y ejecutar `.\scripts\run.ps1`

**Si responde pero frontend no funciona:**
- Abrir Dev Tools (F12) en navegador
- Ver la pestaña "Console" → buscar errores
- Ver la pestaña "Network" → verificar llamadas AJAX

---

### "conda: command not found"

**Causa:** Terminal fue abierta antes de que conda se inicializara

**Solución:**
```powershell
# Cerrar terminal
# Abrir terminal NUEVA
# Ejecutar de nuevo
.\scripts\run.ps1
```

---

##  Tips Productivos

### 1. Mantén Neo4j siempre corriendo durante desarrollo
- No lo apagues entre pruebas
- Solo detenlo cuando termines el día

### 2. Usa múltiples terminales
```
Terminal 1: Backend (.\scripts\run.ps1)
Terminal 2: Testing (Invoke-RestMethod ...)
Terminal 3: Comandos varios
```

### 3. Atajo de teclado para Live Server
```
En VS Code:
Alt+L → Alt+O
```

### 4. Recarga rápida del backend
```
Terminal donde corre backend:
Ctrl+C (detener)
Flecha arriba (último comando)
Enter (re-ejecutar)
```

---

##  Checklist de "No Funciona"

Antes de buscar ayuda, verifica:

- [ ] Neo4j Desktop abierto y en estado "Running" ✓
- [ ] Abriste PowerShell DESPUÉS de iniciar Neo4j
- [ ] Estás en la carpeta `D:\Proyecto_Practica\biomedicos`
- [ ] `.\scripts\run.ps1` muestra "✓ Servidor iniciado"
- [ ] `http://localhost:7474/` abre en navegador
- [ ] `http://localhost:5000/` responde "En ejecución"
- [ ] Live Server está activo (puerto 5500)
- [ ] No hay errores en consola del navegador (F12)

---

##  Diferencia: Setup vs Uso Diario

| Aspecto           | Setup Inicial (1 vez) | Uso Diario        |
|-------------------|-----------------------|-------------------|
| `setup.ps1`       |  Ejecutar             | No necesario      |
| Crear `.env`      |  Copiar y editar      | Ya existe         |
| `import_csv.py`   |  Importar datos       | Ya están en Neo4j |
| Iniciar Neo4j     |  Sí                   | Sí (cada vez)     |
| `run.ps1`         |  Sí                   | Sí (cada vez)     |
| Live Server       |  Sí                   | Sí (cada vez)     |
|---------------------------------------------------------------|

---

**Última actualización:** 2026-02-13
