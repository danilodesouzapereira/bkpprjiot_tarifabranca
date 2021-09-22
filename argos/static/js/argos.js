/*
Função para converter um string de códigos ASCII com representação hexa para texto
*/
function asciiToText(data_payload) {
  var i;
  var code;
  var str = '';
  //varre string do payload
  for (i = 0; i < data_payload.length; i = i + 2) {
    code = parseInt(data_payload.slice(i, i + 2), 16);
    str += String.fromCharCode(code);
  }
  return str;
}

/*
Função para converter um string em base64 para um string em hexa
*/
function base64ToHex(data_payload) {
  var raw = atob(data_payload);
  var HEX = '';
  //varre string do payload
  for (i = 0; i < raw.length; i++) {
    var _hex = raw.charCodeAt(i).toString(16);
    HEX += (_hex.length == 2 ? _hex: '0' + _hex);
  }
  return HEX.toUpperCase();
}

/*
Função para filtrar o conteúdo da barra de navegação conforme o que
o usuário digitou na caixa de busca. A função lê um elemento input chamado
inputSearch, um elemento nav chamado navMenu e elementos da classe
dropdown-item.
*/
function filterContent() {
  var i, objInput, objItems;
  objInput = document.getElementById('inputSearch');
  objItems = document.getElementById('navMenu').getElementsByClassName('dropdown-item');
  //varre todos os elementos da classe dropdown-item do navMenu
  for (i = 0; i < objItems.length; i++) {
    //verifica se o contúdo do elemento contém o texto
    //digitado pelo usuário
    if (objItems[i].innerHTML.toUpperCase().indexOf(objInput.value.toUpperCase()) == -1) {
      //esconde elemento
      objItems[i].style.display = 'none';
    }
    else {
      //exibe elemento
      objItems[i].style.display = 'block';
    }
  }
}

/*
Função para filtrar o conteúdo das tabelas de dispositivos conforme o que
o usuário digitou na caixa de busca. A função lê um elemento input chamado
inputSearch e elementos da classe com a tag <tr>.
*/
function filterTables() {
  var i, objInput, objItems;
  objInput = document.getElementById('inputSearch');
  objItems = document.getElementsByTagName('TR');
  //varre todas as linhas da tabela (<tr>)
  for (i = 0; i < objItems.length; i++) {
    //pega primeiro elemento filho (primeira coluna) e checa se é <td>
    if (objItems[i].children[0].tagName.indexOf('TD') == -1) continue;
    //se chegou a este ponto é porque o elemento <tr> contém apenas
    //elementos <td>, ou seja, não contém o título das tabelas:
    //verifica se texto da primeira coluna (descrição) contém o texto
    //digitado pelo usuário
    if (objItems[i].children[0].innerText.toUpperCase().indexOf(objInput.value.toUpperCase()) == -1) {
      //esconde linha da tabela
      objItems[i].style.display = 'none';
    }
    else {
      //exibe linha da tabeala
      objItems[i].style.display = '';
    }
  }
}

/*
Função para fazer get e set do scrollTop do navMenu.
*/
function getSetScrollTop() {
  var navMenu_scrollTop;

  //obtém ajuste salvo no último unload
  navMenu_scrollTop = localStorage.getItem('navMenu-scrollTop');
  //muda o scrollTop do navMenu
  document.getElementById('navMenu').scrollTop = navMenu_scrollTop;
  //cria evento para salver o novo scrollTop do navMenu antes do unload
  window.addEventListener('beforeunload', function() {
      localStorage.setItem('navMenu-scrollTop', document.getElementById('navMenu').scrollTop);
  })
}

/*
Função para salvar a última aba selecionada pelo usuário. Ela é recuperada após
qualquer refresh da página.
*/
function getSetActiveTab(){
    $(function() {
        // for bootstrap 3 use 'shown.bs.tab', for bootstrap 2 use 'shown' in the next line
        $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
            // save the latest tab
            localStorage.setItem('lastTab', $(this).attr('href'));
        });

        // go to the latest tab, if it exists:
        var lastTab = localStorage.getItem('lastTab');
        if (lastTab) {
            $('[href="' + lastTab + '"]').tab('show');
        }
    });
}


