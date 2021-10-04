import datetime
from datetime import datetime
from .models import TariffFlag, Tariff, TaxIcms, TaxPisCofins


"""
Função para formatar string de valor monetário
"""
def CurrencyFormatBrazil(value_ini):
    value = "R$ {:,.2f}".format(value_ini)
    main_currency, fractional_currency = value.split(".")[0], value.split(".")[1]
    new_main_currency = main_currency.replace(",", ".")
    value = new_main_currency + ',' + fractional_currency
    return value


"""
Função para decidir se o dado pode ser utilizado para a curva típica de consumo
"""
def ConsiderData(v, days_consider, seasons_consider):
    dt1, dt2, dt3 = {'month': 1, 'day': 1}, {'month': 3, 'day': 21}, {'month': 6, 'day': 21}
    dt4, dt5 = {'month': 9, 'day': 23}, {'month': 12, 'day': 21}
    filter_week_day = v[0].weekday() in days_consider
    d1 = datetime(v[0].year, dt1['month'], dt1['day'])
    d2 = datetime(v[0].year, dt2['month'], dt2['day'])
    d3 = datetime(v[0].year, dt3['month'], dt3['day'])
    d4 = datetime(v[0].year, dt4['month'], dt4['day'])
    d5 = datetime(v[0].year, dt5['month'], dt5['day'])
    filter1 = d1 <= v[0] < d2 and 1 in seasons_consider  # verão
    filter2 = d2 <= v[0] < d3 and 2 in seasons_consider  # outono
    filter3 = d3 <= v[0] < d4 and 3 in seasons_consider  # inverno
    filter4 = d4 <= v[0] < d5 and 4 in seasons_consider  # primavera
    filter5 = d5 <= v[0] and 1 in seasons_consider  # verão
    filter_season = filter1 or filter2 or filter3 or filter4 or filter5
    return filter_week_day and filter_season


"""
Função para definir os estados dos checkboxes relativos aos dias da semana 
e as estações do ano a serem considerados, em função do filtro do usuário
"""
def DaysSeasonsConsider(days_consider, seasons_consider):
    # dias da semana a serem marcados/desmarcados
    ck2af = 1 if 0 in days_consider else 0
    ck3af = 1 if 1 in days_consider else 0
    ck4af = 1 if 2 in days_consider else 0
    ck5af = 1 if 3 in days_consider else 0
    ck6af = 1 if 4 in days_consider else 0
    ckSab = 1 if 5 in days_consider else 0
    ckDom = 1 if 6 in days_consider else 0
    json_days_filter = {'ck2af': ck2af, 'ck3af': ck3af, 'ck4af': ck4af, 'ck5af': ck5af, 'ck6af': ck6af, 'ckSab': ckSab,
                        'ckDom': ckDom}
    # estações do ano a serem marcadas/desmarcadas
    ckSummer = 1 if 1 in seasons_consider else 0
    ckFall = 1 if 2 in seasons_consider else 0
    ckWinter = 1 if 3 in seasons_consider else 0
    ckSpring = 1 if 4 in seasons_consider else 0
    json_seasons_filter = {'ckSummer': ckSummer, 'ckFall': ckFall, 'ckWinter': ckWinter, 'ckSpring': ckSpring}
    return json_days_filter, json_seasons_filter


"""
Função para mapear nome da bandeira e valor da bandeira
"""
def flag_value(flag_name, flag_tariffs):
    if flag_name == 'VD': value = flag_tariffs[0]
    elif flag_name == 'AM': value = flag_tariffs[1]
    elif flag_name == 'V1': value = flag_tariffs[2]
    elif flag_name == 'V2': value = flag_tariffs[3]
    else: value = flag_tariffs[4]
    return value


