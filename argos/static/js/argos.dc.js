//função para definir configurações de tempo para o Brasil
function formatLocale() {
  var pt_BR = {
    'decimal': ',',
    'thousands': '.',
    'grouping': [3],
    'currency': ['R$', ''],
    'dateTime': '%d/%m/%Y %H:%M:%S.%f',
    'date': '%d/%m/%Y',
    'time': '%H:%M',
    'periods': ['AM', 'PM'],
    'days': ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'],
    'shortDays': ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
    'months': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
    'shortMonths': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  }
  //definições locais para tempo
  d3.timeFormatDefaultLocale(pt_BR);
  d3.formatDefaultLocale(pt_BR);
}

//função para fazer o parse de um string para uma data (formato dd/mm/yyyy hh:mm:ss)
function parseTime(val) {
  var pt = d3.timeParse('%d/%m/%Y %H:%M:%S');
  return pt(val);
}

//função para formatar uma data em um string (formato dd/mm/yyyy hh:mm:ss)
function formatTime(val) {
  var ft = d3.timeFormat('%d/%m/%Y %H:%M:%S');
  return ft(val);
}

//função para formatar um número com N casas decimais
function formatNumber(val, dec = 1) {
  return(val.toLocaleString('pt-BR', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec
  }));
}

//função para converter medida de minutos em um string do tipo hh:mm:ss
//utiliza um tipo const date javascript
function minToTime(val) {
  const date = new Date('Jan 01, 2000 00:00:00');
  if (val >= 60) {
    date.setHours(parseInt(val / 60));
  }
  date.setMinutes(parseInt(val) % 10);
  date.setSeconds(parseInt(parseInt(60 * (val - parseInt(val)))));
  var str_date = date.toString();
  return str_date.slice(16, 24);
}

//função para preencher um gráfico e uma tabela passados como parâmetro
//dispositivo tipo 1 - sensor de tensão e corrente
function dcChartTable1 (valuesJson, dcChartName1, dcChartName2,
                        dcRangeChartName1, dcRangeChartName2,
                        dcTableName1, dcTableName2) {
  //configura esquema de cores do gráfico
  dc.config.defaultColors(d3.schemeCategory10);
  //variáveis para guardar tensão máxima e corrente máxima
  var maxV = 0;
  var maxI = 0;
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valores máximos de cada dimensão
  var maxTime = valuesJson.reduce(function(max, d) { return (d.intervalo > max) ? d.intervalo : max; }, 0);
  var maxVA = valuesJson.reduce(function(max, d) { return (d.va > max) ? d.va : max; }, 0);
  var maxVB = valuesJson.reduce(function(max, d) { return (d.vb > max) ? d.vb : max; }, 0);
  var maxVC = valuesJson.reduce(function(max, d) { return (d.vc > max) ? d.vc : max; }, 0);
  var maxIA = valuesJson.reduce(function(max, d) { return (d.ia > max) ? d.ia : max; }, 0);
  var maxIB = valuesJson.reduce(function(max, d) { return (d.ib > max) ? d.ib : max; }, 0);
  var maxIC = valuesJson.reduce(function(max, d) { return (d.ic > max) ? d.ic : max; }, 0);
  //determina tensão máxim e corrente máxima
  if (maxVA > maxV) maxV = maxVA;
  if (maxVB > maxV) maxV = maxVB;
  if (maxVC > maxV) maxV = maxVC;
  if (maxIA > maxI) maxI = maxIA;
  if (maxIB > maxI) maxI = maxIB;
  if (maxIC > maxI) maxI = maxIC;
  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.datetime_rx;});
  //define os grupos (o que vai no eixo y)
  var vaGroup = timeDim.group().reduceSum(function(d) {return d.va;});
  var vbGroup = timeDim.group().reduceSum(function(d) {return d.vb;});
  var vcGroup = timeDim.group().reduceSum(function(d) {return d.vc;});
  var iaGroup = timeDim.group().reduceSum(function(d) {return d.ia;});
  var ibGroup = timeDim.group().reduceSum(function(d) {return d.ib;});
  var icGroup = timeDim.group().reduceSum(function(d) {return d.ic;});
  var timeGroup = timeDim.group().reduceSum(function(d) {return d.interval;});
  //define limites
  var minDate = timeDim.bottom(1)[0]['datetime_rx'];
  var maxDate =  timeDim.top(1)[0]['datetime_rx'];

  //cria 2 gráficos para servir de rangeChart (filtro)
  var dcRangeChart1 = dc.lineChart(dcRangeChartName1);
  var dcRangeChart2 = dc.lineChart(dcRangeChartName2);
  //define rangeCharts, que deverão ser feitos para va e tempo:
  //pelo menos essas informações deverão ser fornecidas
  dcRangeChart1
    .useViewBoxResizing(true)
    .margins({top: 5, right: 68, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(vaGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxVA]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  dcRangeChart2
    .useViewBoxResizing(true)
    .margins({top: 5, right: 20, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(timeGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxTime]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);

  //cria gráficos compostos
  var dcChart1 = dc.compositeChart(dcChartName1);
  var dcChart2 = dc.compositeChart(dcChartName2);

  //cria gráfico para cada grupo
  //gráfico da tensão na fase A
  var dcChartVA = dc.lineChart(dcChart1);
  dcChartVA
    .group(vaGroup, 'VA [V]')
    .colors('blue');
    //gráfico da tensão na fase B
  var dcChartVB = dc.lineChart(dcChart1);
  dcChartVB
    .group(vbGroup, 'VB [V]')
    .colors('orange');
  //gráfico da tensão na fase C
  var dcChartVC = dc.lineChart(dcChart1);
  dcChartVC
    .group(vcGroup, 'VC [V]')
    .colors('green');
  //gráfico da corrente na fase A
  var dcChartIA = dc.lineChart(dcChart1);
  dcChartIA
    .group(iaGroup, 'IA [A]')
    .colors('red')
    .useRightYAxis(true);
  //gráfico da corrente na fase B
  var dcChartIB = dc.lineChart(dcChart1);
  dcChartIB
    .group(ibGroup, 'IB [A]')
    .colors('purple')
    .useRightYAxis(true);
  //gráfico da corrente na fase C
  var dcChartIC = dc.lineChart(dcChart1);
  dcChartIC
    .group(icGroup, 'IC [A]')
    .colors('brown')
    .useRightYAxis(true);
  //gráfico do tempo desde o último envio
  var dcChartTime = dc.lineChart(dcChart2);
  dcChartTime
    .group(timeGroup, 'Tempo desde o último envio [min]')
    .colors('brown')

  //define os gráficos compostos
  dcChart1
    .useViewBoxResizing(true)
    .margins({top: 30, right: 65, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxV]))
    .rightY(d3.scaleLinear().domain([0, 2.1*maxI]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart1)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .yAxisLabel('Tensão [V]', 16)
    .rightYAxisLabel('Corrente [A]', 16)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value, 1);
    });
  dcChart2
    .useViewBoxResizing(true)
    .margins({top: 30, right: 20, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxTime]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart2)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .yAxisLabel('Tempo [min]', 16)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + minToTime(d.value);
    });

  //compôe todas as curvas nos gráficos compostos
  dcChart1.compose([dcChartVA, dcChartIA, dcChartVB, dcChartIB, dcChartVC, dcChartIC]);
  dcChart2.compose([dcChartTime]);

  //cria uma dimensão para as tabelas
  var allDim = ndx.dimension(function(d) {return d;});

  //cria tabelas
  var dcTable1 = dc.dataTable(dcTableName1);
  var dcTable2 = dc.dataTable(dcTableName2);

  //define tabela2
  dcTable1
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  dcTable2
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);

  //define as colunas que as tabelas devem exibir
  dcTable1
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return formatNumber(d.va);},
      function(d) {return formatNumber(d.ia);},
      function(d) {return formatNumber(d.vb);},
      function(d) {return formatNumber(d.ib);},
      function(d) {return formatNumber(d.vc);},
      function(d) {return formatNumber(d.ic);}
    ]);
  dcTable2
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return d.data_payload;}
    ]);

  //variáveis para paginação da tabela
  var offset = 0;
  var recs = window.innerHeight/50;
  //render chart and table
  renderChartTable();
  //função para habilitar desabilitar botões
  function display() {
    d3.select('#id_next')
      .attr('disabled', (offset + recs) >= ndx.groupAll().reduceCount().value() ? 'true' : null);
    d3.select('#id_previous')
      .attr('disabled', offset <= 0 ? 'true' : null);
  }
  //função para atualizar paginação das tabelas
  function update() {
    dcTable1.beginSlice(offset); dcTable2.beginSlice(offset);
    dcTable1.endSlice(offset + recs); dcTable2.endSlice(offset + recs);
    display();
  }
  //função para ir para a próxima página das tabelas
  function next() {
    offset += recs;
    update();
    dcTable1.redraw(); dcTable2.redraw();
  }
  //função para ir para a página anterior das tabelas
  function previous() {
    offset -= recs;
    if (offset < 0) offset = 0;
    update();
    dcTable1.redraw(); dcTable2.redraw();
  }
  //function to render chart and table
  function renderChartTable() {
    //define razão largura/altura para gráfico
    var ratio = 2.4;
    //define proporção de altura entre chart e rangeChart
    var prop = 0.1;
    //variáveis para altura e largura
    var height;
    var width;
    //redefine número de registros para paginação da tabela em função da altura
    recs = Math.round(window.innerHeight/50);
    //atualiza tabela
    update();
    //define propriedades dos gráficos
    width = document.getElementById('myChart1').clientWidth;
    if (document.getElementById('myChart2').clientWidth > width) {
      width = document.getElementById('myChart2').clientWidth;
    }
    height = Math.round(prop*width/ratio);
    height = (height >= 50) ? height : 50;
    dcRangeChart1.width(width); dcRangeChart2.width(width);
    dcRangeChart1.height(height); dcRangeChart2.height(height);
    dcRangeChart1.xAxis().ticks(Math.round(dcRangeChart1.width()/190));
    dcRangeChart2.xAxis().ticks(Math.round(dcRangeChart2.width()/190));
    dcRangeChart1.yAxis().ticks(Math.round(dcRangeChart1.height()/130));
    dcRangeChart2.yAxis().ticks(Math.round(dcRangeChart2.height()/130));
    height = Math.round(width/ratio) - dcRangeChart1.height();
    height = (height >= 200) ? height : 200;
    dcChart1.width(width); dcChart2.width(width);
    dcChart1.height(height); dcChart2.height(height);
    dcChartVA.width(width);
    dcChartVB.width(width);
    dcChartVC.width(width);
    dcChartIA.width(width);
    dcChartIB.width(width);
    dcChartIC.width(width);
    dcChartTime.width(width);
    dcChartVA.height(height);
    dcChartVB.height(height);
    dcChartVC.height(height);
    dcChartIA.height(height);
    dcChartIB.height(height);
    dcChartIC.height(height);
    dcChartTime.height(height);
    dcChart1.xAxis().ticks(Math.round(dcChart1.width()/190));
    dcChart2.xAxis().ticks(Math.round(dcChart2.width()/190));
    dcChart1.yAxis().ticks(Math.round(dcChart1.height()/130));
    dcChart2.yAxis().ticks(Math.round(dcChart2.height()/130));
    dcChart1.legend(dc.legend().x(80).y(height - 85).itemHeight(13).gap(5).horizontal(true).legendWidth(140).itemWidth(70));
    dcChart2.legend(dc.legend().x(80).y(height - 50).itemHeight(13).gap(5).horizontal(true).legendWidth(140).itemWidth(70));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
  //adiciona evento onclick aos botões id_next e id_previous
  document.getElementById('id_next').addEventListener('click', next, false);
  document.getElementById('id_previous').addEventListener('click', previous, false);
}