/*
Função para adicionar um evento a cada objeto da classe
dropdown-toggle para impedir que um deles colapse quando outro
for expandido. A função lê todos os elementos da classe dropdown-toggle.
*/
function initDropdown() {
  var i;
  var dropdown = document.getElementsByClassName('dropdown-toggle');
  //adiciona evento a cada objeto da classe dropdown-toggle
  for (i = 0; i < dropdown.length; i++) {
    dropdown[i].addEventListener('click', function() {
      this.classList.toggle('active');
      var dropdownContent = this.nextElementSibling;
      if (dropdownContent.style.display === 'none') {
        //exibe
        dropdownContent.style.display = 'block';
      }
      else {
        //esconde
        dropdownContent.style.display = 'none';
      }
    });
  }
}

/*
Função para imprimir dados do monitor1.
*/
function printDataMonitor1(data) {
  var va, vb, vc;
  var ia, ib, ic;
  var data_payload, values;

  if (data['data_format'] == 'base64') {
    data_payload = atob(data['logs'][0]['data_payload']);
  }
  else if (data['data_format'] == 'hexa') {
    data_payload = data['logs'][0]['data_payload'];
  }

  values = data_payload.split(',');
  va = parseFloat(values[1]);
  ia = parseFloat(values[2]);
  vb = parseFloat(values[3]);
  ib = parseFloat(values[4]);
  vc = parseFloat(values[5]);
  ic = parseFloat(values[6]);

  document.getElementById('datetime_rx_' + data['eui'].toUpperCase()).innerHTML = formatTime(parseTime(data['logs'][0]['datetime_rx']));
  document.getElementById('va_' + data['eui'].toUpperCase()).innerHTML = 'Tensão fase A: ' + formatNumber(va, 1);
  document.getElementById('vb_' + data['eui'].toUpperCase()).innerHTML = 'Tensão fase B: ' + formatNumber(vb, 1);
  document.getElementById('vc_' + data['eui'].toUpperCase()).innerHTML = 'Tensão fase C: ' + formatNumber(vc, 1);
  document.getElementById('ia_' + data['eui'].toUpperCase()).innerHTML = 'Corrente fase B: ' + formatNumber(ia, 1);
  document.getElementById('ib_' + data['eui'].toUpperCase()).innerHTML = 'Corrente fase A: ' + formatNumber(ib, 1);
  document.getElementById('ic_' + data['eui'].toUpperCase()).innerHTML = 'Corrente fase B: ' + formatNumber(ic, 1);

}

/*
Função para imprimir dados do monitor2.
*/
function printDataMonitor2(data) {
  var pulseC;
  var pulseG;
  var lid;
  var status;
  var card_code;
  var batl;
  var data_payload;

  if (data['data_format'] == 'base64') {
    data_payload = base64ToHex(data['logs'][0]['data_payload']);
  }
  else if (data['data_format'] == 'hexa') {
    data_payload = data['logs'][0]['data_payload'];
  }

  /*
  Até 19/12/2019 os pacotes possuíam 23 bytes (46 caracteres). Nesse
  dia, a Mauá fez uma mudança no pacote, que passou a ter 25 bytes
  (50 caracteres). Dessa forma, para manter a compatibilidade com o
  histórico, é preciso verificar o tamanho do payload antes de extrair
  os dados.
  */
  if (data_payload.length == 46) {
    pulseC = data_payload.slice(2, 8);
    pulseG = data_payload.slice(10, 16);
    lid = data_payload.slice(18, 22);
    status = data_payload.slice(24, 28);
    card_code = data_payload.slice(30, 40);
    batl = data_payload.slice(42, 46);
  }
  else if (data_payload.length == 50) {
    pulseC = data_payload.slice(2, 10);
    pulseG = data_payload.slice(12, 20);
    lid = data_payload.slice(22, 26);
    status = data_payload.slice(28, 32);
    card_code = data_payload.slice(34, 44);
    batl = data_payload.slice(46, 50);
  }

  document.getElementById('datetime_rx_' + data['eui'].toUpperCase()).innerHTML = formatTime(parseTime(data['logs'][0]['datetime_rx']));
  document.getElementById('pulseC_' + data['eui'].toUpperCase()).innerHTML = 'Leitura consumo: ' + parseInt(pulseC, 16) + ' pulsos';
  document.getElementById('pulseG_' + data['eui'].toUpperCase()).innerHTML = 'Leitura geração: ' + parseInt(pulseG, 16) + ' pulsos';
  document.getElementById('lid_' + data['eui'].toUpperCase()).innerHTML = 'Tampa: ' + (parseInt(lid, 16) > 1000 ? 'Aberta' : 'Fechada');
  document.getElementById('status_' + data['eui'].toUpperCase()).innerHTML = 'Estado: ' + (parseInt(status, 16) > 1000 ? 'Desligado' : 'Ligado');
  document.getElementById('card_code_' + data['eui'].toUpperCase()).innerHTML = 'Cartão: ' + card_code;
  document.getElementById('batl_' + data['eui'].toUpperCase()).innerHTML = 'Nível da bateria: ' + formatNumber(parseInt(batl, 16)/1000) + ' V';
  //habilita/desabilita botões conforme permissão de usuário e valor de estado
  if(document.getElementById('is_admin').innerHTML == 'True') {
    if (parseInt(status, 16) > 1000) {
        document.getElementById('turnOn_' + data['eui'].toUpperCase()).disabled = false;
        document.getElementById('turnOff_' + data['eui'].toUpperCase()).disabled = true;
      }
      else {
      document.getElementById('turnOn_' + data['eui'].toUpperCase()).disabled = true;
      document.getElementById('turnOff_' + data['eui'].toUpperCase()).disabled = false;
    }
  }
}

