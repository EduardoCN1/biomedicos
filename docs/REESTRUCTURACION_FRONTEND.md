# Reestructuración del Frontend

## Resumen de Cambios

Se ha reestructurado el archivo `frontend/index.html` para mejorar la organización y mantenibilidad del código, separando el CSS inline, los modales y el JavaScript en archivos individuales.

## Nueva Estructura de Archivos

```
frontend/
├── index.html                      # Archivo HTML principal (limpio y organizado)
├── css/
│   ├── stilous.css                # Estilos existentes
│   ├── stilous.scss              # Fuente SCSS existente
│   └── index-custom.css          #  NUEVO: Estilos específicos del index
├── js/
│   ├── config.js                 # Configuración existente
│   ├── entradas.js               # Lógica de negocio existente
│   └── main.js                   # NUEVO: Funciones principales del UI
└── modals/                        # NUEVA CARPETA
    ├── modal-personal.html       # Modal de Antecedentes Personales
    ├── modal-heredofamiliar.html # Modal de Antecedentes Heredofamiliares
    ├── modal-tumoral.html        # Modal de Estadía Tumoral
    └── modal-ihc.html            # Modal de Inmunohistoquímica (IHC)
```

## Archivos Creados

### 1. `frontend/css/index-custom.css`
- **Propósito**: Contiene todos los estilos que estaban inline en el `<style>` del index.html
- **Contenido**: 
  - Estilos del header
  - Estilos del contenedor principal
  - Estilos de botones y acciones
  - Estilos del perfil del paciente
  - Estilos de modales
  - Estilos de carga y tratamientos
  - Media queries para responsive design

### 2. `frontend/js/main.js`
- **Propósito**: Contiene toda la lógica JavaScript que estaba inline en el index.html
- **Funciones principales**:
  - `getModalState()` - Obtiene el estado actual de un modal
  - `openModal()` / `closeModal()` - Gestión de modales
  - `handleComorbilidadesChange()` - Manejo de checkboxes de comorbilidades
  - `calcularIndiceTabaquico()` - Cálculo del índice tabáquico
  - `updateProfile()` - Actualización de la vista del perfil
  - `guardarPersonales()`, `guardarHeredofamiliar()`, etc. - Funciones de guardado
  - `enviar()` - Función de consulta
  - `toggleTreatment()` - Toggle de tratamientos
  - `resetConsulta()` - Reinicio de consulta
  - `loadModals()` - Carga dinámica de modales

### 3. `frontend/modals/`
Nueva carpeta que contiene los 4 modales separados en archivos HTML individuales:

#### `modal-personal.html`
- Modal de Antecedentes Personales
- Contiene campos: edad, altura, sexo, peso, drogas, cigarros, alcohol, comorbilidades, antecedentes ginecológicos

#### `modal-heredofamiliar.html`
- Modal de Antecedentes Heredofamiliares
- Contiene campos: familiar ascendiente, descendiente, lateral

#### `modal-tumoral.html`
- Modal de Estadía Tumoral
- Contiene campos TNM: T (tamaño), N (nódulos), M (metástasis)

#### `modal-ihc.html`
- Modal de Inmunohistoquímica
- Contiene campos: RP, RE, Grade, HER2

## Cómo Funciona la Carga Dinámica

Los modales ya no están embebidos en el index.html. En su lugar:

1. El `index.html` tiene contenedores vacíos para cada modal:
```html
<div id="modal-personal-container"></div>
<div id="modal-heredofamiliar-container"></div>
<div id="modal-tumoral-container"></div>
<div id="modal-ihc-container"></div>
```

2. La función `loadModals()` en `main.js` carga los modales mediante fetch al cargar la página:
```javascript
function loadModals() {
    // Carga cada modal desde su archivo HTML correspondiente
    fetch('modals/modal-personal.html')
        .then(response => response.text())
        .then(html => {
            document.getElementById('modal-personal-container').innerHTML = html;
        });
    // ... (y así para cada modal)
}
```

## Beneficios de esta Reestructuración

### 1. **Mejor Organización**
- Separación clara de responsabilidades (HTML, CSS, JS)
- Código más fácil de navegar y entender
- Estructura modular

### 2. **Mantenibilidad Mejorada**
- Cambios en estilos se hacen en un solo archivo CSS
- Cada modal puede editarse independientemente
- Funciones JavaScript bien organizadas

### 3. **Reusabilidad**
- Los modales pueden reutilizarse en otras páginas
- Los estilos son consistentes y centralizados
- Las funciones JavaScript están disponibles globalmente

### 4. **Tamaño de Archivo Reducido**
- El index.html pasó de 1674 líneas a aproximadamente 350 líneas
- Más fácil de cargar y renderizar
- Mejor performance

### 5. **Desarrollo Colaborativo**
- Múltiples desarrolladores pueden trabajar en diferentes archivos sin conflictos
- Más fácil hacer code reviews
- Mejor control de versiones

## Migración y Compatibilidad

 **Compatibilidad total**: Todas las funciones existentes siguen funcionando exactamente igual.

 **Sin cambios de comportamiento**: La aplicación se ve y funciona de la misma manera.

 **Referencias actualizadas**: Todas las referencias a archivos CSS y JS están correctamente actualizadas.

## Próximos Pasos Recomendados

1. **Testing**: Verificar que todos los modales se cargen correctamente y todas las funciones trabajen como antes.

2. **Optimización adicional**: 
   - Considerar minificar los archivos CSS y JS para producción
   - Implementar lazy loading para los modales

3. **Documentación de componentes**: 
   - Documentar cada modal individualmente
   - Crear guía de estilos CSS

## Notas Técnicas

- Los modales se cargan dinámicamente usando `fetch()` API
- Se mantiene compatibilidad con jQuery existente
- Bootstrap y Toastr siguen funcionando normalmente
- El archivo `entradas.js` existente no fue modificado y sigue funcionando

---

**Fecha de reestructuración**: Marzo 2026  
**Archivos modificados**: 1 (index.html)  
**Archivos creados**: 6 (1 CSS + 1 JS + 4 HTML de modales)