//função para preencher um gráfico e uma tabela passados como parâmetro
//dispositivo tipo 2 - remota para medidor de energia
function dcChartTable2 (valuesJson,
                        dcChartName1, dcChartName2, dcChartName3,
                        dcRangeChartName1, dcRangeChartName2, dcRangeChartName3,
                        dcTableName1, dcTableName2, dcTableName3, dcTableName4) {
  //configura esquema de cores do gráfico
  dc.config.defaultColors(d3.schemeCategory10);
  //variável para guardar demanda máxima
  var maxD = 0;
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valor máximo de cada dimensão
  var maxV = valuesJson.reduce(function(max, d) { return (d.batl > max) ? d.batl : max; }, 0);
  var maxTime = valuesJson.reduce(function(max, d) { return (d.interval > max) ? d.interval : max; }, 0);
  var maxDemC = valuesJson.reduce(function(max, d) { return (d.demC > max) ? d.demC : max; }, 0);
  var maxDemG = valuesJson.reduce(function(max, d) { return (d.demG > max) ? d.demG : max; }, 0);
  if (maxDemC > maxD) maxD = maxDemC;
  if (maxDemG > maxD) maxD = maxDemG;
  //determina valores máximo e mínimo de SNR e RSSI
  var maxSNR = valuesJson.reduce(function(max, d) { return (d.snr > max) ? d.snr : max; }, 0);
  var maxRSSI = valuesJson.reduce(function(max, d) { return (d.rssi > max) ? d.rssi : max; }, 0);
  var minSNR = valuesJson.reduce(function(min, d) { return (d.snr < min) ? d.snr : min; }, 0);
  var minRSSI = valuesJson.reduce(function(min, d) { return (d.rssi < min) ? d.rssi : min; }, 0);
  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.datetime_rx;});
  //define os grupos (o que vai no eixo y)
  var demCGroup = timeDim.group().reduceSum(function(d) {return d.demC;});
  var demGGroup = timeDim.group().reduceSum(function(d) {return d.demG;});
  var batlGroup = timeDim.group().reduceSum(function(d) {return d.batl;});
  var timeGroup = timeDim.group().reduceSum(function(d) {return d.interval;});
  var snrGroup  = timeDim.group().reduceSum(function(d) {return d.snr;});
  var rssiGroup = timeDim.group().reduceSum(function(d) {return d.rssi;});
  //define limites
  var minDate = timeDim.bottom(1)[0]['datetime_rx'];
  var maxDate =  timeDim.top(1)[0]['datetime_rx'];

  //cria 3 gráficos para servir de rangeChart (filtro)
  var dcRangeChart1 = dc.lineChart(dcRangeChartName1);
  //define rangeChart
  dcRangeChart1
    .useViewBoxResizing(true)
    .margins({top: 5, right: 20, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(demCGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxD]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  var dcRangeChart2 = dc.lineChart(dcRangeChartName2);
  //define rangeChart
  dcRangeChart2
    .useViewBoxResizing(true)
    .margins({top: 5, right: 68, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(batlGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxV]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  var dcRangeChart3 = dc.lineChart(dcRangeChartName3);
  //define rangeChart
  dcRangeChart3
    .useViewBoxResizing(true)
    .margins({top: 5, right: 68, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(batlGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([1.1*minSNR, 1.1*maxSNR]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);

  //cria 3 gráficos compostos
  var dcChart1 = dc.compositeChart(dcChartName1);
  var dcChart2 = dc.compositeChart(dcChartName2);
  var dcChart3 = dc.compositeChart(dcChartName3);

  //cria gráfico para cada grupo
  //gráfico da demanda consumida
  var dcChartDC = dc.lineChart(dcChart1);
  dcChartDC
    .group(demCGroup, 'Demanda Consumida [W]')
    .colors('blue');
  //gráfico da demanda gerada
  var dcChartDG = dc.lineChart(dcChart1);
  dcChartDG
    .group(demGGroup, 'Demanda Gerada [W]')
    .colors('orange');
  //gráfico do nível da bateria
  var dcChartV = dc.lineChart(dcChart2);
  dcChartV
    .group(batlGroup, 'Nível da Bateria [V]')
    .colors('green');
  //gráfico do tempo desde o último envio
  var dcChartTime = dc.lineChart(dcChart2);
  dcChartTime
    .group(timeGroup, 'Tempo desde o último envio [min]')
    .colors('red')
    .useRightYAxis(true);
  //gráfico do SNR
  var dcChartSNR = dc.lineChart(dcChart3);
  dcChartSNR
    .group(snrGroup, 'SNR')
    .colors('green');
  //gráfico do RSSI
  var dcChartRSSI = dc.lineChart(dcChart3);
  dcChartRSSI
    .group(rssiGroup, 'RSSI [dbi]')
    .colors('red')
    .useRightYAxis(true);

  //define gráficos
  dcChart1
    .useViewBoxResizing(true)
    .margins({top: 30, right: 20, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxD]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart1)
    .yAxisLabel('Demanda [W]', 16)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value, 1);
    });
  dcChart2
    .useViewBoxResizing(true)
    .margins({top: 30, right: 65, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxV]))
    .rightY(d3.scaleLinear().domain([0, 1.1*maxTime]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart2)
    .yAxisLabel('Nível da Bateria [V]', 16)
    .rightYAxisLabel('Tempo [min]', 16)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value, 2);
    });
  dcChart3
    .useViewBoxResizing(true)
    .margins({top: 30, right: 65, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([1.1*minSNR, 1.1*maxSNR]))
    .rightY(d3.scaleLinear().domain([1.1*minRSSI, 1.1*maxRSSI]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart3)
    .yAxisLabel('SNR', 16)
    .rightYAxisLabel('RSSI [dbi]', 16)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value, 2);
    });

  //compôe todas as curvas nos gráficos compostos
  dcChart1.compose([dcChartDC, dcChartDG]);
  dcChart2.compose([dcChartV, dcChartTime]);
  dcChart3.compose([dcChartSNR, dcChartRSSI]);

  //cria uma dimensão para as tabelas
  var allDim = ndx.dimension(function(d) {return d;});

  //cria tabelas
  var dcTable1 = dc.dataTable(dcTableName1);
  var dcTable2 = dc.dataTable(dcTableName2);
  var dcTable3 = dc.dataTable(dcTableName3);
  var dcTable4 = dc.dataTable(dcTableName4);

  //define as tabelas
  dcTable1
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  dcTable2
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  dcTable3
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  dcTable4
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);

  //define as colunas que as tabelas devem exibir
  dcTable1
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return formatNumber(d.demC);},
      function(d) {return d.pulseC;},
  ]);
  dcTable2
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return formatNumber(d.demG);},
      function(d) {return d.pulseG;},
  ]);
  dcTable3
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return (d.lid > 1000) ? 'Aberta' : 'Fechada';},
      function(d) {return (d.status > 1000) ? 'Desligado' : 'Ligado';},
      function(d) {return d.card_code;},
      function(d) {return formatNumber(d.batl);}
  ]);
  dcTable4
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return d.data_payload;},
      function(d) {return formatNumber(d.interval);},
      function(d) {return formatNumber(d.snr);},
      function(d) {return formatNumber(d.rssi);}
  ]);

  //variáveis para paginação das tabelas
  var offset = 0;
  var recs = window.innerHeight/50;
  //render chart and table
  renderChartTable();
  //função para exportar os dados visualizados em uma determinada página
  function exportData() {
    download(d3.csvFormat(ndx.all()), 'deviceData.csv', 'text/plain');
  }
  //função para habilitar desabilitar botões
  function display() {
    d3.select('#id_next')
      .attr('disabled', (offset + recs) >= ndx.groupAll().reduceCount().value() ? 'true' : null);
    d3.select('#id_previous')
      .attr('disabled', offset <= 0 ? 'true' : null);
  }
  //função para atualizar paginação das tabelas
  function update() {
    dcTable1.beginSlice(offset); dcTable2.beginSlice(offset);
    dcTable3.beginSlice(offset); dcTable4.beginSlice(offset);
    dcTable1.endSlice(offset + recs); dcTable2.endSlice(offset + recs);
    dcTable3.endSlice(offset + recs); dcTable4.endSlice(offset + recs);
    display();
  }
  //função para ir para a próxima página das tabelas
  function next() {
    offset += recs;
    update();
    dcTable1.redraw(); dcTable2.redraw(); dcTable3.redraw(); dcTable4.redraw();
  }
  //função para ir para a página anterior das tabelas
  function previous() {
    offset -= recs;
    if (offset < 0) offset = 0;
    update();
    dcTable1.redraw(); dcTable2.redraw(); dcTable3.redraw(); dcTable4.redraw();
  }
  //function to render chart and table
  function renderChartTable() {
    //define razão largura/altura para gráfico
    var ratio = 2.4;
    //define proporção de altura entre chart e rangeChart
    var prop = 0.1;
    //variáveis para altura e largura
    var height;
    var width;
    //redefine número de registros para paginação da tabela em função da altura
    recs = Math.round(window.innerHeight/50);
    //atualiza tabela
    update();
    //define propriedades dos gráficos
    width = document.getElementById('myChart1').clientWidth;
    if (document.getElementById('myChart2').clientWidth > width) {
      width = document.getElementById('myChart2').clientWidth;
    }
    if (document.getElementById('myChart3').clientWidth > width) {
      width = document.getElementById('myChart3').clientWidth;
    }
    height = Math.round(prop*width/ratio);
    height = (height >= 50) ? height : 50;
    dcRangeChart1.width(width); dcRangeChart2.width(width); dcRangeChart3.width(width);
    dcRangeChart1.height(height); dcRangeChart2.height(height); dcRangeChart3.height(height);
    dcRangeChart1.xAxis().ticks(Math.round(dcRangeChart1.width()/190));
    dcRangeChart2.xAxis().ticks(Math.round(dcRangeChart2.width()/190));
    dcRangeChart3.xAxis().ticks(Math.round(dcRangeChart3.width()/190));
    dcRangeChart1.yAxis().ticks(Math.round(dcRangeChart1.height()/130));
    dcRangeChart2.yAxis().ticks(Math.round(dcRangeChart2.height()/130));
    dcRangeChart3.yAxis().ticks(Math.round(dcRangeChart3.height()/130));
    height = Math.round(width/ratio) - dcRangeChart1.height();
    height = (height >= 200) ? height : 200;
    dcChart1.width(width); dcChart2.width(width); dcChart3.width(width);
    dcChart1.height(height); dcChart2.height(height); dcChart3.height(height);
    dcChartDC.width(width);
    dcChartDG.width(width);
    dcChartV.width(width);
    dcChartTime.width(width);
    dcChartDC.height(height);
    dcChartDG.height(height);
    dcChartV.height(height);
    dcChartTime.height(height);
    dcChartSNR.height(height);
    dcChartRSSI.height(height);
    dcChart1.xAxis().ticks(Math.round(dcChart1.width()/190));
    dcChart2.xAxis().ticks(Math.round(dcChart2.width()/190));
    dcChart3.xAxis().ticks(Math.round(dcChart3.width()/190));
    dcChart1.yAxis().ticks(Math.round(dcChart1.height()/130));
    dcChart2.yAxis().ticks(Math.round(dcChart2.height()/130));
    dcChart3.yAxis().ticks(Math.round(dcChart3.height()/130));
    dcChart1.yAxis().tickFormat(d3.format('~s'));
    dcChart1.legend(dc.legend().x(80).y(height - 65).itemHeight(13).gap(5).horizontal(false).legendWidth(140).itemWidth(70));
    dcChart2.legend(dc.legend().x(80).y(height - 65).itemHeight(13).gap(5).horizontal(false).legendWidth(140).itemWidth(70));
    dcChart3.legend(dc.legend().x(80).y(height - 65).itemHeight(13).gap(5).horizontal(false).legendWidth(140).itemWidth(70));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
  //adiciona evento onclick aos botões id_next e id_previous
  document.getElementById('id_next').addEventListener('click', next, false);
  document.getElementById('id_previous').addEventListener('click', previous, false);
  //adiciona evento onclick ao botão id_export
  document.getElementById('id_export').addEventListener('click', exportData, false);
}

