// Main JavaScript for Biomedical Management System

// Global Variables
const modalSnapshots = {};
let indiceTabaquicoCalculado = ''; // Variable para almacenar el índice calculado

// Get Modal State
function getModalState(type) {
    const modal = document.getElementById(`modal-${type}`);
    if (!modal) {
        return { data: '', hasData: false };
    }

    const fields = Array.from(modal.querySelectorAll('input, select, textarea'));
    const state = {};
    let hasData = false;

    fields.forEach((field, index) => {
        // Excluir el select oculto de índice
        if (field.id === 'indice' && field.style.display === 'none') {
            return;
        }
        
        const key = `${field.id || field.name || 'field'}_${index}`;
        let value = '';

        if (field.type === 'checkbox' || field.type === 'radio') {
            value = field.checked ? '1' : '0';
            if (field.checked) {
                hasData = true;
            }
        } else {
            value = String(field.value || '').trim();
            if (value) {
                hasData = true;
            }
        }

        state[key] = value;
    });

    // Incluir el índice tabáquico calculado en el estado
    if (type === 'personal' && indiceTabaquicoCalculado) {
        state['indiceCalculado'] = indiceTabaquicoCalculado;
        hasData = true;
    }

    return { data: JSON.stringify(state), hasData };
}

// Modal Functions
function openModal(type) {
    const modal = document.getElementById(`modal-${type}`);
    if (modal) {
        modal.classList.add('active');
        modalSnapshots[type] = getModalState(type).data;
    }
}

function closeModal(type) {
    const modal = document.getElementById(`modal-${type}`);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        event.target.classList.remove('active');
    }
});

// Handle Comorbilidades Change
function handleComorbilidadesChange(input) {
    const all = Array.from(document.querySelectorAll('input[name="comorbilidades"]'));
    const ninguna = document.getElementById('ninguna');

    if (input.id === 'ninguna' && input.checked) {
        all.forEach((item) => {
            if (item !== input) {
                item.checked = false;
            }
        });
    }

    if (input.id !== 'ninguna' && input.checked) {
        ninguna.checked = false;
    }

    updateProfile();
}

// Set Gineco Manual Selection
function setGinecoManualSelection() {
    const GinecoSelect = document.getElementById('gineco');
    if (GinecoSelect) {
        GinecoSelect.dataset.userSelected = '1';
    }
}

// Calcular Indice Tabaquico
function calcularIndiceTabaquico() {
    const cigarrosInput = document.getElementById('cigarrosDiarios').value;
    const anosInput = document.getElementById('anosConsumo').value;
    
    // Si alguno está vacío, no hay suficiente información
    if (cigarrosInput === '' || anosInput === '') {
        indiceTabaquicoCalculado = '';
        updateProfile();
        return;
    }
    
    const cigarros = Number(cigarrosInput);
    const anos = Number(anosInput);
    
    const indiceCalculado = (cigarros * anos) / 20;
    let rangoIndice = '';

    if (indiceCalculado < 10) {
        rangoIndice = '< 10';
    } else if (indiceCalculado >= 10 && indiceCalculado <= 20) {
        rangoIndice = '10 - 20';
    } else if (indiceCalculado > 20 && indiceCalculado <= 40) {
        rangoIndice = '21 - 40';
    } else if (indiceCalculado > 40) {
        rangoIndice = '> 41';
    }

    indiceTabaquicoCalculado = rangoIndice;
    updateProfile();
}

