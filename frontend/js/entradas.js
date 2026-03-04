
function comorbi(sincomor, diabetes, hiper, vih){
    this.sincomor=sincomor;
    this.diabetes=diabetes;
    this.hiper=hiper;
    this.vih=vih;
}

function personales(edad, sexo, talla, preferencia, peso, gineco, indice, comor, droga, alcohol){
    this.edad=edad;
    this.sexo=sexo;
    this.talla=talla;
    this.preferencia=preferencia;
    this.peso=peso;
    this.gineco=gineco;
    this.indice=indice;
    this.comor=comor;
    this.droga=droga;
    this.alcohol=alcohol;
}

function heredo(ascendente, lateral, descendente){
    this.ascendente=ascendente;
    this.lateral=lateral;
    this.descendente=descendente;
}

function estadia(T, N, M){
    this.T=T;
    this.N=N;
    this.M=M;
}

function antecede(RP, RE, HER2, Grade){
    this.RP=RP;
    this.RE=RE;
    this.HER2=HER2;
    this.Grade=Grade;
}

function biomedicos(personal, heredof, estadiat, anteceden){
    this.personal=personal;
    this.heredof=heredof;
    this.estadiat=estadiat;
    this.anteceden=anteceden;
}

function personalButton(){
    var edad= $("#edad").val(); 
    var sexo= $("#sexo").val();
    var gineco= $("#gineco").val();

    if(edad!== "" && sexo!== "" && gineco !== ""){
        let personalInfoTexto = "Edad: " + edad + ", Sexo: " + sexo + ", Ginecológicos: " + gineco;
        $("#personalInfo").text(personalInfoTexto);
    }
}

// Funciones helper para actualizar elementos de salida (evitan ReferenceError)
function updateAgeOutput(val){
    document.getElementById('ageOutput').textContent = val;
}

function updateWeightOutput(val){
    document.getElementById('weightOutput').textContent = val + ' kg';
}

function updateHeightOutput(val){
    document.getElementById('heightOutput').textContent = val + ' cm';
}

function updateTumorCount(val){
    document.getElementById('tumorCountOutput').textContent = val;
}

function updateNodeCount(val){
    document.getElementById('nodeCountOutput').textContent = val;
}


function heredoButton(){
    console.log("picao");
    var ascendente= $("#ascendente").val();
    var lateral= $("#lateral").val();
    var descendente= $("#descendente").val();

    if(ascendente!== "" && ascendente!== null && lateral!== "" && lateral!== null && descendente !== "" && descendente!== null){
        let heredofamInfoTexto = "Ascendente: " + ascendente + ", Lateral: " + lateral + ", Descendente: " + descendente;
        $("#heredofamInfo").text(heredofamInfoTexto);
    }
}

function estadiaButton(){
    console.log("picao");
    var T= $("#T").val(); 
    var N= $("#N").val(); 
    var M= $("#M").val(); 

    if(T!== "" && N!== "" && M !== ""){
        let tumoralInfoTexto = "T: " + T + ", N: " + N + ", M: " + M;
        $("#tumoralInfo").text(tumoralInfoTexto);
    }
}

function ginecoButton(){
    var RP= $("#RP").val();
    var RE= $("#RE").val();
    var HER2= $("#HER2").val();
    var Grade= $("#Grade").val();

    if(RP!== "" && RP!== null && RE!== "" && RE!== null && HER2 !== "" && HER2!== null && Grade!=="" && Grade!== null){
        console.log(RP, RE, HER2, Grade);
        let ginecoobstetricInfoTexto = "RP: " + RP + ", RE: " + RE + ", HER2: " + HER2 + ", Grado: " + Grade;
        $("#ginecoobstetricInfo").text(ginecoobstetricInfoTexto);
    }
}




function renderTreatments(data, loadingContainer, treatmentsContainer, buttonsContainer) {
    if (data && data.length > 0) {
        loadingContainer.classList.remove('active');
        treatmentsContainer.classList.add('active');

        for (let j = 1; j <= 3; j++) {
            const treatmentItem = document.getElementById(`treatment${j}`);
            if (treatmentItem) {
                treatmentItem.style.display = 'none';
            }
        }

        for (let i = 0; i < Math.min(data.length, 3); i++) {
            const treatmentNum = i + 1;
            const treatmentData = data[i];

            const treatmentItem = document.getElementById(`treatment${treatmentNum}`);
            if (treatmentItem) {
                treatmentItem.style.display = 'block';
            }

            const etapaElement = document.getElementById(`etapa${treatmentNum}`);
            if (etapaElement && treatmentData.Stage) {
                etapaElement.textContent = String(treatmentData.Stage);
            }

            const testSection = document.querySelector(`#treatment${treatmentNum} .treatment-section:nth-child(2) .treatment-section-content`);
            if (testSection && treatmentData.RecommendedTests) {
                testSection.innerHTML = '';
                treatmentData.RecommendedTests.forEach(test => {
                    const div = document.createElement('div');
                    div.innerHTML = `<span class="treatment-item-label">${test}</span>`;
                    testSection.appendChild(div);
                });
            }

            const treatmentSection = document.querySelector(`#treatment${treatmentNum} .treatment-section:nth-child(3) .treatment-section-content`);
            if (treatmentSection && treatmentData.TreatmentOptions) {
                treatmentSection.innerHTML = '';
                treatmentData.TreatmentOptions.forEach(treatment => {
                    const div = document.createElement('div');
                    div.innerHTML = `<span class="treatment-item-label">${treatment}</span>`;
                    treatmentSection.appendChild(div);
                });
            }
        }

        toastr.success('Tratamientos validados correctamente', 'Éxito');
    } else {
        loadingContainer.classList.remove('active');
        buttonsContainer.classList.remove('hidden');
        toastr.error('No se encontraron tratamientos para estos parámetros', 'Error');
    }
}

