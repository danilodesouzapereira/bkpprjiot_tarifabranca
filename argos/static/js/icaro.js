/*
Função para inicializar os checkboxes para filtros do dia típico
*/
function setFiltersInitValue(valuesJson_daysFilter, valuesJson_seasonsFilter) {

  // marca/desmarca dias da semana
  var checked = false, selectAllChecked = true;
  if (valuesJson_daysFilter['ck2af'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ck2af').checked = checked;
  document.getElementById('ck2af_hidden').checked = checked;
  if (valuesJson_daysFilter['ck3af'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ck3af').checked = checked;
  document.getElementById('ck3af_hidden').checked = checked;
  if (valuesJson_daysFilter['ck4af'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ck4af').checked = checked;
  document.getElementById('ck4af_hidden').checked = checked;
  if (valuesJson_daysFilter['ck5af'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ck5af').checked = checked;
  document.getElementById('ck5af_hidden').checked = checked;
  if (valuesJson_daysFilter['ck6af'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ck6af').checked = checked;
  document.getElementById('ck6af_hidden').checked = checked;
  if (valuesJson_daysFilter['ckSab'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ckSab').checked = checked;
  document.getElementById('ckSab_hidden').checked = checked;
  if (valuesJson_daysFilter['ckDom'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ckDom').checked = checked;
  document.getElementById('ckDom_hidden').checked = checked;
  document.getElementById('ckAlldays').checked = selectAllChecked;
  document.getElementById('ckAlldays_hidden').checked = selectAllChecked;

  // marca/desmarca filtros de estações do ano
  selectAllChecked = true;
  if (valuesJson_seasonsFilter['ckSummer'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ckSummer').checked = checked;
  document.getElementById('ckSummer_hidden').checked = checked;
  if (valuesJson_seasonsFilter['ckFall'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ckFall').checked = checked;
  document.getElementById('ckFall_hidden').checked = checked;
  if (valuesJson_seasonsFilter['ckWinter'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ckWinter').checked = checked;
  document.getElementById('ckWinter_hidden').checked = checked;
  if (valuesJson_seasonsFilter['ckSpring'] == 1){checked = true;}else{checked = false; selectAllChecked = false;}
  document.getElementById('ckSpring').checked = checked;
  document.getElementById('ckSpring_hidden').checked = checked;
  document.getElementById('ckAllSeasons').checked = selectAllChecked;
  document.getElementById('ckAllSeasons_hidden').checked = selectAllChecked;
}


/*
Função para marcar/desmarcar todos os checkboxes relativos a dias da semana
*/
function updateCheckboxesDays(source){
    checkboxes = document.getElementsByName('ckWeekday');
    for(var i=0, n=checkboxes.length; i<n; i++){
        checkboxes[i].checked = source.checked;
    }

    // atualiza checkboxes ocultos
    checkboxes_hidden = document.getElementsByName('ckWeekday_hidden');
    for(var i=0, n=checkboxes_hidden.length; i<n; i++){
        checkboxes_hidden[i].checked = source.checked;
    }
    document.getElementsById('ckAlldays_hidden').checked = source.checked;
}


/*
Função para atualizar campos ocultos de uma das abas do aplicativo
Tarifa Branca, para replicar os valores dos filtros de data inicial e data final
*/
function updateHiddenFields(){
    dt_ini_value = document.getElementById('datetime_ini').value;
    dt_fin_value = document.getElementById('datetime_fin').value;
    document.getElementById('datetime_ini_hidden').value = dt_ini_value;
    document.getElementById('datetime_fin_hidden').value = dt_fin_value;
}


/*
Função para marcar/desmarcar todos os checkboxes relativos a estações
*/
function updateCheckboxesSeasons(source){
    checkboxes = document.getElementsByName('ckSeason');
    for(var i=0, n=checkboxes.length; i<n; i++){
        checkboxes[i].checked = source.checked;
    }

    // atualiza checkbox oculto
    checkboxes_hidden = document.getElementsByName('ckSeason_hidden');
    for(var i=0, n=checkboxes_hidden.length; i<n; i++){
        checkboxes_hidden[i].checked = source.checked;
    }
    document.getElementsById('ckAllSeasons_hidden').checked = source.checked;
}


/*
Função para atualizar o checkbox responsável por marcar/desmarcar todos - Dias da semana
*/
function updateSelectAllDays(source){
    var selectAllChecked = true;
    if(document.getElementById('ck2af').checked == false){selectAllChecked = false;}
    if(document.getElementById('ck3af').checked == false){selectAllChecked = false;}
    if(document.getElementById('ck4af').checked == false){selectAllChecked = false;}
    if(document.getElementById('ck5af').checked == false){selectAllChecked = false;}
    if(document.getElementById('ck6af').checked == false){selectAllChecked = false;}
    if(document.getElementById('ckSab').checked == false){selectAllChecked = false;}
    if(document.getElementById('ckDom').checked == false){selectAllChecked = false;}
    document.getElementById('ckAlldays').checked = selectAllChecked;

    // itens ocultos (navbar à esquerda)
    document.getElementById('ck2af_hidden').checked = document.getElementById('ck2af').checked;
    document.getElementById('ck3af_hidden').checked = document.getElementById('ck3af').checked;
    document.getElementById('ck4af_hidden').checked = document.getElementById('ck4af').checked;
    document.getElementById('ck5af_hidden').checked = document.getElementById('ck5af').checked;
    document.getElementById('ck6af_hidden').checked = document.getElementById('ck6af').checked;
    document.getElementById('ckSab_hidden').checked = document.getElementById('ckSab').checked;
    document.getElementById('ckDom_hidden').checked = document.getElementById('ckDom').checked;
    document.getElementById('ckAlldays_hidden').checked = selectAllChecked;
}

/*
Função para atualizar o checkbox responsável por marcar/desmarcar todos - Estações
*/
function updateSelectAllSeasons(source){
    var selectAllChecked = true;
    if(document.getElementById('ckSummer').checked == false){selectAllChecked = false;}
    if(document.getElementById('ckFall').checked == false){selectAllChecked = false;}
    if(document.getElementById('ckWinter').checked == false){selectAllChecked = false;}
    if(document.getElementById('ckSpring').checked == false){selectAllChecked = false;}
    document.getElementById('ckAllSeasons').checked = selectAllChecked;

    // itens ocultos (navbar à esquerda)
    document.getElementById('ckSummer_hidden').checked = document.getElementById('ckSummer').checked;
    document.getElementById('ckFall_hidden').checked = document.getElementById('ckFall').checked;
    document.getElementById('ckWinter_hidden').checked = document.getElementById('ckWinter').checked;
    document.getElementById('ckSpring_hidden').checked = document.getElementById('ckSpring').checked;
    document.getElementById('ckAllSeasons_hidden').checked = selectAllChecked;
}