//função para preencher um gráfico e uma tabela passados como parâmetro
//dispositivo tipo 3 - sensor de temperatura
function dcChartTable3 (valuesJson, dcChartName, dcRangeChartName, dcTableName) {
  //configura esquema de cores do gráfico
  dc.config.defaultColors(d3.schemeCategory10);
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valor máximo de cada dimensão
  var maxT = valuesJson.reduce(function(max, d) { return (d.temp > max) ? d.temp : max; }, 0);
  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.datetime_rx;});
  //define um grupo (o que vai no eixo y)
  var tempGroup = timeDim.group().reduceSum(function(d) {return d.temp;});
  //define limites
  var minDate = timeDim.bottom(1)[0]['datetime_rx'];
  var maxDate =  timeDim.top(1)[0]['datetime_rx'];

  //cria um gráfico para servir de rangeChart (filtro)
  var dcRangeChart = dc.lineChart(dcRangeChartName);
  //define rangeChart
  dcRangeChart
    .useViewBoxResizing(true)
    .margins({top: 5, right: 20, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(tempGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxT]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  //cria gráfico
  var dcChart = dc.lineChart(dcChartName);
  //define gráfico
  dcChart
    .useViewBoxResizing(true)
    .margins({top: 30, right: 20, bottom: 30, left: 60})
    .dimension(timeDim)
    .group(tempGroup, 'Temperatura [°C]')
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxT]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart)
    .yAxisLabel('Temperatura [°C]', 16)
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value, 1);
    });
  //cria uma dimensão para a tabela
  var allDim = ndx.dimension(function(d) {return d;});
  //cria tabela
  var dcTable = dc.dataTable(dcTableName);
  //define tabela
  dcTable
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  //define as colunas que a tabela deve exibir
  dcTable
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return formatNumber(1.0*d.temp, 1);},
      function(d) {return d.payload;}
  ]);
  //variáveis para paginação da tabela
  var offset = 0;
  var recs = window.innerHeight/50;
  //render chart and table
  renderChartTable();
  //função para habilitar desabilitar botões
  function display() {
    d3.select('#id_next')
      .attr('disabled', (offset + recs) >= ndx.groupAll().reduceCount().value() ? 'true' : null);
    d3.select('#id_previous')
      .attr('disabled', offset <= 0 ? 'true' : null);
  }
  //função para atualizar paginação da tabela
  function update() {
    dcTable.beginSlice(offset);
    dcTable.endSlice(offset + recs);
    display();
  }
  //função para ir para a próxima página da tabela
  function next() {
    offset += recs;
    update();
    dcTable.redraw();
  }
  //função para ir para a página anterior da tabela
  function previous() {
    offset -= recs;
    if (offset < 0) offset = 0;
    update();
    dcTable.redraw();
  }
  //function to render chart and table
  function renderChartTable() {
    //define razão largura/altura para gráfico
    var ratio = 2.4;
    //define proporção de altura entre chart e rangeChart
    var prop = 0.1;
    //variáveis para altura e largura
    var height;
    var width;
    //redefine número de registros para paginação da tabela em função da altura
    recs = Math.round(window.innerHeight/50);
    //atualiza tabela
    update();
    //define propriedades dos gráficos
    width = document.getElementById('myChart').clientWidth;
    height = Math.round(prop*width/ratio);
    height = (height >= 50) ? height : 50;
    dcRangeChart.width(width);
    dcRangeChart.height(height);
    dcRangeChart.xAxis().ticks(Math.round(dcRangeChart.width()/190));
    dcRangeChart.yAxis().ticks(Math.round(dcRangeChart.height()/130));
    height = Math.round(width/ratio) - dcRangeChart.height();
    height = (height >= 200) ? height : 200;
    dcChart.width(width);
    dcChart.height(height);
    dcChart.xAxis().ticks(Math.round(dcChart.width()/190));
    dcChart.yAxis().ticks(Math.round(dcChart.height()/130));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
  //adiciona evento onclick aos botões id_next e id_previous
  document.getElementById('id_next').addEventListener('click', next, false);
  document.getElementById('id_previous').addEventListener('click', previous, false);
}

