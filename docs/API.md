# Documentación de Endpoints API

Base URL: `http://localhost:5000`

## 1. GET `/`
Verifica que la API está en funcionamiento.

**Request:**
```
GET http://localhost:5000/
```

**Response:** 200 OK
```
"En ejecución"
```

---

## 2. GET `/labels/t`
Obtiene todas las etiquetas T disponibles en la base de datos.

**Request:**
```
GET http://localhost:5000/labels/t
```

**Response:** 200 OK
```json
["T0", "T1", "T1a", "T1b", "T2", "T3", "T4", ...]
```

---

## 3. GET `/labels/n`
Obtiene todas las etiquetas N disponibles en la base de datos.

**Request:**
```
GET http://localhost:5000/labels/n
```

**Response:** 200 OK
```json
["N0", "N1", "N1a", "N1b", "N2", "N3", "Nx", ...]
```

---

## 4. GET `/labels/m`
Obtiene todas las etiquetas M disponibles en la base de datos.

**Request:**
```
GET http://localhost:5000/labels/m
```

**Response:** 200 OK
```json
["M0", "M1", "Mx"]
```

---

## 5. GET `/get_stage_info`
Obtiene información de tratamientos y pruebas recomendadas para una combinación TNM.

**Request:**
```
GET http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0
```

**Parameters:**
- `t_label` (required): Etiqueta T (ej. T2)
- `n_label` (required): Etiqueta N (ej. N1)
- `m_label` (required): Etiqueta M (ej. M0)

**Response:** 200 OK
```json
[
  {
    "Stage": "Stage IIIA",
    "RecommendedTests": [
      "Breast Biopsy",
      "Bone Scan",
      "Histologic Typing"
    ],
    "TreatmentOptions": [
      "Mastectomy",
      "Chemotherapy"
    ]
  },
  {
    "Stage": "Stage IIB",
    "RecommendedTests": [
      "Receptor Testing",
      "Mammogram"
    ],
    "TreatmentOptions": [
      "Surgery",
      "Endocrine Therapy"
    ]
  }
]
```

**Response:** 404 Not Found
```json
{
  "error": "No results found"
}
```

**Response:** 400 Bad Request (missing params)
```json
{
  "error": "Missing parameters"
}
```

---

## 6. POST `/entradas`
Recibe datos del formulario desde el frontend.

**Request:**
```
POST http://localhost:5000/entradas
Content-Type: application/json

{
  "personal": {
    "edad": 45,
    "sexo": "Femenino",
    "peso": 70,
    "talla": 160
  },
  "estadio": {
    "t": "T2",
    "n": "N1",
    "m": "M0"
  }
}
```

**Response:** 201 Created
```json
{
  "mensaje": "Datos recibidos correctamente",
  "datos": {
    "personal": {...},
    "estadio": {...}
  }
}
```

**Response:** 400 Bad Request (sin JSON)
```json
{
  "error": "No JSON body provided"
}
```

---

## Ejemplos con cURL

```bash
# Obtener etiquetas
curl http://localhost:5000/labels/t

# Obtener info de tratamiento
curl "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0"

# POST datos
curl -X POST http://localhost:5000/entradas \
  -H "Content-Type: application/json" \
  -d '{"name":"Prueba","age":30}'
```

## Ejemplos con PowerShell

```powershell
# GET etiquetas
Invoke-RestMethod http://localhost:5000/labels/t | ConvertTo-Json

# GET info de tratamiento
Invoke-RestMethod "http://localhost:5000/get_stage_info?t_label=T2&n_label=N1&m_label=M0" | ConvertTo-Json -Depth 10

# POST datos
$body = @{ name='Prueba'; age=30 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:5000/entradas -Body $body -ContentType 'application/json'
```

## Códigos de Estado HTTP

| Código         | Significado                                        |
|----------------|----------------------------------------------------|
| 200            | OK - Solicitud exitosa                             |
| 201            | Created - Recurso creado                           |
| 400            | Bad Request - Parámetros inválidos o faltantes     |
| 404            | Not Found - No hay datos para esa combinación TNM  |
| 500            | Internal Server Error - Error en el servidor       |
|---------------------------------------------------------------------|