"""
Função para cálculo do valor da fatura considerando Tarifa Branca
"""
def BillWhiteTariff(data_list_energy_hour, flag_name = None):
    # DADO EXTERNO: valores de tarifa branca por patamar
    hourly_white_tariffs = [0.43664, 0.61737, 0.96013]

    # DADO EXTERNO: valor de ICMS(%)
    icms = 12.0

    # DADO EXTERNO - matriz de bandeiras tarifárias, com a seguinte formatação:
    # bandeira, valor (R$/kWh sem impostos)
    # 0: verde, 1: amarela, 2: vermelha pat. 1, 3: vermelha pat. 2, 4: escassez hídrica
    flag_tariffs = [0.0, 0.01874, 0.03971, 0.09492, 0.1420]

    # calcula os consumos de energia (kWh) por patamar horário
    kwh_offpeak, kwh_intermediate, kwh_peak = 0.0, 0.0, 0.0
    for i in range(1, len(data_list_energy_hour)):
        val_prev = data_list_energy_hour[i - 1]
        val = data_list_energy_hour[i]
        kwh = (val[1] + val[2] + val[3] + val[4]) - (val_prev[1] + val_prev[2] + val_prev[3] + val_prev[4])
        if 0 <= val[0].hour < 17:
            kwh_offpeak += kwh
        elif 17 <= val[0].hour < 18 or 22 <= val[0].hour < 23:
            kwh_intermediate += kwh
        elif 18 <= val[0].hour < 22:
            kwh_peak += kwh
        else:
            kwh_offpeak += kwh

    # calcula os custos finais devido às bandeiras
    if flag_name is not None:
        flag_kwh = flag_value(flag_name, flag_tariffs)
        flag_cost_offpeak = kwh_offpeak * flag_kwh / (1 - icms / 100.)
        flag_cost_intermediate = kwh_intermediate * flag_kwh / (1 - icms / 100.)
        flag_cost_peak = kwh_peak * flag_kwh / (1 - icms / 100.)
    else:
        flag_cost_offpeak, flag_cost_intermediate, flag_cost_peak = 0.0, 0.0, 0.0

    # calcula os custos de energia apenas
    cost_offpeak = round(kwh_offpeak * hourly_white_tariffs[0], 2)
    cost_intermediate = round(kwh_intermediate * hourly_white_tariffs[1], 2)
    cost_peak = round(kwh_peak * hourly_white_tariffs[2], 2)

    # corrige as tarifas com o ICMS
    tariff_offpeak = hourly_white_tariffs[0] / (1.0 - icms/100.)
    tariff_intermediate = hourly_white_tariffs[1] / (1.0 - icms / 100.)
    tariff_peak = hourly_white_tariffs[2] / (1.0 - icms / 100.)

    # custos finais
    final_cost_offpeak = round(kwh_offpeak * tariff_offpeak + flag_cost_offpeak, 2)
    final_cost_intermediate = round(kwh_intermediate * tariff_intermediate + flag_cost_intermediate, 2)
    final_cost_peak = round(kwh_peak * tariff_peak + flag_cost_peak, 2)

    # custos icms
    icms_offpeak = round(final_cost_offpeak - cost_offpeak, 2)
    icms_intermediate = round(final_cost_intermediate - cost_intermediate, 2)
    icms_peak = round(final_cost_peak - cost_peak, 2)

    final_cost = round(final_cost_offpeak + final_cost_intermediate + final_cost_peak, 2)

    # monta a estrutura de saída
    white_costs = [['Fora Ponta', round(kwh_offpeak, 2), hourly_white_tariffs[0], cost_offpeak, icms, icms_offpeak, final_cost_offpeak],
                   ['Intermediário', round(kwh_intermediate, 2), hourly_white_tariffs[1], cost_intermediate, icms, icms_intermediate, final_cost_intermediate],
                   ['Ponta', round(kwh_peak, 2), hourly_white_tariffs[2], cost_peak, icms, icms_peak, final_cost_peak],
                   ['Total', 0.0, 0.0, 0.0, 0.0, 0.0, final_cost]]

    return white_costs