//função para preencher uma tabela passada como parâmetro
//dispositivo tipo 4 - rastreador GPS
function dcChartTable4 (valuesJson, dcRangeChartName, dcTableName1, dcTableName2) {
  //configura esquema de cores do gráfico
  dc.config.defaultColors(d3.schemeCategory10);
  //proteção contra objetos com menos de 2 registros
  if (valuesJson['records'].length < 2) return;
  //variável para guardar SNR mínimo
  var minSNR = valuesJson['snr_min'];
  //variável para guardar SNR máximo
  var maxSNR = valuesJson['snr_max'];
  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson['records']);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.datetime_rx;});
  //define um grupo (o que vai no eixo y)
  var yGroup = timeDim.group().reduceSum(function(d) {return d.snr;});
  //define limites
  var minDate = timeDim.bottom(1)[0]['datetime_rx'];
  var maxDate =  timeDim.top(1)[0]['datetime_rx'];

  //cria um gráfico para servir de rangeChart (filtro)
  var dcRangeChart = dc.lineChart(dcRangeChartName);
  //define rangeChart
  dcRangeChart
    .useViewBoxResizing(true)
    .margins({top: 20, right: 2, bottom: 25, left: 8})
    .dimension(timeDim)
    .group(yGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([1.1*minSNR, 1.1*maxSNR]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  //cria uma dimensão para a tabela
  var allDim = ndx.dimension(function(d) {return d;});

  //cria tabelas
  var dcTable1 = dc.dataTable(dcTableName1);
  var dcTable2 = dc.dataTable(dcTableName2);

  //define tabelas
  dcTable1
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  dcTable2
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);

  //define as colunas que as tabelas devem exibir
  dcTable1
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return formatNumber(d.lat);},
      function(d) {return formatNumber(d.long);},
      function(d) {return formatNumber(d.snr);}
    ]);
  dcTable2
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return d.data_payload;},
      function(d) {return formatNumber(d.interval);},
      function(d) {return formatNumber(d.snr);},
      function(d) {return formatNumber(d.rssi);}
  ]);

  //variáveis para paginação da tabela
  var offset = 0;
  var recs = window.innerHeight/50;
  //render chart and table
  renderChartTable();
  //função para habilitar desabilitar botões
  function display() {
    d3.select('#id_next')
      .attr('disabled', (offset + recs) >= ndx.groupAll().reduceCount().value() ? 'true' : null);
    d3.select('#id_previous')
      .attr('disabled', offset <= 0 ? 'true' : null);
  }
  //função para atualizar paginação da tabela
  function update() {
    dcTable1.beginSlice(offset); dcTable2.beginSlice(offset);
    dcTable1.endSlice(offset + recs); dcTable2.endSlice(offset + recs);
    display();
  }
  //função para ir para a próxima página da tabela
  function next() {
    offset += recs;
    update();
    dcTable1.redraw(); dcTable2.redraw();
  }
  //função para ir para a página anterior da tabela
  function previous() {
    offset -= recs;
    if (offset < 0) offset = 0;
    update();
    dcTable1.redraw(); dcTable2.redraw();
  }
  //function to render chart and table
  function renderChartTable() {
    //define razão largura/altura para conjunto mapa+gráfico
    var ratio = 2.4;
    //define proporção de altura entre mapa e rangeChart
    var prop = 0.1;
    //variáveis para altura e largura
    var height;
    var width;
    //redefine número de registros para paginação da tabela em função da altura
    recs = Math.round(window.innerHeight/50);
    //atualiza tabela
    update();
    //define propriedades dos gráficos
    width = document.getElementById('myRangeChart').clientWidth;
    height = Math.round(prop*width/ratio);
    height = (height >= 70) ? height : 70;
    dcRangeChart.width(width);
    dcRangeChart.height(height);
    dcRangeChart.xAxis().ticks(Math.round(dcRangeChart.width()/190));
    dcRangeChart.yAxis().ticks(Math.round(dcRangeChart.height()/130));
    width = document.getElementById('myGeoMapChart').clientWidth;
    document.getElementById('myGeoMapChart').style.width = width + ' px';
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
  //adiciona evento onclick aos botões id_next e id_previous
  document.getElementById('id_next').addEventListener('click', next, false);
  document.getElementById('id_previous').addEventListener('click', previous, false);
}