/*
Função para imprimir dados do monitor4.
*/
function printDataMonitor4(data) {
  var lat;
  var long;
  var data_payload;

  if (data['data_format'] == 'base64') {
    data_payload = base64ToHex(data['logs'][0]['data_payload']);
  }
  else if (data['data_format'] == 'hexa') {
    data_payload = data['logs'][0]['data_payload'];
  }

  lat = asciiToText(data_payload.slice(8, 26));
  long = asciiToText(data_payload.slice(32, 50));

  document.getElementById('datetime_rx_' + data['eui'].toUpperCase()).innerHTML = formatTime(parseTime(data['logs'][0]['datetime_rx']));
  document.getElementById('lat_' + data['eui'].toUpperCase()).innerHTML = 'Latitude: ' + formatNumber(lat, 6);
  document.getElementById('long_' + data['eui'].toUpperCase()).innerHTML = 'Longitude: ' + formatNumber(long, 6);
}

/*
Função para imprimir dados do monitor5.
*/
function printDataMonitor5(data) {
  var temp;
  var humid;
  var batl;
  var data_payload;

  if (data['data_format'] == 'base64') {
    data_payload = base64ToHex(data['logs'][0]['data_payload']);
  }
  else if (data['data_format'] == 'hexa') {
    data_payload = data['logs'][0]['data_payload'];
  }

  temp = data_payload.slice(2, 6);
  humid = data_payload.slice(8, 12);
  batl = data_payload.slice(14, 18);

  document.getElementById('datetime_rx_' + data['eui'].toUpperCase()).innerHTML = formatTime(parseTime(data['logs'][0]['datetime_rx']));
  document.getElementById('temp_' + data['eui'].toUpperCase()).innerHTML = 'Temperatura: ' + formatNumber(parseInt(temp, 16)/10) + ' °C';
  document.getElementById('humid_' + data['eui'].toUpperCase()).innerHTML = 'Umidade: ' + formatNumber(parseInt(humid, 16)/10) + ' %';
  document.getElementById('batl_' + data['eui'].toUpperCase()).innerHTML = 'Nível da bateria: ' + formatNumber(parseInt(batl, 16)/1000) + ' V';
}

/*
Função para fazer reset do scrollTop do navMenu.
*/
function resetScrollTop() {
  localStorage.setItem('navMenu-scrollTop', 0);
}


/*
Função para inicializar os checkboxes para filtros do dia típico
*/
function setFiltersInitValue(valuesJson_daysFilter, valuesJson_seasonsFilter) {

  // marca/desmarca dias da semana
  var checked = false;
  if (valuesJson_daysFilter['ck2af'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ck2af').checked = checked;
  if (valuesJson_daysFilter['ck3af'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ck3af').checked = checked;
  if (valuesJson_daysFilter['ck4af'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ck4af').checked = checked;
  if (valuesJson_daysFilter['ck5af'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ck5af').checked = checked;
  if (valuesJson_daysFilter['ck6af'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ck6af').checked = checked;
  if (valuesJson_daysFilter['ckSab'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ckSab').checked = checked;
  if (valuesJson_daysFilter['ckDom'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ckDom').checked = checked;

  // marca/desmarca filtros de estações do ano
  if (valuesJson_seasonsFilter['ckSummer'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ckSummer').checked = checked;
  if (valuesJson_seasonsFilter['ckFall'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ckFall').checked = checked;
  if (valuesJson_seasonsFilter['ckWinter'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ckWinter').checked = checked;
  if (valuesJson_seasonsFilter['ckSpring'] == 1){checked = true;}else{checked = false;}
  document.getElementById('ckSpring').checked = checked;
}