// Update Profile Display
function updateProfile() {
    // Información Personal
    const edad = document.getElementById('edad').value;
    document.getElementById('display-edad').textContent = edad ? edad : 'Sin ingresar';
    
    // Validar edad máxima
    if (edad && edad > 110) {
        toastr.warning('La edad ingresada parece estar fuera de lo normal', 'Verificar Edad');
    }

    const talla = document.getElementById('talla').value;
    document.getElementById('display-altura').textContent = talla ? `${talla} cm` : 'Sin ingresar';
    
    // Validar altura máxima
    if (talla && talla > 230) {
        toastr.warning('La altura ingresada parece estar fuera de lo normal', 'Verificar Altura');
    }

    const sexo = document.getElementById('sexo').value;
    document.getElementById('display-sexo').textContent = sexo ? sexo : 'Sin ingresar';

    const peso = document.getElementById('peso').value;
    document.getElementById('display-peso').textContent = peso ? `${peso} kg` : 'Sin ingresar';
    if(peso && peso > 250){
        toastr.warning('El peso ingresado parece estar fuera de lo normal', 'Verificar Peso');
    }

    // Información Consumo
    const drogas = document.getElementById('drogas').value;
    document.getElementById('display-drogas').textContent = drogas ? drogas : 'Sin seleccionar';

    const alcohol = document.getElementById('alcohol').value;
    document.getElementById('display-alcohol').textContent = alcohol ? alcohol : 'Sin seleccionar';

    const cigarros = document.getElementById('cigarrosDiarios').value;
    const anos = document.getElementById('anosConsumo').value;
    
    let indiceDisplay = 'Sin calcular';
    if (cigarros && anos) {
        indiceDisplay = indiceTabaquicoCalculado || 'Sin calcular';
    }
    document.getElementById('display-indice').textContent = indiceDisplay;

    // Comorbilidades
    const comorbilidades = Array.from(
        document.querySelectorAll('input[name="comorbilidades"]:checked')
    ).map((item) => item.value);
    document.getElementById('display-comorbilidades').textContent = comorbilidades.length
        ? comorbilidades.join(', ')
        : 'Sin seleccionar';

    // Antecedentes Ginecológicos
    const ginecoSelect = document.getElementById('gineco');
    const edadNumero = Number(edad);
    const tieneEdadValida = edad !== '' && Number.isFinite(edadNumero);
    const ginecoDefault = tieneEdadValida
        ? (edadNumero < 40 ? 'Premenopausica' : 'Menopausica')
        : '';

    if (ginecoSelect && ginecoDefault && !ginecoSelect.dataset.userSelected) {
        ginecoSelect.value = ginecoDefault;
    }

    const gineco = ginecoSelect ? ginecoSelect.value : '';
    document.getElementById('display-ginecologicos').textContent = gineco ? gineco : 'Sin seleccionar';

    // Heredo familiales
    const ascendente = document.getElementById('ascendente').value;
    document.getElementById('display-ascendente').textContent = ascendente ? ascendente : 'Sin seleccionar';

    const descendente = document.getElementById('descendente').value;
    document.getElementById('display-descendente').textContent = descendente ? descendente : 'Sin seleccionar';

    const lateral = document.getElementById('lateral').value;
    document.getElementById('display-lateral').textContent = lateral ? lateral : 'Sin seleccionar';

    // Estadía Tumoral
    const T = document.getElementById('T').value;
    document.getElementById('display-T').textContent = T ? T : 'Sin ingresar';

    const M = document.getElementById('M').value;
    document.getElementById('display-M').textContent = M ? M : 'Sin seleccionar';

    const N = document.getElementById('N').value;
    document.getElementById('display-N').textContent = N ? N : 'Sin ingresar';

    const surgeryPreferenceSelect = document.getElementById('surgeryPreference');
    const surgeryPreference = surgeryPreferenceSelect ? surgeryPreferenceSelect.value : '';
    document.getElementById('display-surgery-preference').textContent = surgeryPreference ? surgeryPreference : 'Sin ingresar';

    // Inmunohistoquímica (IHC)
    const RP = document.getElementById('RP').value;
    document.getElementById('display-RP').textContent = RP ? RP : 'Sin seleccionar';

    const RE = document.getElementById('RE').value;
    document.getElementById('display-RE').textContent = RE ? RE : 'Sin seleccionar';

    const Grade = document.getElementById('Grade').value;
    document.getElementById('display-Grade').textContent = Grade ? Grade : 'Sin seleccionar';

    const HER2 = document.getElementById('HER2').value;
    document.getElementById('display-HER2').textContent = HER2 ? HER2 : 'Sin seleccionar';
}