//função para preencher um gráfico e uma tabela passados como parâmetro
//dispositivo tipo 5 - sensor de temperatura e umidade
function dcChartTable5 (valuesJson,
                        dcChartName1, dcChartName2, dcChartName3,
                        dcRangeChartName1, dcRangeChartName2, dcRangeChartName3,
                        dcTableName1, dcTableName2) {
  //configura esquema de cores do gráfico
  dc.config.defaultColors(d3.schemeCategory10);
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valores máximos de cada dimensão
  var maxT = valuesJson.reduce(function(max, d) { return (d.temp > max) ? d.temp : max; }, 0);
  var maxU = valuesJson.reduce(function(max, d) { return (d.humid > max) ? d.humid : max; }, 0);
  var maxV = valuesJson.reduce(function(max, d) { return (d.batl > max) ? d.batl : max; }, 0);
  var maxTime = valuesJson.reduce(function(max, d) { return (d.interval > max) ? d.interval : max; }, 0);
  //determina valores máximo e mínimo de SNR e RSSI
  var maxSNR = valuesJson.reduce(function(max, d) { return (d.snr > max) ? d.snr : max; }, 0);
  var maxRSSI = valuesJson.reduce(function(max, d) { return (d.rssi > max) ? d.rssi : max; }, 0);
  var minSNR = valuesJson.reduce(function(min, d) { return (d.snr < min) ? d.snr : min; }, 0);
  var minRSSI = valuesJson.reduce(function(min, d) { return (d.rssi < min) ? d.rssi : min; }, 0);
//cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.datetime_rx;});
  //define os grupos (o que vai no eixo y)
  var tempGroup = timeDim.group().reduceSum(function(d) {return d.temp;});
  var umidGroup = timeDim.group().reduceSum(function(d) {return d.humid;});
  var batlGroup = timeDim.group().reduceSum(function(d) {return d.batl;});
  var timeGroup = timeDim.group().reduceSum(function(d) {return d.interval;});
  var snrGroup  = timeDim.group().reduceSum(function(d) {return d.snr;});
  var rssiGroup = timeDim.group().reduceSum(function(d) {return d.rssi;});
  //define limites
  var minDate = timeDim.bottom(1)[0]['datetime_rx'];
  var maxDate =  timeDim.top(1)[0]['datetime_rx'];

  //cria 3 gráficos para servirem de rangeChart (filtro)
  var dcRangeChart1 = dc.lineChart(dcRangeChartName1);
  //define rangeChart
  dcRangeChart1
    .useViewBoxResizing(true)
    .margins({top: 5, right: 68, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(tempGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxT]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  var dcRangeChart2 = dc.lineChart(dcRangeChartName2);
  //define rangeChart
  dcRangeChart2
    .useViewBoxResizing(true)
    .margins({top: 5, right: 68, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(batlGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxV]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);
  var dcRangeChart3 = dc.lineChart(dcRangeChartName3);
  //define rangeChart
  dcRangeChart3
    .useViewBoxResizing(true)
    .margins({top: 5, right: 68, bottom: 25, left: 76})
    .dimension(timeDim)
    .group(snrGroup)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([1.1*minSNR, 1.1*maxSNR]))
    .renderArea(true)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .transitionDuration(500);

  //cria gráficos compostos
  var dcChart1 = dc.compositeChart(dcChartName1);
  var dcChart2 = dc.compositeChart(dcChartName2);
  var dcChart3 = dc.compositeChart(dcChartName3);

  //cria gráfico para cada grupo
  //gráfico da temperatura
  var dcChartT = dc.lineChart(dcChart1);
  dcChartT
    .group(tempGroup, 'Temperatura [°C]')
    .colors('blue');
  //gráfico da umidade
  var dcChartU = dc.lineChart(dcChart1);
  dcChartU
    .group(umidGroup, 'Umidade [%]')
    .colors('orange')
    .useRightYAxis(true);
  //gráfico do nível da bateria
  var dcChartV = dc.lineChart(dcChart2);
  dcChartV
    .group(batlGroup, 'Nível da Bateria [V]')
    .colors('green');
  //gráfico do tempo desde o último envio
  var dcChartTime = dc.lineChart(dcChart2);
  dcChartTime
    .group(timeGroup, 'Tempo desde o último envio [min]')
    .colors('red')
    .useRightYAxis(true);
  //gráfico do SNR
  var dcChartSNR = dc.lineChart(dcChart3);
  dcChartSNR
    .group(snrGroup, 'SNR')
    .colors('green');
  //gráfico do RSSI
  var dcChartRSSI = dc.lineChart(dcChart3);
  dcChartRSSI
    .group(rssiGroup, 'RSSI [dbi]')
    .colors('red')
    .useRightYAxis(true);

  //define os gráficos compostos
  dcChart1
    .useViewBoxResizing(true)
    .margins({top: 30, right: 65, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxT]))
    .rightY(d3.scaleLinear().domain([0, 1.1*maxU]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart1)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .yAxisLabel('Temperatura [°C]', 16)
    .rightYAxisLabel('Umidade [%]', 16)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value, 1);
    });
  dcChart2
    .useViewBoxResizing(true)
    .margins({top: 30, right: 65, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([0, 1.1*maxV]))
    .rightY(d3.scaleLinear().domain([0, 1.1*maxTime]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart2)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .yAxisLabel('Nível da Bateria [V]', 16)
    .rightYAxisLabel('Tempo [min]', 16)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value);
    });
  dcChart3
    .useViewBoxResizing(true)
    .margins({top: 30, right: 65, bottom: 30, left: 60})
    .dimension(timeDim)
    .x(d3.scaleTime().domain([minDate, maxDate]))
    .y(d3.scaleLinear().domain([1.1*minSNR, 1.1*maxSNR]))
    .rightY(d3.scaleLinear().domain([1.1*minRSSI, 1.1*maxRSSI]))
    .brushOn(false)
    .transitionDuration(500)
    .mouseZoomable(false)
    .rangeChart(dcRangeChart3)
    .renderHorizontalGridLines(true)
    .renderVerticalGridLines(true)
    .yAxisLabel('SNR', 16)
    .rightYAxisLabel('RSSI [dbi]', 16)
    .title(function(d) {
      return formatTime(d.key) + ':\n' + formatNumber(d.value);
    });

  //compôe todas as curvas nos gráficos compostos
  dcChart1.compose([dcChartT, dcChartU]);
  dcChart2.compose([dcChartV, dcChartTime]);
  dcChart3.compose([dcChartSNR, dcChartRSSI]);

  //cria uma dimensão para as tabelas
  var allDim = ndx.dimension(function(d) {return d;});

  //cria tabelas
  var dcTable1 = dc.dataTable(dcTableName1);
  var dcTable2 = dc.dataTable(dcTableName2);

  //define tabelas
  dcTable1
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);
  dcTable2
    .dimension(allDim)
    .group(function(d) {return '';})
    .showGroups(false)
    .sortBy(function (d) {return d.datetime_rx;})
    .order(d3.descending)
    .size(Infinity);

  //define as colunas que as tabelas devem exibir
  dcTable1
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return formatNumber(d.temp);},
      function(d) {return formatNumber(d.humid);},
      function(d) {return formatNumber(d.batl, 2);}
    ]);
  dcTable2
    .columns([
      function(d) {return formatTime(d.datetime_rx);},
      function(d) {return d.data_payload;},
      function(d) {return formatNumber(d.interval);},
      function(d) {return formatNumber(d.snr);},
      function(d) {return formatNumber(d.rssi);}
]);

  //variáveis para paginação da tabela
  var offset = 0;
  var recs = window.innerHeight/50;
  //render chart and table
  renderChartTable();
  //função para habilitar desabilitar botões
  function display() {
    d3.select('#id_next')
      .attr('disabled', (offset + recs) >= ndx.groupAll().reduceCount().value() ? 'true' : null);
    d3.select('#id_previous')
      .attr('disabled', offset <= 0 ? 'true' : null);
  }
  //função para atualizar paginação da tabela
  function update() {
    dcTable1.beginSlice(offset); dcTable2.beginSlice(offset);
    dcTable1.endSlice(offset + recs); dcTable2.endSlice(offset + recs);
    display();
  }
  //função para ir para a próxima página da tabela
  function next() {
    offset += recs;
    update();
    dcTable1.redraw(); dcTable2.redraw();
  }
  //função para ir para a página anterior da tabela
  function previous() {
    offset -= recs;
    if (offset < 0) offset = 0;
    update();
    dcTable1.redraw(); dcTable2.redraw();
  }
  //function to render chart and table
  function renderChartTable() {
    //define razão largura/altura para gráfico
    var ratio = 2.4;
    //define proporção de altura entre chart e rangeChart
    var prop = 0.1;
    //variáveis para altura e largura
    var height;
    var width;
    //redefine número de registros para paginação da tabela em função da altura
    recs = Math.round(window.innerHeight/50);
    //atualiza tabela
    update();
    //define propriedades dos gráficos
    width = document.getElementById('myChart1').clientWidth;
    if (document.getElementById('myChart2').clientWidth > width) {
      width = document.getElementById('myChart2').clientWidth;
    }
    if (document.getElementById('myChart3').clientWidth > width) {
      width = document.getElementById('myChart3').clientWidth;
    }
    height = Math.round(prop*width/ratio);
    height = (height >= 50) ? height : 50;
    dcRangeChart1.width(width); dcRangeChart2.width(width); dcRangeChart3.width(width);
    dcRangeChart1.height(height); dcRangeChart2.height(height); dcRangeChart3.height(height);
    dcRangeChart1.xAxis().ticks(Math.round(dcRangeChart1.width()/190));
    dcRangeChart2.xAxis().ticks(Math.round(dcRangeChart2.width()/190));
    dcRangeChart3.xAxis().ticks(Math.round(dcRangeChart3.width()/190));
    dcRangeChart1.yAxis().ticks(Math.round(dcRangeChart1.height()/130));
    dcRangeChart2.yAxis().ticks(Math.round(dcRangeChart2.height()/130));
    dcRangeChart3.yAxis().ticks(Math.round(dcRangeChart3.height()/130));
    height = Math.round(width/ratio) - dcRangeChart1.height();
    height = (height >= 200) ? height : 200;
    dcChart1.width(width); dcChart2.width(width); dcChart3.width(width);
    dcChart1.height(height); dcChart2.height(height); dcChart3.height(height);
    dcChartT.width(width);
    dcChartU.width(width);
    dcChartV.width(width);
    dcChartTime.width(width);
    dcChartT.height(height);
    dcChartU.height(height);
    dcChartV.height(height);
    dcChartTime.height(height);
    dcChartSNR.height(height);
    dcChartRSSI.height(height);
    dcChart1.xAxis().ticks(Math.round(dcChart1.width()/190));
    dcChart2.xAxis().ticks(Math.round(dcChart2.width()/190));
    dcChart3.xAxis().ticks(Math.round(dcChart3.width()/190));
    dcChart1.yAxis().ticks(Math.round(dcChart1.height()/130));
    dcChart2.yAxis().ticks(Math.round(dcChart2.height()/130));
    dcChart3.yAxis().ticks(Math.round(dcChart3.height()/130));
    dcChart1.legend(dc.legend().x(80).y(height - 65).itemHeight(13).gap(5).horizontal(false).legendWidth(140).itemWidth(70));
    dcChart2.legend(dc.legend().x(80).y(height - 65).itemHeight(13).gap(5).horizontal(false).legendWidth(140).itemWidth(70));
    dcChart3.legend(dc.legend().x(80).y(height - 65).itemHeight(13).gap(5).horizontal(false).legendWidth(140).itemWidth(70));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
  //adiciona evento onclick aos botões id_next e id_previous
  document.getElementById('id_next').addEventListener('click', next, false);
  document.getElementById('id_previous').addEventListener('click', previous, false);
}

