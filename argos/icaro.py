import datetime
from datetime import datetime


def cost_white(data_list_energy_hour, flag_name = None):
    # DADO EXTERNO: valores de tarifa branca por patamar
    hourly_white_tariffs = [0.43664, 0.61737, 0.96013]

    # DADO EXTERNO: valor de ICMS(%)
    icms = 12.0

    # DADO EXTERNO - matriz de bandeiras tarifárias, com a seguinte formatação:
    # bandeira, valor (R$/kWh sem impostos)
    # 0: verde, 1: amarela, 2: vermelha pat. 1, 3: vermelha pat. 2, 4: escassez hídrica
    flag_tariffs = [0.0, 0.01874, 0.03971, 0.09492, 0.1420]

    # função para mapear nome da bandeira e valor da bandeira
    def flag_value(flag_name, flag_tariffs):
        if flag_name == 'VD': value = flag_tariffs[0]
        elif flag_name == 'AM': value = flag_tariffs[1]
        elif flag_name == 'V1': value = flag_tariffs[2]
        elif flag_name == 'V2': value = flag_tariffs[3]
        else: value = flag_tariffs[4]
        return value

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
Função para cálculo do valor total da fatura com tarifa convencional
- data_list_energy_proj: lista com os valores de consumo
- customer_type: tipo/classe do consumidor (B1_1, B1_2, ..., B2_1, B2_2, ...
- use_valid_flags: usar (ou não) as bandeiras vigentes
- simulated_flag: nome da bandeira simulada (apenas se use_valid_flags=false)
"""
def cost_conventional(data_list_energy_proj, customer_type, use_valid_flags, simulated_flag = None):

    # DADO EXTERNO - matriz de bandeiras tarifárias, com a seguinte formatação:
    # bandeira, valor (R$/kWh sem impostos)
    # 0: verde, 1: amarela, 2: vermelha pat. 1, 3: vermelha pat. 2, 4: escassez hídrica
    flag_tariffs = [0.0, 0.01874, 0.03971, 0.09492, 0.1420]

    # função para mapear nome da bandeira e valor da bandeira
    def flag_value(flag_name, flag_tariffs):
        if flag_name == 'VD': value = flag_tariffs[0]
        elif flag_name == 'AM': value = flag_tariffs[1]
        elif flag_name == 'V1': value = flag_tariffs[2]
        elif flag_name == 'V2': value = flag_tariffs[3]
        else: value = flag_tariffs[4]
        return value

    # DADO EXTERNO - matriz de tarifas
    tariff_matrix = [{'subgrupo': 'B1', 'tarifas': [0.53224, 0.16121, 0.27636, 0.41454, 0.4606]},
                     {'subgrupo': 'B2', 'tarifas': [0.46837, 0.46837, 0.44709]},
                     {'subgrupo': 'B3', 'tarifas': [0.460451, 0.53224]},
                     {'subgrupo': 'B4a', 'tarifas': [0.29273]},
                     {'subgrupo': 'B4b', 'tarifas': [0.31934]}]

    # DADO EXTERNO - matriz de impostos PIS/COFINS/ICMS
    # ano, mês, PIS(%), COFINS(%), ICMS_res1(%), ICMS_res2(%), ICMS_rur1(%), ICMS_rur2(%), ICMS_out(%)
    pis_cofins_icms = [[2021, 6,  0.50, 2.0, 12.0, 25.0, 12.0, 25.0, 25.0],
                       [2021, 7,  0.41, 2.0, 12.0, 25.0, 12.0, 25.0, 25.0],
                       [2021, 8,  0.55, 2.0, 12.0, 25.0, 12.0, 25.0, 25.0],
                       [2021, 9,  0.53, 2.0, 12.0, 25.0, 12.0, 25.0, 25.0],
                       [2021, 10, 0.55, 2.0, 12.0, 25.0, 12.0, 25.0, 25.0]]

    # DADO EXTERNO - matriz de bandeiras tarifárias ao longo do tempo
    # ano, mês, bandeira
    tariff_flags = [[2021, 6, 'AM'],
                    [2021, 7, 'AM'],
                    [2021, 8, 'AM'],
                    [2021, 9, 'AM'],
                    [2021, 10, 'V1']]

    # determina tarifas sem imposto (R$/kWh)
    subgroup, subsubgroup = customer_type.split('_')[0].upper(), customer_type.split('_')[1]
    tariff_group = next(item for item in tariff_matrix if item['subgrupo'] == subgroup)
    tariff_value = tariff_group['tarifas'][int(subsubgroup)-1]

    dt1, dt2 = data_list_energy_proj[0][0], data_list_energy_proj[len(data_list_energy_proj)-1][0]
    dt1_month, dt1_year, dt2_month, dt2_year = dt1.month, dt1.year, dt2.month, dt2.year
    pis_cofins_icms_1 = next(item for item in pis_cofins_icms if item[0] == dt1_year and item[1] == dt1_month)
    pis_cofins_icms_2 = next(item for item in pis_cofins_icms if item[0] == dt2_year and item[1] == dt2_month)

    # consulta últimas bandeiras vigentes para obter as bandeiras do PRO-RATA1 e do PRO-RATA2
    flag_1, flag_2 = 'VD', 'VD'  # valores default
    for fl in tariff_flags:
        if fl[0] == dt1_year and fl[1] == dt1_month:
            flag_1 = fl[2]
        if fl[0] == dt2_year and fl[1] == dt2_month:
            flag_2 = fl[2]

    # montagem dos dados de tarifas, com a seguinte formatação:
    # datetime (1 por mês), tarifa, pis(%), cofins(%), icms_res1(%), icms_res2(%), icms_rur1(%), icms_rur2(%), icms_out(%), bandeira
    dt1, dt2 = datetime(dt1_year, dt1_month, 1, 0, 0, 0), datetime(dt2_year, dt2_month, 1, 0, 0, 0)
    tariff_data = [[dt1, tariff_value] + pis_cofins_icms_1[2:] + [flag_1],
                   [dt2, tariff_value] + pis_cofins_icms_2[2:] + [flag_2]]

    # limites de icms para classe residencial (<= 150 e > 150 kWh) e classe rural (<= 500 e > 500 kWh)
    icms_limits = [150.0, 500.0]

    # função para cálculo da fatura
    dt_base = data_list_energy_proj[0][0]
    etot_accum_ini = data_list_energy_proj[0][1] + data_list_energy_proj[0][2] + data_list_energy_proj[0][3] + data_list_energy_proj[0][4]

    # discrimina o tipo de consumidor
    if subgroup == 'B1': customer_class = 0  # residencial
    elif subgroup == 'B2': customer_class = 1  # rural
    else: customer_class = 2  # outros

    # calcula a fatura total para medição da lista data_list_energy_proj
    etot_accum_prorata1 = -1
    for i in range(len(data_list_energy_proj)):
        v = data_list_energy_proj[i]
        if i == 0:
            etot_accum_ini = v[1] + v[2] + v[3] + v[4]
            v.append(0.0)  # custo 0 para a medição inicial
            continue
        # calcula as energias pro-rata1 (kWh durante o mês 1) e pro-rata2 (kWh durante o mês 2)
        etot_accum = v[1] + v[2] + v[3] + v[4]
        if v[0].month == dt_base.month:
            e_pro_rata1 = etot_accum - etot_accum_ini
            e_pro_rata2 = 0.0
        else:
            if etot_accum_prorata1 == -1:
                v_prev = data_list_energy_proj[i - 1]
                etot_accum_prorata1 = v_prev[1] + v_prev[2] + v_prev[3] + v_prev[4]
            e_pro_rata1 = etot_accum_prorata1 - etot_accum_ini
            e_pro_rata2 = etot_accum - etot_accum_prorata1

        # para energias pro-rata1 e pro-rata2, calcula partes 1 e 2
        if customer_class == 0:
            icms_limit = icms_limits[0]
        elif customer_class == 1:
            icms_limit = icms_limits[1]
        else:
            icms_limit = 100000.0

        if e_pro_rata1 <= icms_limit:
            e_pro_rata1_p1 = e_pro_rata1
            e_pro_rata1_p2 = 0.0
        else:
            e_pro_rata1_p1 = icms_limit
            e_pro_rata1_p2 = e_pro_rata1 - icms_limit
        if e_pro_rata2 <= icms_limit:
            e_pro_rata2_p1 = e_pro_rata2
            e_pro_rata2_p2 = 0.0
        else:
            e_pro_rata2_p1 = icms_limit
            e_pro_rata2_p2 = e_pro_rata2 - icms_limit

        # determina tarifa, PIS e COFINS relativas aos meses 1 e 2
        tariff_pis_cofins_1, tariff_pis_cofins_2 = None, None
        for t in tariff_data:
            if t[0].year == dt_base.year and t[0].month == dt_base.month:
                tariff_pis_cofins_1 = t
            if t[0].year == v[0].year and t[0].month == v[0].month:
                tariff_pis_cofins_2 = t

        # calcula tarifa com impostos e bandeira com impostos
        if customer_class == 0:  # residencial
            tariff_pr1, tariff_pr2 = tariff_pis_cofins_1[1], tariff_pis_cofins_2[1]
            pis_pr1, pis_pr2 = tariff_pis_cofins_1[2] / 100.0, tariff_pis_cofins_2[2] / 100.0
            cofins_pr1, cofins_pr2 = tariff_pis_cofins_1[3] / 100.0, tariff_pis_cofins_2[3] / 100.0
            icms_pr1_p1, icms_pr1_p2 = tariff_pis_cofins_1[4] / 100.0, tariff_pis_cofins_1[5] / 100.0
            icms_pr2_p1, icms_pr2_p2 = tariff_pis_cofins_2[4] / 100.0, tariff_pis_cofins_2[5] / 100.0
            # tarifa com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            tariffWithTaxes = [tariff_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p1),
                               tariff_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p2),
                               tariff_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p1),
                               tariff_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p2)]

            if use_valid_flags:
                flag_pr1 = flag_value(tariff_pis_cofins_1[9], flag_tariffs)
                flag_pr2 = flag_value(tariff_pis_cofins_2[9], flag_tariffs)
            else:
                if simulated_flag is not None:
                    flag_pr1 = flag_value(simulated_flag, flag_tariffs)
                    flag_pr2 = flag_value(simulated_flag, flag_tariffs)
                else:
                    flag_pr1, flag_pr2 = 0.0, 0.0
            # bandeira com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            flagWithTaxes = [flag_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p1),
                             flag_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p2),
                             flag_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p1),
                             flag_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p2)]
        elif customer_class == 1:  # rural
            tariff_pr1, tariff_pr2 = tariff_pis_cofins_1[1], tariff_pis_cofins_2[1]
            pis_pr1, pis_pr2 = tariff_pis_cofins_1[2] / 100.0, tariff_pis_cofins_2[2] / 100.0
            cofins_pr1, cofins_pr2 = tariff_pis_cofins_1[3] / 100.0, tariff_pis_cofins_2[3] / 100.0
            icms_pr1_p1, icms_pr1_p2 = tariff_pis_cofins_1[6] / 100.0, tariff_pis_cofins_1[7] / 100.0
            icms_pr2_p1, icms_pr2_p2 = tariff_pis_cofins_2[6] / 100.0, tariff_pis_cofins_2[7] / 100.0
            tariffWithTaxes = [tariff_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p1),
                               tariff_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p2),
                               tariff_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p1),
                               tariff_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p2)]

            if use_valid_flags:
                flag_pr1 = flag_value(tariff_pis_cofins_1[9], flag_tariffs)
                flag_pr2 = flag_value(tariff_pis_cofins_2[9], flag_tariffs)
            else:
                if simulated_flag is not None:
                    flag_pr1 = flag_value(simulated_flag, flag_tariffs)
                    flag_pr2 = flag_value(simulated_flag, flag_tariffs)
                else:
                    flag_pr1, flag_pr2 = 0.0, 0.0
            # bandeira com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            flagWithTaxes = [flag_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p1),
                             flag_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p2),
                             flag_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p1),
                             flag_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p2)]
        else:  # outros
            tariff_pr1, tariff_pr2 = tariff_pis_cofins_1[1], tariff_pis_cofins_2[1]
            pis_pr1, pis_pr2 = tariff_pis_cofins_1[2] / 100.0, tariff_pis_cofins_2[2] / 100.0
            cofins_pr1, cofins_pr2 = tariff_pis_cofins_1[3] / 100.0, tariff_pis_cofins_2[3] / 100.0
            icms_pr1_p1, icms_pr2_p1 = tariff_pis_cofins_1[8] / 100.0, tariff_pis_cofins_2[8] / 100.0
            tariffWithTaxes = [tariff_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p1),
                               0.0,
                               tariff_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p1),
                               0.0]
            if use_valid_flags:
                flag_pr1 = flag_value(tariff_pis_cofins_1[9], flag_tariffs)
                flag_pr2 = flag_value(tariff_pis_cofins_2[9], flag_tariffs)
            else:
                if simulated_flag is not None:
                    flag_pr1 = flag_value(simulated_flag, flag_tariffs)
                    flag_pr2 = flag_value(simulated_flag, flag_tariffs)
                else:
                    flag_pr1, flag_pr2 = 0.0, 0.0
            # bandeira com impostos para pro-rata1 (partes 1 e 2) e para pro-rata2 (partes 1 e 2)
            flagWithTaxes = [flag_pr1 / (1.0 - pis_pr1 - cofins_pr1 - icms_pr1_p1),
                             0.0,
                             flag_pr2 / (1.0 - pis_pr2 - cofins_pr2 - icms_pr2_p1),
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