// Guardar con Validacion
function guardarConValidacion(type, successMessage) {
    const state = getModalState(type);
    const snapshot = modalSnapshots[type] || '';

    if (!state.hasData || state.data === snapshot) {
        toastr.warning('No hay informacion nueva para guardar', 'Sin cambios');
        return;
    }

    closeModal(type);
    toastr.success(successMessage, 'Éxito');
}

// Guardar Functions
function guardarPersonales() {
    guardarConValidacion('personal', 'Antecedentes personales guardados correctamente');
}

function guardarHeredofamiliar() {
    guardarConValidacion('heredofamiliar', 'Antecedentes heredofamiliares guardados correctamente');
}

function guardarTumoral() {
    guardarConValidacion('tumoral', 'Estadía tumoral guardada correctamente');
}

function guardarIHC() {
    guardarConValidacion('IHC', 'Inmunohistoquímica (IHC)  guardados correctamente');
}

// Función Enviar (Consultar)
function enviar() {
    console.log('Función enviar() llamada');
    
    // Validar que haya al menos algunos datos ingresados
    const edad = document.getElementById('edad').value;
    const talla = document.getElementById('talla').value;
    const peso = document.getElementById('peso').value;

    console.log('Edad:', edad, 'Talla:', talla, 'Peso:', peso);

    if (!edad && !talla && !peso) {
        toastr.error('Por favor completa al menos la información personal', 'Error de validación');
        return;
    }

    // Mostrar carga
    const buttonsContainer = document.getElementById('buttonsContainer');
    const loadingContainer = document.getElementById('loadingContainer');
    const treatmentsContainer = document.getElementById('treatmentsContainer');

    console.log('Elementos encontrados:', { buttonsContainer, loadingContainer, treatmentsContainer });

    buttonsContainer.classList.add('hidden');
    loadingContainer.classList.add('active');

    console.log('Iniciando carga de 3.5 segundos...');

    // Simular carga de 3.5 segundos
    setTimeout(() => {
        console.log('Finalizando carga');
        loadingContainer.classList.remove('active');
        treatmentsContainer.classList.add('active');
        toastr.success('Tratamientos generados correctamente', 'Éxito');
    }, 3500);
}

// Toggle Treatment
function toggleTreatment(num) {
    const content = document.getElementById(`content${num}`);
    const chevron = document.getElementById(`chevron${num}`);

    content.classList.toggle('active');
    chevron.classList.toggle('rotated');
}

// Reset Consulta
function resetConsulta() {
    const buttonsContainer = document.getElementById('buttonsContainer');
    const treatmentsContainer = document.getElementById('treatmentsContainer');

    treatmentsContainer.classList.remove('active');
    buttonsContainer.classList.remove('hidden');

    // Cerrar todos los tratamientos expandidos
    for (let i = 1; i <= 3; i++) {
        const content = document.getElementById(`content${i}`);
        const chevron = document.getElementById(`chevron${i}`);
        content.classList.remove('active');
        chevron.classList.remove('rotated');
    }

    // Resetear índice tabáquico
    indiceTabaquicoCalculado = '';

    toastr.info('Listo para nueva consulta', 'Reiniciado');
}

// Initialize Profile on Load
window.addEventListener('load', function() {
    loadModals().then(() => {
        updateProfile();
    }).catch(error => {
        console.error('Error loading modals:', error);
        // Intentar actualizar perfil incluso si hay error
        updateProfile();
    });
});

// Load Modals Function
function loadModals() {
    // Cargar modales desde archivos externos
    const modalsToLoad = [
        { id: 'modal-personal-container', file: 'modals/modal-personal.html' },
        { id: 'modal-heredofamiliar-container', file: 'modals/modal-heredofamiliar.html' },
        { id: 'modal-tumoral-container', file: 'modals/modal-tumoral.html' },
        { id: 'modal-ihc-container', file: 'modals/modal-ihc.html' }
    ];

    const loadPromises = modalsToLoad.map(modal => {
        return fetch(modal.file)
            .then(response => response.text())
            .then(html => {
                const container = document.getElementById(modal.id);
                if (container) {
                    container.innerHTML = html;
                }
            })
            .catch(error => console.error(`Error loading ${modal.file}:`, error));
    });

    return Promise.all(loadPromises);
}