//função para preencher gráfico de tarifas (branca e convencional)
function dcChartTariffs (valuesJson, dcChartName) {
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valores máximo e minimo da dimensão
//  var maxTariff = valuesJson.reduce(function(max, d) { return (d.white_peak > max) ? d.white_peak : max; }, 0);
  var maxTariff = 1.0,
      minTariff = 0.0;

  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.t;});

  //define os grupos de tarifas
  var whiteoffpeakGroup = timeDim.group().reduceSum(function(d) {return d.white_offpeak;}),
      whiteintermediateGroup = timeDim.group().reduceSum(function(d) {return d.white_intermediate;}),
      whitepeakGroup = timeDim.group().reduceSum(function(d) {return d.white_peak;}),
      conventionalGroup = timeDim.group().reduceSum(function(d) {return d.conventional;});

  //Função para habilitar/desabilitar os itens da legenda. Se o respectivo gráfico
  //está desabilitado, o item da legenda fica opaco.
  function drawLegendToggles(chart) {
    chart.selectAll('g.dc-legend .dc-legend-item')
      .style('opacity', function(d, i) {
          var indexChart = i;
          var subchart = chart.select('g.sub._' + indexChart);
          var visible = subchart.style('visibility') !== 'hidden';
            return visible ? 1 : 0.2;
       });
  }
  //função para habilitar/desabilitar a visualização de um gráfico
  function legendToggle(chart) {
        chart.selectAll('g.dc-legend .dc-legend-item')
        .on('click.hideshow', function(d, i) {
          var subchart = chart.select('g.sub._' + i);
          var visible = subchart.style('visibility') !== 'hidden';
          subchart.style('visibility', function() {
                return visible ? 'hidden' : 'visible';});
          drawLegendToggles(chart);
        })
      drawLegendToggles(chart);
  }
  //define limites do eixo horizontal (patamares de 0 a 23)
  var minHour = timeDim.bottom(1)[0]['t'];
  var maxHour =  timeDim.top(1)[0]['t'] + 1;
  //largura das barras do gráfico
  var x_units = 40;

  //montagem do gráfico composto
  var lineChartConventional, barChartWhiteOffpeak, barChartWhitePeak, barChartWhiteIntermediate;
  var dcChart = dc.compositeChart(dcChartName);
    dcChart
    .transitionDuration(200)
    .margins({top: 5, right: 80, bottom: 25, left: 50})
    .x(d3.scaleLinear().domain([minHour, maxHour]))
    .xUnits(function(){return x_units;})
    .y(d3.scaleLinear().domain([minTariff, 1.05*maxTariff]))
    .brushOn(false)
    .yAxisLabel('Tarifa [R$/kWh]', 16)
    .dimension(timeDim)
    .renderHorizontalGridLines(true)
    .compose([
            barChartWhiteOffpeak = new dc.barChart(dcChart).centerBar(false).colors('gray').group(whiteoffpeakGroup, 'Tarifa Branca - Fora Ponta').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            barChartWhitePeak = new dc.barChart(dcChart).centerBar(false).colors('red').group(whitepeakGroup, 'Tarifa Branca - Ponta').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            barChartWhiteIntermediate = new dc.barChart(dcChart).centerBar(false).colors('orange').group(whiteintermediateGroup, 'Tarifa Branca - Intermediário').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            lineChartConventional = new dc.lineChart(dcChart).colors('black').dashStyle([2,3]).group(conventionalGroup, 'Tarifa Convencional').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
        ])
    .on('pretransition.hideshow', legendToggle)
    .legend(dc.legend().x(0).y(10).itemHeight(13).gap(5));

  //comandos para remover da legenda as curvas auxiliares (mínimos e máximos)
  //lineChartVaMax.legendables = function() { return [];};
  //lineChartVaMin.legendables = function() { return [];};
  //lineChartVbMax.legendables = function() { return [];};
  //lineChartVbMin.legendables = function() { return [];};
  //lineChartVcMax.legendables = function() { return [];};
  //lineChartVcMin.legendables = function() { return [];};
  //lineChartVlim1Lower.legendables = function() { return [];};
  //lineChartVlim2Lower.legendables = function() { return [];};

  //renderiza gráfico
  dcChart.render();
  renderChartTariffs();

  function renderChartTariffs()
  {
    //altura, largura e razão largura/altura
    var height, width, ratio = 2.4;
    //define propriedades dos gráficos
    width = document.getElementById('myChart1').clientWidth;
    height = Math.round(width / ratio);
    dcChart.width(width);
    dcChart.height(height);
    dcChart.xAxis().tickValues([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]).tickFormat(function (v) {return v + 'h';});
    dcChart.legend(dc.legend().x(80).y(30).itemHeight(7).gap(7).horizontal(false).legendWidth(140).itemWidth(70));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTariffs();};
}

//função para preencher gráfico de consumos horários diário
function dcChartConsumptionDaily (valuesJson, dcChartName) {
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valores máximo e minimo da dimensão
  var maxKW = valuesJson.reduce(function(max, d) { return (d.highlight_peak > max) ? d.highlight_peak : max; }, 0);
  var minKW = 0;

  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.t;});

  //define os grupos de consumo
  var highlightintermediateGroup = timeDim.group().reduceSum(function(d) {return d.highlight_interm;}),
      highlightpeakGroup = timeDim.group().reduceSum(function(d) {return d.highlight_peak;}),
      kwdailyGroup = timeDim.group().reduceSum(function(d) {return d.kw_tot;});

  //Função para habilitar/desabilitar os itens da legenda. Se o respectivo gráfico
  //está desabilitado, o item da legenda fica opaco.
  function drawLegendToggles(chart) {
    chart.selectAll('g.dc-legend .dc-legend-item')
      .style('opacity', function(d, i) {
          var indexChart = i;
          var subchart = chart.select('g.sub._' + indexChart);
          var visible = subchart.style('visibility') !== 'hidden';
            return visible ? 1 : 0.2;
       });
  }
  //função para habilitar/desabilitar a visualização de um gráfico
  function legendToggle(chart) {
        chart.selectAll('g.dc-legend .dc-legend-item')
        .on('click.hideshow', function(d, i) {
          var subchart = chart.select('g.sub._' + i);
          var visible = subchart.style('visibility') !== 'hidden';
          subchart.style('visibility', function() {
                return visible ? 'hidden' : 'visible';});
          drawLegendToggles(chart);
        })
      drawLegendToggles(chart);
  }
  //define limites do eixo horizontal (patamares de 0 a 23)
  var minHour = timeDim.bottom(1)[0]['t'];
  var maxHour =  timeDim.top(1)[0]['t'] + 1;
  var x_units = 1.3;

  //montagem do gráfico composto
  var barChartHighlightInterm, barChartHighlightPeak, lineChartKWdaily;
  var dcChart = dc.compositeChart(dcChartName);
    dcChart
    .transitionDuration(200)
    .margins({top: 5, right: 80, bottom: 25, left: 50})
    .x(d3.scaleLinear().domain([minHour, maxHour]))
    .xUnits(function(){return x_units;})
    .y(d3.scaleLinear().domain([minKW, 1.05*maxKW]))
    .brushOn(false)
    .yAxisLabel('Consumo [kW]', 16)
    .dimension(timeDim)
    .renderHorizontalGridLines(true)
    .compose([
            barChartHighlightInterm = new dc.barChart(dcChart).centerBar(true).colors('#B0C4DE').group(highlightintermediateGroup, 'Intermediário').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            barChartHighlightPeak = new dc.barChart(dcChart).centerBar(true).colors('#FFA07A').group(highlightpeakGroup, 'Ponta').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            lineChartKWdaily = new dc.lineChart(dcChart).colors('blue').group(kwdailyGroup, 'Consumo').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
        ])
    .on('pretransition.hideshow', legendToggle)
    .legend(dc.legend().x(0).y(10).itemHeight(13).gap(5));

  //comandos para remover da legenda as curvas auxiliares (mínimos e máximos)
  //lineChartVaMax.legendables = function() { return [];};
  //lineChartVaMin.legendables = function() { return [];};
  //lineChartVbMax.legendables = function() { return [];};
  //lineChartVbMin.legendables = function() { return [];};
  //lineChartVcMax.legendables = function() { return [];};
  //lineChartVcMin.legendables = function() { return [];};
  //lineChartVlim1Lower.legendables = function() { return [];};
  //lineChartVlim2Lower.legendables = function() { return [];};

  //renderiza gráfico
  dcChart.render();
  renderChartTariffs();

  function renderChartTariffs()
  {
    //altura, largura e razão largura/altura
    var height, width, ratio = 2.6;
    //define propriedades dos gráficos
    width = Math.round(document.getElementById('myChart1').clientWidth);
    height = Math.round(width / ratio);
    dcChart.width(width);
    dcChart.height(height);
    dcChart.xAxis().tickValues([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]).tickFormat(function (v) {return v + 'h';});
    dcChart.legend(dc.legend().x(80).y(30).itemHeight(7).gap(7).horizontal(false).legendWidth(140).itemWidth(70));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTariffs();};
}

