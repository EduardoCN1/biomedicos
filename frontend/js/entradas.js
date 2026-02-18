
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
    /*
    var T= $("#T").val(); Tis, T0 - T4
    var N= $("#N").val(); N0 - N4
    var M= $("#M").val(); M0, M1
    */
    var T= "T2";
    var N= "N1";
    var M= "M0";
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
    // usar la API local por defecto
    const url= "http://127.0.0.1:5000/get_stage_info?t_label=" + T + "&n_label=" + N + "&m_label=" + M;  
    console.log(T, N, M);
    $.ajax({
        type: "GET",
        url: url,
        /*data: JSON.stringify(nestadia),*/
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            console.log("Respuesta del servidooor:", data);
            console.log("jalÃ³");

            if (data) {
                let cont = 0;
                let resp = "res";
                let st = "stage";

                //recorre todas las respuestas de data
                for (let key in data) {
                    cont++; //para poder recorrer los id's de cada elemento de data
                    let res = resp + cont; //esto es res1, res2 o res3 (id's de data) dependiendo de la cantidad de respuestas en data                                                   
                    let respuesta = document.getElementById(res); 
                    respuesta.style.display = "block"; //muestro la respuesta en turno
    

                    //recorre todos los recommendedTests de las respuestas recibidas
                    let recommendedlabels = respuesta.getElementsByClassName("recommended");

                    for (let key2 in data[key].RecommendedTests) {
                        recommendedlabels[key2].textContent = data[key].RecommendedTests[key2];

                    }

                    //muestra el stage de la respuesta de data en turno
                    let stage =cont + st; //stage tiene tres id's, 1stage, 2stage y 3stage, aqui se construye el id
                    let stagelabel = document.getElementById(stage);
                    stagelabel.textContent = data[key].Stage[0];


                    // recorre los treatmentOptions
                    let treatmentlabels = respuesta.getElementsByClassName("treatment");
                    for (let key3 in data[key].TreatmentOptions) {
                        treatmentlabels[key3].textContent = data[key].TreatmentOptions[key3];
                    }
                }
                
            }

        },
        error: function (error) {
            console.error("no funciona:", error);
        }
    

   });
  
}