"""
Função para cálculo do valor da fatura considerando Tarifa Convencional
- data_list_energy_proj: lista com os valores de consumo
- customer_type: tipo/classe do consumidor (B1_1, B1_2, ..., B2_1, B2_2, ...
- use_valid_flags: usar (ou não) as bandeiras vigentes
- simulated_flag: id da bandeira, começando em 0 (verde), 1 (amarela), ...
"""
def BillConventionalTariff(data_list_energy_proj, customer_type, use_valid_flags, simulated_flag = 0):

    # Recupera do banco os dados históricos de bandeira, identificando
    # os valores mais recentes de cada bandeira
    flag_tariffs_dict = [{'type': i+1, 'dt_ini': None, 'value': 0.0} for i in range(5)]
    allTariffFlags = TariffFlag.objects.all()
    tf: TariffFlag
    for tf in allTariffFlags:
        dt = datetime(tf.year, tf.month, 1, 0, 0, 0)
        if flag_tariffs_dict[tf.type_id - 1]['dt_ini'] is None:
            flag_tariffs_dict[tf.type_id - 1]['dt_ini'] = dt
            flag_tariffs_dict[tf.type_id - 1]['value'] = float(tf.value)
        elif dt > flag_tariffs_dict[tf.type_id - 1]['dt_ini'] and float(tf.value) > flag_tariffs_dict[tf.type_id - 1]['value']:
            flag_tariffs_dict[tf.type_id - 1]['dt_ini'] = dt
            flag_tariffs_dict[tf.type_id - 1]['value'] = float(tf.value)

    # Valores das bandeiras tarifárias, na seguinte sequência:
    # 0: verde, 1: amarela, 2: vermelha pat. 1, 3: vermelha pat. 2, 4: escassez hídrica
    flag_tariffs = [flag_tariffs_dict[i]['value'] for i in range(5)]


    # Recupera dados da tarifa. Cada item da lista tariff_matrix é um dict, como no exemplo:
    # {'subgrupo': 'B1', 'tarifas': [0.53224, 0.16121, 0.27636, 0.41454, 0.4606]}
    allTariffs = Tariff.objects.all()
    tariff_matrix = []
    for t in allTariffs:
        v = next((item for item in tariff_matrix if item["subgrupo"] == t.subgroup), None)
        if v:
            if t.classif_id < len(v['tarifas']):
                v['tarifas'][t.classif_id - 1] = float(t.value)
            else:
                diff = t.classif_id - len(v['tarifas'])
                for i in range(diff):
                    if i < diff - 1:
                        v['tarifas'].append(0.0)
                    else:
                        v['tarifas'].append(float(t.value))
        else:
            v = {'subgrupo': t.subgroup, 'tarifas': []}
            for i in range(t.classif_id):
                if i < t.classif_id - 1:
                    v['tarifas'].append(0.0)
                else:
                    v['tarifas'].append(float(t.value))
            tariff_matrix.append(v)

    # Recupera do banco os dados relativos a PIS, COFINS e ICMS. Cada item tem o formato:
    # ano, mês, PIS(%), COFINS(%), ICMS_res1(%), ICMS_res2(%), ICMS_rur1(%), ICMS_rur2(%), ICMS_out(%)
    allPisCofins = TaxPisCofins.objects.all()
    allIcms = TaxIcms.objects.all()
    pis_cofins_icms = []
    for pc in allPisCofins:
        v = next((item for item in pis_cofins_icms if item[0] == pc.year and item[1] == pc.month), None)
        pis, cofins = float(pc.value_pis), float(pc.value_cofins)
        if v:
            v[2], v[3] = pis, cofins
        else:
            v = [pc.year, pc.month, pis, cofins] + [0.0 for i in range(5)]
            pis_cofins_icms.append(v)
    for icms_db in allIcms:
        v = next((item for item in pis_cofins_icms if item[0] == icms_db.year and item[1] == icms_db.month), None)
        res1, res2 = float(icms_db.valueRes1), float(icms_db.valueRes2)
        rur1, rur2, oth = float(icms_db.valueRur1), float(icms_db.valueRur2), float(icms_db.valueOther)
        if v:
            v[4], v[5], v[6], v[7], v[8] = res1, res2, rur1, rur2, oth
        else:
            v = [icms_db.year, icms_db.month, 0.0, 0.0] + [res1, res2, rur1, rur2, oth]
            pis_cofins_icms.append(v)

    # determina tarifas sem imposto (R$/kWh)
    subgroup, subsubgroup = customer_type.split('_')[0].upper(), customer_type.split('_')[1]
    tariff_group = next(item for item in tariff_matrix if item['subgrupo'] == subgroup)
    tariff_value = tariff_group['tarifas'][int(subsubgroup)-1]

    dt1, dt2 = data_list_energy_proj[0][0], data_list_energy_proj[len(data_list_energy_proj)-1][0]
    dt1_month, dt1_year, dt2_month, dt2_year = dt1.month, dt1.year, dt2.month, dt2.year
    pis_cofins_icms_1 = next(item for item in pis_cofins_icms if item[0] == dt1_year and item[1] == dt1_month)
    pis_cofins_icms_2 = next(item for item in pis_cofins_icms if item[0] == dt2_year and item[1] == dt2_month)

    # determina o valor da bandeira da parte 1 e da parte 2
    flag_value1, flag_value2 = 0.0, 0.0
    if use_valid_flags:
        for tf in allTariffFlags:
            if tf.month == dt1_month and tf.year == dt1_year:
                flag_value1 = float(tf.value)
            if tf.month == dt2_month and tf.year == dt2_year:
                flag_value2 = float(tf.value)
    else:
        flag_value1 = flag_tariffs[simulated_flag]
        flag_value2 = flag_tariffs[simulated_flag]

    # montagem dos dados de tarifas, com a seguinte formatação:
    # datetime (1 por mês), tarifa, pis(%), cofins(%), icms_res1(%), icms_res2(%), icms_rur1(%), icms_rur2(%), icms_out(%), bandeira
    dt1, dt2 = datetime(dt1_year, dt1_month, 1, 0, 0, 0), datetime(dt2_year, dt2_month, 1, 0, 0, 0)
    tariff_data = [[dt1, tariff_value] + pis_cofins_icms_1[2:] + [flag_value1],
                   [dt2, tariff_value] + pis_cofins_icms_2[2:] + [flag_value2]]

    # limites de icms para classe residencial (<= 150 e > 150 kWh) e classe rural (<= 500 e > 500 kWh)
    icms_kwh_limits = [150.0, 500.0]

    # função para cálculo da fatura
    dt_base = data_list_energy_proj[0][0]
    etot_accum_ini = data_list_energy_proj[0][1] + data_list_energy_proj[0][2] + data_list_energy_proj[0][3] + data_list_energy_proj[0][4]

    # discrimina o tipo de consumidor
    if subgroup == 'B1': customer_class = 0  # residencial
    elif subgroup == 'B2': customer_class = 1  # rural
    else: customer_class = 2  # outros

    # calcula a fatura total para medição da lista data_list_energy_proj
    for i in range(len(data_list_energy_proj)):
        v = data_list_energy_proj[i]
        if i == 0:
            etot_accum_ini = v[1] + v[2] + v[3] + v[4]
            v.append(0.0)  # custo 0 para a medição inicial
            continue

        # consumo total no período
        etot_accum = v[1] + v[2] + v[3] + v[4]
        etot_period = etot_accum - etot_accum_ini

        # número de dias de medição durante mês 1 e durante mês 2
        days = (v[0] - dt_base).days + 1
        if days == 0:
            days, days_1, days_2 = 1, 1, 0
        else:
            if v[0].month > dt_base.month:
                days_2 = v[0].day
                days_1 = days - days_2
            else:
                days_2 = 0
                days_1 = days

        # obtém os limites de consumo para ICMS, para definir partes 1 e 2 do consumo
        if customer_class == 0:
            icms_kwh_limit = icms_kwh_limits[0]
        elif customer_class == 1:
            icms_kwh_limit = icms_kwh_limits[1]
        else:
            icms_kwh_limit = 100000.0

        # calcula os consumos (partes 1 e 2) para pro-rata 1 e pro-rata 2
        if etot_period <= icms_kwh_limit:
            e_pro_rata1_p1 = etot_period * days_1 / (days_1 + days_2)
            e_pro_rata1_p2 = 0.0
            e_pro_rata2_p1 = etot_period * days_2 / (days_1 + days_2)
            e_pro_rata2_p2 = 0.0
        else:
            e_pro_rata1_p1 = icms_kwh_limit * days_1 / (days_1 + days_2)
            e_pro_rata1_p2 = (etot_period - icms_kwh_limit) * days_1 / (days_1 + days_2)
            e_pro_rata2_p1 = icms_kwh_limit * days_2 / (days_1 + days_2)
            e_pro_rata2_p2 = (etot_period - icms_kwh_limit) * days_2 / (days_1 + days_2)

        # determina tarifa, PIS e COFINS relativas aos meses 1 e 2
        tariff_pis_cofins_1, tariff_pis_cofins_2 = None, None
        for t in tariff_data:
            if t[0].year == dt_base.year and t[0].month == dt_base.month:
                tariff_pis_cofins_1 = t
            if t[0].year == v[0].year and t[0].month == v[0].month:
                tariff_pis_cofins_2 = t
            if tariff_pis_cofins_1 and tariff_pis_cofins_2:
                break

        # calcula tarifa com impostos e bandeira com impostos
        if customer_class == 0:  # residencial
            # custo relativo à tarifa
            tariff_pr1, tariff_pr2 = tariff_pis_cofins_1[1], tariff_pis_cofins_2[1]
            pis, cofins = tariff_pis_cofins_2[2] / 100.0, tariff_pis_cofins_2[3] / 100.0
            icms_p1, icms_p2 = tariff_pis_cofins_2[4] / 100.0, tariff_pis_cofins_2[5] / 100.0
            # tarifa com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            tariffWithTaxes = [tariff_pr1 / (1.0 - pis - cofins - icms_p1),
                               tariff_pr1 / (1.0 - pis - cofins - icms_p2),
                               tariff_pr2 / (1.0 - pis - cofins - icms_p1),
                               tariff_pr2 / (1.0 - pis - cofins - icms_p2)]

            # custo relativo à bandeira
            flag_pr1, flag_pr2 = tariff_pis_cofins_1[9], tariff_pis_cofins_2[9]
            # bandeira com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            flagWithTaxes = [flag_pr1 / (1.0 - pis - cofins - icms_p1),
                             flag_pr1 / (1.0 - pis - cofins - icms_p2),
                             flag_pr2 / (1.0 - pis - cofins - icms_p1),
                             flag_pr2 / (1.0 - pis - cofins - icms_p2)]
        elif customer_class == 1:  # rural
            # custo relativo à tarifa
            tariff_pr1, tariff_pr2 = tariff_pis_cofins_1[1], tariff_pis_cofins_2[1]
            pis, cofins = tariff_pis_cofins_2[2] / 100.0, tariff_pis_cofins_2[3] / 100.0
            icms_p1, icms_p2 = tariff_pis_cofins_2[6] / 100.0, tariff_pis_cofins_2[7] / 100.0
            tariffWithTaxes = [tariff_pr1 / (1.0 - pis - cofins - icms_p1),
                               tariff_pr1 / (1.0 - pis - cofins - icms_p2),
                               tariff_pr2 / (1.0 - pis - cofins - icms_p1),
                               tariff_pr2 / (1.0 - pis - cofins - icms_p2)]

            # custo relativo à bandeira
            flag_pr1, flag_pr2 = tariff_pis_cofins_1[9], tariff_pis_cofins_2[9]
            # bandeira com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            flagWithTaxes = [flag_pr1 / (1.0 - pis - cofins - icms_p1),
                             flag_pr1 / (1.0 - pis - cofins - icms_p2),
                             flag_pr2 / (1.0 - pis - cofins - icms_p1),
                             flag_pr2 / (1.0 - pis - cofins - icms_p2)]
        else:  # outros
            # custo relativo à tarifa
            tariff_pr1, tariff_pr2 = tariff_pis_cofins_1[1], tariff_pis_cofins_2[1]
            pis, cofins = tariff_pis_cofins_2[2] / 100.0, tariff_pis_cofins_2[3] / 100.0
            icms = tariff_pis_cofins_2[8] / 100.0
            tariffWithTaxes = [tariff_pr1 / (1.0 - pis - cofins - icms),
                               0.0,
                               tariff_pr2 / (1.0 - pis - cofins - icms),
                               0.0]

            # custo relativo à bandeira
            flag_pr1, flag_pr2 = tariff_pis_cofins_1[9], tariff_pis_cofins_2[9]
            # bandeira com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            flagWithTaxes = [flag_pr1 / (1.0 - pis - cofins - icms),
                             0.0,
                             flag_pr2 / (1.0 - pis - cofins - icms),
                             0.0]

        # cálculo da componente correspondente à tarifa, sem bandeira
        value_pr1_p1 = e_pro_rata1_p1 * tariffWithTaxes[0]
        value_pr1_p2 = e_pro_rata1_p2 * tariffWithTaxes[1]
        value_pr2_p1 = e_pro_rata2_p1 * tariffWithTaxes[2]
        value_pr2_p2 = e_pro_rata2_p2 * tariffWithTaxes[3]
        value_total_tariff = value_pr1_p1 + value_pr1_p2 + value_pr2_p1 + value_pr2_p2

        # cálculo da componente correspondente à bandeira tarifária
        flag_pr1_p1 = e_pro_rata1_p1 * flagWithTaxes[0]
        flag_pr1_p2 = e_pro_rata1_p2 * flagWithTaxes[1]
        flag_pr2_p1 = e_pro_rata2_p1 * flagWithTaxes[2]
        flag_pr2_p2 = e_pro_rata2_p2 * flagWithTaxes[3]
        value_total_flag = flag_pr1_p1 + flag_pr1_p2 + flag_pr2_p1 + flag_pr2_p2

        # cálculo total da fatura, até este momento:
        value_total = value_total_tariff + value_total_flag
        v.append(value_total)


    val_ini = data_list_energy_proj[0]
    val_last = data_list_energy_proj[len(data_list_energy_proj) - 1]
    kwh_ini = val_ini[1] + val_ini[2] + val_ini[3] + val_ini[4]
    kwh_last = val_last[1] + val_last[2] + val_last[3] + val_last[4]
    kwh = round(kwh_last - kwh_ini, 2)

    total_cost = round(data_list_energy_proj[len(data_list_energy_proj) - 1][5], 2)
    icms_perc = 12.0
    icms_cost = round(total_cost * icms_perc / 100.0, 2)
    energy_cost = round(total_cost - icms_cost, 2)
    tariff_equiv = round(energy_cost / kwh, 2)

    # remove o valor adicionado ao final de cada ponto
    for v in data_list_energy_proj: v.pop()

    # monta a estrutura de saída
    summary_costs = [['Convencional', kwh, tariff_equiv, energy_cost, icms_perc, icms_cost, total_cost]]

    return summary_costs