//função para preencher gráfico de consumo típico
function dcChartTypicalConsumption (valuesJson, dcChartName) {
  //proteção contra objetos com menos de 2 registros
  if (valuesJson.length < 2) return;
  //determina valores máximo e minimo da dimensão
  var maxKW = valuesJson.reduce(function(max, d) { return (d.highlight_peak > max) ? d.highlight_peak : max; }, 0);
  var minKW = 0;

  //cria instância do crossfilter
  var ndx = crossfilter(valuesJson);
  //define uma dimensão (o que vai no eixo x)
  var timeDim = ndx.dimension(function(d) {return d.t;});

  //define os grupos de consumo
  var highlightintermediateGroup = timeDim.group().reduceSum(function(d) {return d.highlight_interm;}),
      highlightpeakGroup = timeDim.group().reduceSum(function(d) {return d.highlight_peak;}),
      kwdailyGroup = timeDim.group().reduceSum(function(d) {return d.kw_tot;});

  //Função para habilitar/desabilitar os itens da legenda. Se o respectivo gráfico
  //está desabilitado, o item da legenda fica opaco.
  function drawLegendToggles(chart) {
    chart.selectAll('g.dc-legend .dc-legend-item')
      .style('opacity', function(d, i) {
          var indexChart = i;
          var subchart = chart.select('g.sub._' + indexChart);
          var visible = subchart.style('visibility') !== 'hidden';
            return visible ? 1 : 0.2;
       });
  }
  //função para habilitar/desabilitar a visualização de um gráfico
  function legendToggle(chart) {
        chart.selectAll('g.dc-legend .dc-legend-item')
        .on('click.hideshow', function(d, i) {
          var subchart = chart.select('g.sub._' + i);
          var visible = subchart.style('visibility') !== 'hidden';
          subchart.style('visibility', function() {
                return visible ? 'hidden' : 'visible';});
          drawLegendToggles(chart);
        })
      drawLegendToggles(chart);
  }
  //define limites do eixo horizontal (patamares de 0 a 23)
  var minHour = timeDim.bottom(1)[0]['t'];
  var maxHour =  timeDim.top(1)[0]['t'] + 1;
  var x_units = 1.3;

  //montagem do gráfico composto
  var barChartHighlightInterm, barChartHighlightPeak, lineChartKWdaily;
  var dcChart = dc.compositeChart(dcChartName);
    dcChart
    .transitionDuration(200)
    .margins({top: 5, right: 80, bottom: 25, left: 50})
    .x(d3.scaleLinear().domain([minHour, maxHour]))
    .xUnits(function(){return x_units;})
    .y(d3.scaleLinear().domain([minKW, 1.05*maxKW]))
    .brushOn(false)
    .yAxisLabel('Consumo [kW]', 16)
    .dimension(timeDim)
    .renderHorizontalGridLines(true)
    .compose([
            barChartHighlightInterm = new dc.barChart(dcChart).centerBar(true).colors('#B0C4DE').group(highlightintermediateGroup, 'Intermediário').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            barChartHighlightPeak = new dc.barChart(dcChart).centerBar(true).colors('#FFA07A').group(highlightpeakGroup, 'Ponta').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
            ,
            lineChartKWdaily = new dc.lineChart(dcChart).colors('blue').group(kwdailyGroup, 'Consumo').title(function (d) {
                return "Bar key: " + d.key + "\nBar value: " + d.value;
            }).valueAccessor(function (d) {
                return d.value;
            })
        ])
    .on('pretransition.hideshow', legendToggle)
    .legend(dc.legend().x(0).y(10).itemHeight(13).gap(5));

  //comandos para remover da legenda as curvas auxiliares (mínimos e máximos)
  //lineChartVaMax.legendables = function() { return [];};
  //lineChartVaMin.legendables = function() { return [];};
  //lineChartVbMax.legendables = function() { return [];};
  //lineChartVbMin.legendables = function() { return [];};
  //lineChartVcMax.legendables = function() { return [];};
  //lineChartVcMin.legendables = function() { return [];};
  //lineChartVlim1Lower.legendables = function() { return [];};
  //lineChartVlim2Lower.legendables = function() { return [];};

  //renderiza gráfico
  dcChart.render();
  renderChartTariffs();

  function renderChartTariffs()
  {
    //altura, largura e razão largura/altura
    var height, width, ratio = 3.0;
    //define propriedades dos gráficos
    width = document.getElementById('myChart1').clientWidth;
    height = Math.round(width / ratio);
    dcChart.width(width);
    dcChart.height(height);
    dcChart.xAxis().tickValues([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]).tickFormat(function (v) {return v + 'h';});
    dcChart.legend(dc.legend().x(80).y(30).itemHeight(7).gap(7).horizontal(false).legendWidth(140).itemWidth(70));
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTariffs();};
}

// função para montagem das tabelas e dos gráficos para comparação tarifa branca x convencional (sem bandeiras)
function dcChartTableComparison1(valuesJson_white, valuesJson_coventional, valuesJson_comparison_kwh, dcTableName1, dcTableName2, dcChart)
{
  //cria crossfilter e dimensão para tabela 1
  var ndx1 = crossfilter(valuesJson_white);
  var dim_table1 = ndx1.dimension(function(d) {return d;});

  //cria crossfilter e dimensão para tabela 2
  var ndx2 = crossfilter(valuesJson_coventional);
  var dim_table2 = ndx2.dimension(function(d) {return d;});

  //cria crossfilter e dimensão para gráfico de consumos totais
  var ndx3 = crossfilter(valuesJson_comparison_kwh);
  var dim_chart = ndx3.dimension(function(d) {return d.period;});
  var kwhGroup = dim_chart.group().reduceSum(function(d) {return d.value;});

  //cria tabelas
  var dcTable1 = dc.dataTable(dcTableName1);
  var dcTable2 = dc.dataTable(dcTableName2);

  //define tabela2
  dcTable1
    .dimension(dim_table1)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable2
    .dimension(dim_table2)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);

  //define as colunas que as tabelas devem exibir
  dcTable1
    .columns([
      function(d) {return d.description;},
      function(d) {return formatNumber(d.kwh);},
      function(d) {return formatNumber(d.tariff);},
      function(d) {return formatNumber(d.cost_energy);},
      function(d) {return formatNumber(d.icms);},
      function(d) {return formatNumber(d.cost_icms);},
      function(d) {return formatNumber(d.total);}
    ]);
  dcTable2
    .columns([
      function(d) {return d.description;},
      function(d) {return formatNumber(d.kwh);},
      function(d) {return formatNumber(d.tariff);},
      function(d) {return formatNumber(d.cost_energy);},
      function(d) {return formatNumber(d.icms);},
      function(d) {return formatNumber(d.cost_icms);},
      function(d) {return formatNumber(d.total);}
    ]);

  var chartKWH = new dc.pieChart(dcChart);
  chartKWH
    .width(450)
    .height(250)
    .slicesCap(4)
    .innerRadius(10)
    .radius(100)
    .dimension(dim_chart)
    .group(kwhGroup)
    .legend(dc.legend().x(0).y(20));

    chartKWH.on('pretransition', function(chart) {
      chart.selectAll('.dc-legend-item text')
          .text('')
        .append('tspan')
          .text(function(d) { return d.name; })
        .append('tspan')
          .attr('x', 100)
          .attr('text-anchor', 'end')
          .append('tspan')
          .text(function(d) { return d.data; })});

//  chartKWH.colors(d3.scaleOrdinal().range(['red','green','blue']));

  chartKWH.render();

  //render chart and table
  renderChartTable();

  //function to render chart and table
  function renderChartTable() {
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
}

// função para montagem das tabelas e dos gráficos para comparação tarifa branca x convencional (com bandeiras)
function dcChartTableComparison2(valuesJson_white, valuesJson_conv, dcTableName1, dcTableName2, dcTableName3, dcTableName4,
                                 dcTableName5, dcTableName6, dcTableName7, dcTableName8, dcTableName9, dcTableName10)
{
  //cria crossfilter e dimensão para dados de tarifa branca
  var ndx1 = crossfilter(valuesJson_white);
  var dim_white = ndx1.dimension(function(d) {return d;});

  //cria crossfilter e dimensão para dados de tarifa convencional
  var ndx2 = crossfilter(valuesJson_conv);
  var dim_conv = ndx2.dimension(function(d) {return d;});

  //cria tabelas
  var dcTable1  = dc.dataTable(dcTableName1);   // verde
  var dcTable2  = dc.dataTable(dcTableName2);
  var dcTable3  = dc.dataTable(dcTableName3);   // amarela
  var dcTable4  = dc.dataTable(dcTableName4);
  var dcTable5  = dc.dataTable(dcTableName5);   // vermelha patamar I
  var dcTable6  = dc.dataTable(dcTableName6);
  var dcTable7  = dc.dataTable(dcTableName7);   // vermelha patamar II
  var dcTable8  = dc.dataTable(dcTableName8);
  var dcTable9  = dc.dataTable(dcTableName9);   // escassez hídrica
  var dcTable10 = dc.dataTable(dcTableName10);

  //define tabela2
  dcTable1
    .dimension(dim_white)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable2
    .dimension(dim_conv)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable3
    .dimension(dim_white)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable4
    .dimension(dim_conv)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable5
    .dimension(dim_white)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable6
    .dimension(dim_conv)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable7
    .dimension(dim_white)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable8
    .dimension(dim_conv)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable9
    .dimension(dim_white)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);
  dcTable10
    .dimension(dim_conv)
    .group(function(d) {return '';})
    .showGroups(false)
    .size(Infinity);

  //define as colunas das tabelas (branca e convencional) para bandeira verde
  dcTable1
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_green;}
    ]);
  dcTable2
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_green;}
    ]);
  //define as colunas das tabelas (branca e convencional) para bandeira amarela
  dcTable3
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_yellow;}
    ]);
  dcTable4
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_yellow;}
    ]);
  //define as colunas das tabelas (branca e convencional) para bandeira vermelha patamar I
  dcTable5
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_red1;}
    ]);
  dcTable6
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_red1;}
    ]);
  //define as colunas das tabelas (branca e convencional) para bandeira vermelha patamar II
  dcTable7
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_red2;}
    ]);
  dcTable8
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_red2;}
    ]);
  //define as colunas das tabelas (branca e convencional) para bandeira escassez hídrica
  dcTable9
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_ws;}
    ]);
  dcTable10
    .columns([
      function(d) {return d.description;},
      function(d) {return d.total_ws;}
    ]);

  //render chart and table
  renderChartTable();

  //function to render chart and table
  function renderChartTable() {
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderChartTable();};
}