function consultarStageInfoDirecto(T, N, M, loadingContainer, treatmentsContainer, buttonsContainer) {
    const fallbackUrl = `http://127.0.0.1:5000/get_stage_info?t_label=${T}&n_label=${N}&m_label=${M}`;

    $.ajax({
        type: "GET",
        url: fallbackUrl,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            renderTreatments(data, loadingContainer, treatmentsContainer, buttonsContainer);
            toastr.info('Se usó flujo directo (sin validación ML)', 'Modo degradado');
        },
        error: function () {
            loadingContainer.classList.remove('active');
            buttonsContainer.classList.remove('hidden');
            toastr.error('Error al consultar tratamientos. Verifica servicios activos.', 'Error');
        }
    });
}

function enviar(){
    var edad= $("#edad").val(); 
    var sexo= $("#sexo").val();
    var talla= $("#talla").val();
    var preferencia= $("#Preferencia").val();
    var peso= $("#peso").val();
    var gineco= $("#gineco").val();
    var indice= $("#indice").val();
    var sincomor= $("#ninguna").prop("checked");
    var diabetes= $("#Diabetes").prop("checked");
    var hiper= $("#Hipertension").prop("checked");              
    var vih= $("#VIH").prop("checked");
    var droga= $("#drogas").val();
    var alcohol= $("#alcohol").val();
    var ascendente= $("#ascendente").val();
    var lateral= $("#lateral").val();
    var descendente= $("#descendente").val();
    
    var T= $("#T").val();
    var N= $("#N").val();
    var M= $("#M").val();
    
    // Validar que hay datos completos
    if (!edad || !sexo || !talla || !peso) {
        toastr.error('Por favor completa la información personal (Edad, Sexo, Altura, Peso)', 'Datos incompletos');
        return;
    }
    
    if (!T || !N || !M) {
        toastr.error('Por favor completa la Estadía Tumoral (T, N, M)', 'Datos incompletos');
        return;
    }
    var RP= $("#RP").val();
    var RE= $("#RE").val();
    var HER2= $("#HER2").val();
    var Grade= $("#Grade").val();
    
    const ncomorbi=new comorbi(sincomor, diabetes, hiper, vih);
    const npersona=new personales(edad, sexo, talla, preferencia, peso, gineco ,indice, ncomorbi, droga, alcohol);
    const nheredo= new heredo(ascendente, lateral, descendente);
    const nestadia= new estadia(T, N, M);
    const nantecede= new antecede(RP, RE, HER2, Grade);
    const nbiomedicos= new biomedicos(npersona, nheredo, nestadia, nantecede);
    
    console.log("Datos a enviar:", nbiomedicos);
    
    // Mostrar loading, ocultar botones
    const buttonsContainer = document.getElementById('buttonsContainer');
    const loadingContainer = document.getElementById('loadingContainer');
    const treatmentsContainer = document.getElementById('treatmentsContainer');
    
    buttonsContainer.classList.add('hidden');
    loadingContainer.classList.add('active');
    
    const submitUrl = "http://127.0.0.1:5000/pipeline/submit";
    const payload = {
        t_label: T,
        n_label: N,
        m_label: M,
        context: {
            edad: edad,
            sexo: sexo,
            peso: peso,
            talla: talla,
            RP: RP,
            RE: RE,
            HER2: HER2,
            Grade: Grade
        }
    };

    $.ajax({
        type: "POST",
        url: submitUrl,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        data: JSON.stringify(payload),
        success: function (submitResp) {
            const jobId = submitResp.job_id;
            if (!jobId) {
                consultarStageInfoDirecto(T, N, M, loadingContainer, treatmentsContainer, buttonsContainer);
                return;
            }

            let attempts = 0;
            const maxAttempts = 30;
            const pollIntervalMs = 2000;

            const poller = setInterval(() => {
                attempts += 1;
                $.ajax({
                    type: "GET",
                    url: `http://127.0.0.1:5000/pipeline/result/${jobId}`,
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (resultResp) {
                        const status = resultResp.status;

                        if (status === 'completed' && resultResp.result) {
                            clearInterval(poller);
                            const validated = resultResp.result.final_recommendations || [];
                            renderTreatments(validated, loadingContainer, treatmentsContainer, buttonsContainer);
                        } else if (status === 'failed') {
                            clearInterval(poller);
                            consultarStageInfoDirecto(T, N, M, loadingContainer, treatmentsContainer, buttonsContainer);
                        } else if (attempts >= maxAttempts) {
                            clearInterval(poller);
                            consultarStageInfoDirecto(T, N, M, loadingContainer, treatmentsContainer, buttonsContainer);
                        }
                    },
                    error: function () {
                        if (attempts >= maxAttempts) {
                            clearInterval(poller);
                            consultarStageInfoDirecto(T, N, M, loadingContainer, treatmentsContainer, buttonsContainer);
                        }
                    }
                });
            }, pollIntervalMs);
        },
        error: function () {
            consultarStageInfoDirecto(T, N, M, loadingContainer, treatmentsContainer, buttonsContainer);
        }
    });
}