// função para preencher gráficos de barras comparando tarifa convencional x branca
function dcChartTableComparison2_barCharts(valuesJson, dcChartName1, dcChartName2, dcChartName3, dcChartName4, dcChartName5)
{
  //cria crossfilter e dimensão para dados de tarifa branca
  var ndx = crossfilter(valuesJson);
  var tariffDim = ndx.dimension(function(d) {return d.tariff;});

  //define os grupos (o que vai no eixo y)
  var greenGroup = tariffDim.group().reduceSum(function(d) {return d.cost_green;});
  var yellowGroup = tariffDim.group().reduceSum(function(d) {return d.cost_yellow;});
  var red1Group = tariffDim.group().reduceSum(function(d) {return d.cost_red1;});
  var red2Group = tariffDim.group().reduceSum(function(d) {return d.cost_red2;});
  var wsGroup = tariffDim.group().reduceSum(function(d) {return d.cost_ws;});

  //define valores máximos
  var maxGreen = valuesJson.reduce(function(max, d) { return (d.cost_green > max) ? d.cost_green : max; }, 0);
  var maxYellow = valuesJson.reduce(function(max, d) { return (d.cost_yellow > max) ? d.cost_yellow : max; }, 0);
  var maxRed1 = valuesJson.reduce(function(max, d) { return (d.cost_red1 > max) ? d.cost_red1 : max; }, 0);
  var maxRed2 = valuesJson.reduce(function(max, d) { return (d.cost_red2 > max) ? d.cost_red2 : max; }, 0);
  var maxWs = valuesJson.reduce(function(max, d) { return (d.cost_ws > max) ? d.cost_ws : max; }, 0);
  var maxValue = maxGreen;
  if(maxYellow > maxValue) {maxValue = maxYellow;}
  if(maxRed1 > maxValue) {maxValue = maxRed1;}
  if(maxRed2 > maxValue) {maxValue = maxRed2;}
  if(maxWs > maxValue) {maxValue = maxWs;}

  var dcChartGreen = dc.barChart(dcChartName1);
  var dcChartYellow = dc.barChart(dcChartName2);
  var dcChartRed1 = dc.barChart(dcChartName3);
  var dcChartRed2 = dc.barChart(dcChartName4);
  var dcChartWs = dc.barChart(dcChartName5);
  dcChartGreen
    .width(120)
    .height(200)
    .colors('green')
    .x(d3.scaleBand())
    .y(d3.scaleLinear().domain([0.0, 1.2 * maxValue]))
    .xUnits(dc.units.ordinal)
    .yAxisLabel('Custo [R$]', 15)
    .brushOn(false)
    .barPadding(0.5)
    .dimension(tariffDim)
    .group(greenGroup)
    .renderLabel(true)
    .on('pretransition', function(chart) {
        chart.select('.axis.x')
             .attr("text-anchor", "end")
             .selectAll("text")
             .attr("transform", "rotate(-45)")
             .attr("dy", "-0.7em")
             .attr("dx", "-1em");
        });

  dcChartYellow
    .width(120)
    .height(200)
    .colors('yellow')
    .x(d3.scaleBand())
    .y(d3.scaleLinear().domain([0.0, 1.2 * maxValue]))
    .xUnits(dc.units.ordinal)
    .yAxisLabel('Custo [R$]', 15)
    .brushOn(false)
    .barPadding(0.5)
    .dimension(tariffDim)
    .group(yellowGroup)
    .renderLabel(true)
    .on('pretransition', function(chart) {
        chart.select('.axis.x')
             .attr("text-anchor", "end")
             .selectAll("text")
             .attr("transform", "rotate(-45)")
             .attr("dy", "-0.7em")
             .attr("dx", "-1em");
        });

  dcChartRed1
    .width(120)
    .height(200)
    .colors('red')
    .x(d3.scaleBand())
    .y(d3.scaleLinear().domain([0.0, 1.2 * maxValue]))
    .xUnits(dc.units.ordinal)
    .yAxisLabel('Custo [R$]', 15)
    .brushOn(false)
    .barPadding(0.5)
    .dimension(tariffDim)
    .group(red1Group)
    .renderLabel(true)
    .on('pretransition', function(chart) {
        chart.select('.axis.x')
             .attr("text-anchor", "end")
             .selectAll("text")
             .attr("transform", "rotate(-45)")
             .attr("dy", "-0.7em")
             .attr("dx", "-1em");
        });

  dcChartRed2
    .width(120)
    .height(200)
    .colors('red')
    .x(d3.scaleBand())
    .y(d3.scaleLinear().domain([0.0, 1.2 * maxValue]))
    .xUnits(dc.units.ordinal)
    .yAxisLabel('Custo [R$]', 15)
    .brushOn(false)
    .barPadding(0.5)
    .dimension(tariffDim)
    .group(red2Group)
    .renderLabel(true)
    .on('pretransition', function(chart) {
        chart.select('.axis.x')
             .attr("text-anchor", "end")
             .selectAll("text")
             .attr("transform", "rotate(-45)")
             .attr("dy", "-0.7em")
             .attr("dx", "-1em");
        });

  dcChartWs
    .width(120)
    .height(200)
    .colors('#4B0082')
    .x(d3.scaleBand())
    .y(d3.scaleLinear().domain([0.0, 1.2 * maxValue]))
    .xUnits(dc.units.ordinal)
    .yAxisLabel('Custo [R$]', 15)
    .brushOn(false)
    .barPadding(0.5)
    .dimension(tariffDim)
    .group(wsGroup)
    .renderLabel(true)
    .on('pretransition', function(chart) {
        chart.select('.axis.x')
             .attr("text-anchor", "end")
             .selectAll("text")
             .attr("transform", "rotate(-45)")
             .attr("dy", "-0.7em")
             .attr("dx", "-1em");
        });

  //renderiza gráficos
  dcChartGreen.render(); dcChartYellow.render(); dcChartRed1.render(); dcChartRed2.render(); dcChartWs.render();

  renderCharts();
  function renderCharts()
  {
    //altura, largura e razão largura/altura
    var height, width, ratio = 2;
    //define propriedades dos gráficos
    width = Math.round(document.getElementById('myChart5').clientWidth);
    height = Math.round(width / ratio);

    dcChartGreen.yAxis().tickFormat(function(v) { return ""; });
    dcChartGreen.yAxis().ticks(0);
    dcChartYellow.yAxis().tickFormat(function(v) { return ""; });
    dcChartYellow.yAxis().ticks(0);
    dcChartRed1.yAxis().tickFormat(function(v) { return ""; });
    dcChartRed1.yAxis().ticks(0);
    dcChartRed2.yAxis().tickFormat(function(v) { return ""; });
    dcChartRed2.yAxis().ticks(0);
    dcChartWs.yAxis().tickFormat(function(v) { return ""; });
    dcChartWs.yAxis().ticks(0);

    dcChartGreen.margins().left = 20;
    dcChartGreen.margins().right = 0;
    dcChartGreen.margins().bottom = 70;
    dcChartYellow.margins().left = 20;
    dcChartYellow.margins().right = 0;
    dcChartYellow.margins().bottom = 70;
    dcChartRed1.margins().left = 20;
    dcChartRed1.margins().right = 0;
    dcChartRed1.margins().bottom = 70;
    dcChartRed2.margins().left = 20;
    dcChartRed2.margins().right = 0;
    dcChartRed2.margins().bottom = 70;
    dcChartWs.margins().left = 20;
    dcChartWs.margins().right = 0;
    dcChartWs.margins().bottom = 70;

    //dcChartGreen.width(100);
    //dcChartGreen.height(50);
    dc.renderAll();
  }
  //render the chart again after onresize event
  document.getElementsByTagName('BODY')[0].onresize = function() {renderCharts();};
}