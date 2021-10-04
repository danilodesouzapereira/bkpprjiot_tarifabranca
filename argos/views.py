import base64
import calendar
import csv
import json
#import math
import os
import pyodbc
import pytz
import statistics
from operator import attrgetter, itemgetter
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from argos.serializers import CardSerializer, TransactionSerializer, UserSerializer
from .argos import *
from .forms import DateFilterForm, NewUserForm, WhiteTariffForm
from .models import LoraDeviceType, LoraDevice, LoraPayload, Gateway, Transaction, Installation, Card, RechargeStation, RechargePoint, HTTPDevice, InstallationPeriodHTTPDevice
from .serializers import RechargePointSerializer, RechargeStationSerializer, UserSerializer
import numpy as np
from math import sqrt, ceil
from .icaro import *


def account_activation(request, uidb64, token):
    """
    Valida link de ativação.
    Exibe formulário para usuário preencher senha no GET.
    Valida senhas e ativa a conta no POST.
    """
    editionName = settings.APP_CONFIG['edition']
    template_name = 'registration/' + editionName.lower() + '/activation_form.html'
    uid = force_text(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk = uid)
    is_valid_token = default_token_generator.check_token(user, token)

    if request.method == 'GET':
        return render(request, template_name, context = {'validlink': is_valid_token})

    elif request.method == 'POST':
        data = request.POST
        password1 = data['new_password1']
        password2 = data['new_password2']
        if password1 != password2:
            return redirect('argos:account_activation', request = request, uidb64 = uidb64, token = token)
        user.set_password(password1)
        user.is_active = True
        user.save()
        return redirect('argos:activation_complete')


@api_view(['POST'])
def account_registration(request):
    """
    Valida e registra o usuário e envia e-mail com link de ativação
    da conta.
    """
    serializer = UserSerializer(data = request.data)
    data = {}
    editionName = settings.APP_CONFIG['edition']
    template_name = 'registration/' + editionName.lower() + '/activation_email.html'

    if serializer.is_valid():
        data['response'] = 'Usuário registrado com sucesso. Você receberá um e-mail com um link para ativar sua conta.'

        try:
            """
            Usuário registrado anteriormente terá e-mail e grupo atualizados e receberá
            novo link de ativação.
            """
            user = User.objects.get(username = serializer.validated_data['username'])
        except User.DoesNotExist:
            user = User.objects.create_user(
                username = serializer.validated_data['username'],
                email = serializer.validated_data['email'],
                is_active = False,
                password = 'argosdaimon'
            )
        user.email = serializer.validated_data['email']

        for group_str in user.groups.values_list('name', flat = True):
            if group_str == 'Equatorial-Users-PVE' or group_str == 'Equatorial-Users-PUC':
                group = Group.objects.get(name = group_str)
                user.groups.remove(group)

        group = None
        groups = serializer.validated_data['groups']
        group = Group.objects.get(name = groups[0]['name'])
        user.groups.add(group)
        user.save()

        message = render_to_string(template_name, {
            'user': user,
            'domain': request.get_host(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        subject = 'Ative sua conta'
        send_mail(
            subject = subject,
            message = message,
            from_email = 'argos@daimon.com.br',
            recipient_list = [user.email],
            fail_silently = False,
            )
        return Response(data, status = status.HTTP_201_CREATED)

    else:
        data = serializer.errors
        return Response(data, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def cards_usedby_installation_code(request, installation_code):
    """
    Obtém cartões usados por uma instalação específica.
    """
    #obtém transações de crédito para uma instalação específica
    transaction_list = Transaction.objects.filter(action__exact = 'Credit', installation__code__exact = installation_code)

    #monta lista de cartões usados pela instalação
    card_list = []
    for tr in transaction_list:
        card = Card(code=tr.card_code, value=tr.energy_value)
        card_list.append(card)

    #proteção: verifica se a lista de cartões está vazia
    if len(card_list) == 0:
        return Response(status = status.HTTP_404_NOT_FOUND)

    #responde com a lista de cartões usados pela instalação
    serializer = CardSerializer(card_list, many=True)
    return Response(serializer.data, status.HTTP_200_OK)


@api_view(['POST'])
def credit(request):
    """
    Recebe dados enviados pelo aplicativo mobile (android) por meio da
    requisição POST, completa os campos restantes da transação e faz a
    gravação no banco de dados.
    """
    #obtém objeto instalação para o código enviado
    installation_list = Installation.objects.filter(code__exact = request.data['installation_code'])
    #verifica se existe instalação com esse código
    if len(installation_list) == 0:
        return Response(status = status.HTTP_404_NOT_FOUND)

    #obtém objeto cartão para o código enviado
    card_list = Card.objects.filter(code__exact = request.data['card_code'])
    #verifica se existe cartão com esse código
    if len(card_list) == 0:
        return Response(status = status.HTTP_404_NOT_FOUND)

    #verifica se cartão já foi utilizado
    if (card_list[0].is_used == True):
        return Response(status = status.HTTP_409_CONFLICT)

    #se chegar aqui, é porque tudo já foi validado
    #obtém a última transação da instalação consumidora, desde que ela
    #não seja de ligar ou desligar
    transaction_list = Transaction.objects.filter(installation_code__exact = installation_list[0].code
        ).exclude(action__exact = 'Turn On'
        ).exclude(action__exact = 'Turn Off').order_by('-datetime_rx')
    #calcula o novo saldo após o crédito
    if (len(transaction_list) > 0):
    	energy_account = transaction_list[0].energy_account + card_list[0].value
    else:
    	energy_account = card_list[0].value
    #cria objeto transação
    tr = Transaction(datetime_rx=timezone.now(),
        installation_code=installation_list[0].code, card_code=card_list[0].code,
        energy_value=card_list[0].value, energy_account=energy_account,
        action='Credit', installation=installation_list[0], card=card_list[0])
    #cria serializador
    serializer = TransactionSerializer(tr)
    #atualiza o status do cartão
    card_list[0].is_used = True
    card_list[0].save()
    #salva transação no banco de dados
    tr.save()
    return Response(serializer.data, status = status.HTTP_201_CREATED)


@login_required
def dash(request):
    #obtém lista de tipos de dispositivos, dispositivos e gateways
    device_types_tup, devices_tup, gateways_tup = AllObjects(request)
    #filtra para excluir dispositivos que usam servidor local
    devices_tup = [obj for obj in devices_tup if obj[0].server.server_id != 1]
    gateways_tup = [obj for obj in gateways_tup if obj[0].server.server_id != 1]
    #filtra para excluir dispositivos que não possuem broker configurado em appConfig.yaml
    devices_tup = [obj for obj in devices_tup if obj[0].server.desc in settings.APP_CONFIG['mqtt_hosts']]
    gateways_tup = [obj for obj in gateways_tup if obj[0].server.desc in settings.APP_CONFIG['mqtt_hosts']]
    #monta lista de tipos de dispositivos a partir dos dispositivos filtrados
    device_types = [dev[0].device_type for dev in devices_tup]
    #elimina tipos repetidos
    device_types = list(dict.fromkeys(device_types))
    #monta listas de descrições
    devTypeDesc_list = [dev_type.desc for dev_type in device_types]
    #remonta lista
    device_types_tup = list(zip(device_types, devTypeDesc_list))
    #cria dicionário de dados dos dispositivos para conexão mqtt via websocket
    devices_dict = [{'mqtt_data_format': dev[0].server.mqtt_data_format,
        'rest_data_format': dev[0].server.rest_data_format,
        'eui': dev[0].eui,
        'pwd': dev[0].pwd,
        'device_type': dev[0].device_type.type_id,
        'server': dev[0].server.desc,
        'enabled': True} for dev in devices_tup]
    is_admin = False
    groups = request.user.groups.all()
    for group in groups:
        if group.name.endswith('-Admin') == True:
            is_admin = True

    editionName = settings.APP_CONFIG['edition'].lower()

    return render(request, 'argos/' + editionName + '/dash.html', {
    	'device_json': json.dumps(devices_dict),
        'device_type_list': device_types_tup,
        'device_list': devices_tup,
        'is_admin': is_admin,
    })


@login_required
def whitetarifflist(request):
    editionName = settings.APP_CONFIG['edition'].lower()
    # obtém lista de HTTPDevices do tipo 1 (medidor de energia)
    meters = HTTPDevice.objects.filter(device_type__exact=1)
    # obtém lista de instalações do tipo 1 (instalação consumidora)
    installations = Installation.objects.filter(installation_type__exact=1)
    # lista de dicionários mapeando instalação x medidor instalado
    installations_meters = []
    for installation in installations:
        http_devices = installation.http_devices.all()
        for http_device in http_devices:
            if http_device.device_type.type_id != 1:
                continue
            inst_period = InstallationPeriodHTTPDevice.objects.get(installation__exact=installation, device__exact=http_device)
            date_ini = inst_period.datetime_ini.strftime('%Y-%m-%d %H:%M')
            date_fin = inst_period.datetime_fin.strftime('%Y-%m-%d %H:%M')
            installations_meters.append({'installation': installation, 'meter': http_device, 'date_ini': date_ini, 'date_fin': date_fin})

    context = {'meters': meters, 'installations_meters': installations_meters}
    response = render(request, 'argos/' + editionName + '/whitetarifflist.html', context)
    return response


@login_required
def whitetariff(request, mac):
    editionName = settings.APP_CONFIG['edition'].lower()

    if request.POST:
        form = WhiteTariffForm(request.POST)

        # verifica filtros de data inicial e data final
        if form['datetime_ini'].value():
            datetime_ini = datetime.strptime(form['datetime_ini'].value(), '%Y-%m-%dT%H:%M')
        elif form['datetime_ini_hidden'].value():
            datetime_ini = datetime.strptime(form['datetime_ini_hidden'].value(), '%Y-%m-%dT%H:%M')
        else:
            datetime_ini = None

        if form['datetime_fin'].value():
            datetime_fin = datetime.strptime(form['datetime_fin'].value(), '%Y-%m-%dT%H:%M')
        elif form['datetime_fin_hidden'].value():
            datetime_fin = datetime.strptime(form['datetime_fin_hidden'].value(), '%Y-%m-%dT%H:%M')
        else:
            datetime_fin = None

        # verifica o filtro do gráfico 2 (consumo diário)
        if form['datetime_ref'].value():
            date_value = form['datetime_ref'].value() + 'T00:00'
            datetime_kwh_daily = datetime.strptime(date_value, '%Y-%m-%dT%H:%M')
        else:
            datetime_kwh_daily = None

        # verifica filtros para o gráfico 3 (consumo típico)
        selectedSeasons = request.POST.getlist('ckSeason')
        selectedWeekdays = request.POST.getlist('ckWeekday')
        if len(selectedSeasons) == 0 and len(selectedWeekdays) == 0:
            selectedSeasons = request.POST.getlist('ckSeason_hidden')
            selectedWeekdays = request.POST.getlist('ckWeekday_hidden')
        if len(selectedSeasons) == 0 and len(selectedWeekdays) == 0:
            # se as duas listas estão vazias, o usuário não Atualizou filtro do gráfico 3
            seasons_consider = [1, 2, 3, 4]
            days_consider = [0, 1, 2, 3, 4, 5, 6]
        else:
            # estações do ano selecionadas pelo usuário
            seasons_consider = []
            if 'summer' in selectedSeasons: seasons_consider.append(1)
            if 'fall' in selectedSeasons:   seasons_consider.append(2)
            if 'winter' in selectedSeasons: seasons_consider.append(3)
            if 'spring' in selectedSeasons: seasons_consider.append(4)
            # dias da semana selecionados pelo usuário
            days_consider = []
            if 'monday' in selectedWeekdays:    days_consider.append(0)
            if 'tuesday' in selectedWeekdays:   days_consider.append(1)
            if 'wednesday' in selectedWeekdays: days_consider.append(2)
            if 'thursday' in selectedWeekdays:  days_consider.append(3)
            if 'friday' in selectedWeekdays:    days_consider.append(4)
            if 'saturday' in selectedWeekdays:  days_consider.append(5)
            if 'sunday' in selectedWeekdays:    days_consider.append(6)
    else:
        datetime_kwh_daily = None
        seasons_consider = [1, 2, 3, 4]
        days_consider = [0, 1, 2, 3, 4, 5, 6]
        datetime_ini = None
        datetime_fin = None

    #obtém lista de HTTPDevice tipo 1 (medidor de energia)
    meters_list = HTTPDevice.objects.filter(device_type__exact=1)
    #medidor específico
    meter = HTTPDevice.objects.get(device_type__exact=1, mac__exact=mac)
    # obtém lista de instalações do tipo 1 (instalação consumidora)
    installations = Installation.objects.filter(installation_type__exact=1)
    # lista de dicionários mapeando instalação x medidor instalado
    installations_meters = []
    for installation in installations:
        http_devices = installation.http_devices.all()
        for http_device in http_devices:
            if http_device.device_type.type_id != 1:
                continue
            inst_period = InstallationPeriodHTTPDevice.objects.get(installation__exact=installation, device__exact=http_device)
            date_ini = inst_period.datetime_ini.strftime('%Y-%m-%d %H:%M')
            date_fin = inst_period.datetime_fin.strftime('%Y-%m-%d %H:%M')
            installations_meters.append({'installation': installation, 'meter': http_device, 'date_ini': date_ini, 'date_fin': date_fin})

    # Geração de dados, emulando a recuperação de dados do banco.
    meas_interval_minutes = 5   # intervalo em minutos entre medições
    num_meas_days = 32  # número de dias de medição
    num_meas = round((num_meas_days * 24 * 60) / meas_interval_minutes)  # número de medições
    # datetime_fin_max = datetime.now()
    # datetime_ini_min = datetime_fin_max + timedelta(minutes=-meas_interval_minutes * num_meas)
    datetime_fin_max = datetime(2021, 7, 6, 12, 0, 0)
    datetime_ini_min = datetime_fin_max + timedelta(minutes=-meas_interval_minutes * num_meas)

    # Na primeira chamada deste método, os limites de datas são os limites máximos
    # (definidos pelas datas mínima e máxima dos dados disponíveis)
    # data mínima dos dados = datetime_ini_min
    # data máxima dos dados = datetime_fin_max
    if datetime_ini is None and datetime_fin is None:
        datetime_ini = datetime_ini_min
        datetime_fin = datetime_fin_max
        # se a diferença de datas supera 30 dias, limita datetime_ini
        if (datetime_fin - datetime_ini).days > 30:
            datetime_ini = datetime_fin + timedelta(days=-30)

    """
    Produção artificial dos dados (emulando a recuperação de dados do medidor)
    """
    # Geração dos dados (tensões, correntes, potências ativas e reativas)
    data_list = []
    pf = 0.92  # fator de potência considerado
    loadshape_weekday = [0.594, 0.534, 0.504, 0.475, 0.475, 0.534, 0.534, 0.95, 1.366, 1.514, 1.425, 1.247, 1.009, 1.425, 1.485, 1.425, 1.425, 1.128, 1.069, 1.247, 1.069, 1.009, 0.831, 0.712]
    loadshape_saturday = [0.775, 0.732, 0.689, 0.646, 0.775, 0.732, 0.775, 0.99, 1.249, 1.335, 1.421, 1.249, 1.162, 1.033, 1.033, 0.99, 1.016, 1.042, 1.197, 1.162, 1.076, 0.947, 0.99, 0.973]
    loadshape_sunday = [0.942, 0.986, 0.942, 0.897, 0.807, 0.807, 0.807, 0.986, 1.076, 1.076, 1.031, 0.986, 0.942, 0.942, 0.888, 0.897, 0.897, 1.058, 1.256, 1.256, 1.238, 1.166, 1.031, 1.076]
    loadshape_1pu = [1.0 for i in range(24)]
    for i in range(num_meas):
        datetime_rx = datetime_fin_max + timedelta(minutes=-meas_interval_minutes * i)
        if datetime_rx < datetime_ini_min:
            break
        # volts = np.random.normal(127.0, 3.0, 3)  # vetor de 3 tensões aleatórias
        volts = [127.0, 127.0, 127.0]
        va, vb, vc = round(float(volts[0]), 2), round(float(volts[1]), 2), round(float(volts[2]), 2)

        # corrente média x curva típica (pu da média)
        if datetime_rx.weekday() == 5:
            # i_rated = 5 * loadshape_saturday[datetime_rx.hour]
            i_rated = 1.202307 * loadshape_1pu[datetime_rx.hour]
        elif datetime_rx.weekday() == 6:
            # i_rated = 5 * loadshape_sunday[datetime_rx.hour]
            i_rated = 1.202307 * loadshape_1pu[datetime_rx.hour]
        else:
            # i_rated = 5 * loadshape_weekday[datetime_rx.hour]
            i_rated = 1.202307 * loadshape_1pu[datetime_rx.hour]

        # #debug
        # if datetime_rx.day == 26 and datetime_rx.month == 8 and datetime_rx.hour == 12:
        #     i_rated *= 3

        # amps = np.random.normal(i_rated, 1.0, 4)  # vetor de 4 correntes aleatórias
        amps = [i_rated, i_rated, i_rated, i_rated]
        ia, ib, ic, id = round(float(amps[0]), 5), round(float(amps[1]), 5), round(float(amps[2]), 5), round(
            float(amps[3]), 5)

        # if datetime_rx.month == 9 and datetime_rx.day == 16 and datetime_rx.hour == 12:
        #     ia, ib, ic, id = 2 * ia, 2 * ib, 2 * ic, 2 * id

        pa, pb, pc, pd = va * ia * pf, vb * ib * pf, vc * ic * pf, va * id * pf
        qa, qb, qc, qd = va * ia * sqrt(1.0 - pf * pf), vb * ib * sqrt(1.0 - pf * pf), vc * ic * sqrt(
            1.0 - pf * pf), va * id * sqrt(1.0 - pf * pf)
        pa, pb, pc, pd = round(pa, 5), round(pb, 5), round(pc, 5), round(pd, 5)
        qa, qb, qc, qd = round(qa, 5), round(qb, 5), round(qc, 5), round(qd, 5)
        data_list.append([datetime_rx, va, vb, vc,
                          ia, ib, ic, id,
                          pa, pb, pc, pd,
                          qa, qb, qc, qd])
    data_list.reverse()

    """
    Montagem das curvas de energias acumuladas
    """
    # neste ponto, temos: tensões [V], correntes [A] e potências [W]
    # calcula curvas (fases a,b,c,d) de energia consumida acumulada [kWh]
    for i in range(len(data_list)):
        if i == 0:
            values = data_list[0]
            values.append(0.0)   # 16 - Ea acumulado [kWh]
            values.append(0.0)   # 17 - Eb acumulado [kWh]
            values.append(0.0)   # 18 - Ec acumulado [kWh]
            values.append(0.0)   # 19 - Ed acumulado [kWh]
        else:
            values = data_list[i]
            values_prev = data_list[i-1]
            dt = 5.0 / 60.0  # em horas
            Ea_prev, Eb_prev, Ec_prev, Ed_prev = values_prev[16], values_prev[17], values_prev[18], values_prev[19]
            Pa, Pb, Pc, Pd = values[8], values[9], values[10], values[11]
            dEa, dEb, dEc, dEd = Pa * dt / 1000.0, Pb * dt / 1000.0, Pc * dt / 1000.0, Pd * dt / 1000.0
            Ea, Eb, Ec, Ed = Ea_prev + dEa, Eb_prev + dEb, Ec_prev + dEc, Ed_prev + dEd
            values.append(round(Ea, 6))    # 16 - Ea acumulado [kWh]
            values.append(round(Eb, 6))    # 17 - Eb acumulado [kWh]
            values.append(round(Ec, 6))    # 18 - Ec acumulado [kWh]
            values.append(round(Ed, 6))    # 19 - Ed acumulado [kWh]

    """
    Montagem das curvas de consumo com granularidade horária
    Campos: datetime, Eaccum_A, Eaccum_B, Eaccum_C, Eaccum_D
    """
    data_list_hour = []
    dt_ref = None
    for i in range(len(data_list)):
        val = data_list[i]
        if dt_ref is None:
            dt_ref = val[0]
            continue
        if val[0].hour == dt_ref.hour:
            continue
        dt_ref = val[0]
        val_prev = data_list[i - 1]
        data_list_hour.append(val_prev)


    """
    Teste: cálculo da fatura, considerando alíquotas e bandeiras
    Datetime, va, vb, vc, ia, ib, ic, id, pa, pb, pc, pd, qa, qb, qc, qd, ea, eb, ec, ed
    """
    # teste - projeção linear do consumo
    data_list_energy_proj = [[v[0], v[16], v[17], v[18], v[19]] for v in data_list_hour]
    # billing_dt1 = data_list_hour[0][0]
    # billing_dt2 = billing_dt1 + timedelta(days=30)
    # tot_hours = (data_list_energy_proj[len(data_list_energy_proj)-1][0] - data_list_energy_proj[0][0]).total_seconds() / 3600
    # ea_rate = (data_list_energy_proj[len(data_list_energy_proj) - 1][1] - data_list_energy_proj[0][1]) / tot_hours
    # eb_rate = (data_list_energy_proj[len(data_list_energy_proj) - 1][2] - data_list_energy_proj[0][2]) / tot_hours
    # ec_rate = (data_list_energy_proj[len(data_list_energy_proj) - 1][3] - data_list_energy_proj[0][3]) / tot_hours
    # ed_rate = (data_list_energy_proj[len(data_list_energy_proj) - 1][4] - data_list_energy_proj[0][4]) / tot_hours
    # while True:
    #     v_last = data_list_energy_proj[len(data_list_energy_proj) - 1]
    #     dt_proj = v_last[0] + timedelta(hours=1)
    #     ea_proj, eb_proj, ec_proj, ed_proj = v_last[1] + ea_rate, v_last[2] + eb_rate, v_last[3] + ec_rate, v_last[4] + ed_rate
    #     if dt_proj > billing_dt2:
    #         break
    #     data_list_energy_proj.append([dt_proj, ea_proj, eb_proj, ec_proj, ed_proj])

    # função para cálculo do valor total da fatura
    customer_type = 'B1_1'
    summary_costs = BillConventionalTariff(data_list_energy_proj, customer_type, True)


    """
    ABA 1 - Montagem dos dados relativos às tarifas
    """
    data_list_tariffs = []
    # fora ponta
    for i in range(0, 17):
        data_list_tariffs.append([i, 0.27, 0.0, 0.0, 0.30])
    # período intermediário
    for i in range(17, 18):
        data_list_tariffs.append([i, 0.0, 0.32, 0.0, 0.30])
    # ponta
    for i in range(18, 22):
        data_list_tariffs.append([i, 0.0, 0.0, 0.72, 0.30])
    # período intermediário
    for i in range(22, 23):
        data_list_tariffs.append([i, 0.0, 0.32, 0.0, 0.30])
    # fora ponta
    for i in range(23, 24):
        data_list_tariffs.append([i, 0.27, 0.0, 0.0, 0.30])


    """
    ABA 2 - Cálculo dos consumos horários, para um determinado dia
    Campos: patamar, kwh_tot_patamar, destaque_intermed, detaque_ponta
    """
    consumption_daily = []

    # Se o dia de referência não está definido, identifica o último dia completo
    if datetime_kwh_daily is None:
        dt_ref = data_list_hour[len(data_list_hour)-1][0] + timedelta(days=-1)
        datetime_kwh_daily = datetime(dt_ref.year, dt_ref.month, dt_ref.day, 0, 0, 0)
    else:
        dt_ref = datetime_kwh_daily
    dt_ini = datetime(dt_ref.year, dt_ref.month, dt_ref.day, 0, 0, 0)
    dt_fin = datetime(dt_ref.year, dt_ref.month, dt_ref.day, 23, 59, 59)

    # Monta curva de consumos horários de um dia. Campos:
    # patamar, kwh_tot, destaque interm. destaque ponta
    first_val = None
    for i in range(len(data_list_hour)):
        val = data_list_hour[i]
        if val[0] < dt_ini:
            continue
        if val[0] > dt_fin:
            break
        if first_val is None:
            if i > 0:
                first_val = data_list_hour[i - 1]
            else:
                first_val = data_list_hour[0]
            kwh_tot = first_val[16] + first_val[17] + first_val[18] + first_val[19]
            consumption_daily.append([-1, kwh_tot, 0.0, 0.0])

        kwh_tot = val[16] + val[17] + val[18] + val[19]
        consumption_daily.append([val[0].hour, kwh_tot, 0.0, 0.0])
    # Para cada valor de consumo acumulado total, remove o anterior. Assim,
    # obtemos os consumos acumulados ao final de cada hora.
    for i in reversed(range(1, len(consumption_daily))):
        val_prev = consumption_daily[i - 1]
        val = consumption_daily[i]
        val[1] = val[1] - val_prev[1]
    # Remove o primeiro valor de consumo, que foi apenas auxiliar.
    consumption_daily.pop(0)
    # Inclui os destaques para os intervalos intermediário e ponta
    max_kwh = 0.0
    for val in consumption_daily:
        if val[1] > max_kwh:
            max_kwh = val[1]
    highlight_kwh = ceil(1.5 * max_kwh)
    for i in range(17, 18):
        consumption_daily[i][2] = highlight_kwh
    for i in range(18, 22):
        consumption_daily[i][3] = highlight_kwh
    for i in range(22, 23):
        consumption_daily[i][2] = highlight_kwh


    """
    ABA 3 - Consumo típico
    Considera o filtro de data inicial e data final
    """

    # lista cujas colunas são: patamar (h), kwh típico, destaque interm., destaque ponta
    typical_consumption = [[i, 0.0, 0.0, 0.0] for i in range(24)]
    count = [0 for i in range(24)]
    for i in range(len(data_list_hour)):
        val = data_list_hour[i]
        if val[0] < datetime_ini:
            continue
        if val[0] > datetime_fin:
            break
        # aplica filtros específicos
        if not ConsiderData(val, days_consider, seasons_consider):
            continue
        # acrescenta o consumo total do patamar horário (acumulado menos o acumulado anterior)
        if i == 0:
            kwh_prev = 0.0
        else:
            val_prev = data_list_hour[i - 1]
            kwh_prev = val_prev[16] + val_prev[17] + val_prev[18] + val_prev[19]
        kwh_hour = val[16] + val[17] + val[18] + val[19]
        hour_ref = val[0].hour
        typical_consumption[hour_ref][1] += kwh_hour - kwh_prev
        count[hour_ref] += 1
    # normaliza os valores de consumo
    if count == [0 for i in range(24)]:
        for i in range(24):
            typical_consumption[i][1] = 0.0
    else:
        for i in range(24):
            typical_consumption[i][1] = round(typical_consumption[i][1] / count[i], 3)

    # Inclui os destaques para os intervalos intermediário e ponta
    max_kwh = 0.0
    for val in typical_consumption:
        if val[1] > max_kwh:
            max_kwh = val[1]
    highlight_kwh = ceil(1.5 * max_kwh)
    for i in range(17, 18):
        typical_consumption[i][2] = highlight_kwh
    for i in range(18, 22):
        typical_consumption[i][3] = highlight_kwh
    for i in range(22, 23):
        typical_consumption[i][2] = highlight_kwh

    """
    ABA 4 - Dados relativos à comparação de tarifas (sem bandeiras)
    São considerados filtros de data inicial e data final
    """
    # montagem de lista auxiliar, com a seguinte estrutura:
    # datetime, kwh_faseA, kwh_faseB, kwh_faseC, kwh_faseD
    data_list_energy_hour = []
    for i in range(len(data_list_hour)):
        val = data_list_hour[i]
        if val[0] < datetime_ini:
            continue
        if val[0] > datetime_fin:
            break
        data_list_energy_hour.append([val[0], val[16], val[17], val[18], val[19]])

    # cálculo da fatura considerando tarifa branca, sem bandeiras
    data_list_comp1_white = BillWhiteTariff(data_list_energy_hour)[0:3]
    # cálculo da fatura considerando tarifa convencional, sem bandeiras
    data_list_comp1_conv = BillConventionalTariff(data_list_energy_hour, 'B1_1', False, 0)

    # calcula resultados (total branca, total convencional e diferença)
    total_white = round(data_list_comp1_white[0][6] + data_list_comp1_white[1][6] + data_list_comp1_white[2][6], 2)
    total_conventional = round(data_list_comp1_conv[0][6], 2)
    total_difference = round(total_conventional - total_white, 2)

    # consumos (kWh) totais por patamar horário
    data_list_pie_kwh = [['Fora ponta', round(data_list_comp1_white[0][1])],
                         ['Intermediário', round(data_list_comp1_white[1][1])],
                         ['Ponta', round(data_list_comp1_white[2][1])]]

    """
    ABA 5 - Dados relativos à comparação de tarifas (com bandeiras)
    kWh, R$/kWh, R$(energia), %ICMS, R$(ICMS), R$(total)
    """
    # cálculo da fatura considerando tarifa branca e bandeira verde
    data_list_comp2_white_green = BillWhiteTariff(data_list_energy_hour, 'VD')
    # cálculo da fatura considerando tarifa convencional e bandeira verde
    data_list_comp2_conv_green = BillConventionalTariff(data_list_energy_hour, 'B1_1', False, 0)

    # cálculo da fatura considerando tarifa branca e bandeira amarela
    data_list_comp2_white_yellow = BillWhiteTariff(data_list_energy_hour, 'AM')
    # cálculo da fatura considerando tarifa convencional e bandeira amarela
    data_list_comp2_conv_yellow = BillConventionalTariff(data_list_energy_hour, 'B1_1', False, 1)

    # cálculo da fatura considerando tarifa branca e bandeira vermelha I
    data_list_comp2_white_red1 = BillWhiteTariff(data_list_energy_hour, 'V1')
    # cálculo da fatura considerando tarifa convencional e bandeira vermelha I
    data_list_comp2_conv_red1 = BillConventionalTariff(data_list_energy_hour, 'B1_1', False, 2)

    # cálculo da fatura considerando tarifa branca e bandeira vermelha II
    data_list_comp2_white_red2 = BillWhiteTariff(data_list_energy_hour, 'V2')
    # cálculo da fatura considerando tarifa convencional e bandeira vermelha II
    data_list_comp2_conv_red2 = BillConventionalTariff(data_list_energy_hour, 'B1_1', False, 3)

    # cálculo da fatura considerando tarifa branca e bandeira escassez hídrica (ws: water scarcity)
    data_list_comp2_white_ws = BillWhiteTariff(data_list_energy_hour, 'EH')
    # cálculo da fatura considerando tarifa convencional e bandeira escassez hídrica
    data_list_comp2_conv_ws = BillConventionalTariff(data_list_energy_hour, 'B1_1', False, 4)


    """
    Montagem das listas finais
    """
    # curvas de tarifas
    tariff_profile = [{'t': val[0], 'white_offpeak': val[1], 'white_intermediate': val[2], 'white_peak': val[3], 'conventional': val[4]} for val in data_list_tariffs]

    # curva de consumo horários de um determinado dia
    daily_kw = [{'t': val[0], 'kw_tot': val[1], 'highlight_interm': val[2], 'highlight_peak': val[3]} for val in consumption_daily]

    # curva típica de consumo
    typical_kw = [{'t': val[0], 'kw_tot': val[1], 'highlight_interm': val[2], 'highlight_peak': val[3]} for val in typical_consumption]

    # definir os estados dos checkboxes de dias da semana e estações do ano
    json_days_filter, json_seasons_filter = DaysSeasonsConsider(days_consider, seasons_consider)

    # dados relativos à comparação de tarifas da aba 4 (Comparação de tarifas sem bandeiras)
    json_comparison_white = [{'description': v[0], 'kwh': v[1], 'tariff': v[2], 'cost_energy': v[3],
                             'icms': v[4], 'cost_icms': v[5], 'total': v[6]} for v in data_list_comp1_white]
    json_comparison_conventional = [{'description': v[0], 'kwh': v[1], 'tariff': v[2], 'cost_energy': v[3],
                                     'icms': v[4], 'cost_icms': v[5], 'total': v[6]} for v in data_list_comp1_conv]
    # resumo
    json_results_comparison = {'tot_white': total_white, 'tot_conv': total_conventional, 'diff': total_difference}
    # gráfico de pizza
    json_results_comparison_kwh = [{'period': v[0], 'value': v[1]} for v in data_list_pie_kwh]

    # dados relativos à comparação de tarifas aba 5 (Comparação de tarifas com bandeiras)
    json_comparison2_white = []
    for i in range(len(data_list_comp2_white_green)):
        desc = data_list_comp2_white_green[i][0]
        tot_green = CurrencyFormatBrazil(data_list_comp2_white_green[i][6])
        tot_yellow = CurrencyFormatBrazil(data_list_comp2_white_yellow[i][6])
        tot_red1 = CurrencyFormatBrazil(data_list_comp2_white_red1[i][6])
        tot_red2 = CurrencyFormatBrazil(data_list_comp2_white_red2[i][6])
        tot_ws = CurrencyFormatBrazil(data_list_comp2_white_ws[i][6])
        json_comparison2_white.append({'description': desc, 'total_green': tot_green, 'total_yellow': tot_yellow,
                                       'total_red1': tot_red1, 'total_red2': tot_red2, 'total_ws': tot_ws})
    json_comparison2_conventional = []
    for i in range(len(data_list_comp2_conv_green)):
        desc = data_list_comp2_conv_green[i][0]
        tot_green = CurrencyFormatBrazil(data_list_comp2_conv_green[i][6])
        tot_yellow = CurrencyFormatBrazil(data_list_comp2_conv_yellow[i][6])
        tot_red1 = CurrencyFormatBrazil(data_list_comp2_conv_red1[i][6])
        tot_red2 = CurrencyFormatBrazil(data_list_comp2_conv_red2[i][6])
        tot_ws = CurrencyFormatBrazil(data_list_comp2_conv_ws[i][6])
        json_comparison2_conventional.append({'description': desc, 'total_green': tot_green, 'total_yellow': tot_yellow,
                                              'total_red1': tot_red1, 'total_red2': tot_red2, 'total_ws': tot_ws})


    # dados para preenchimento de gráficos de barra da comparação 2
    json_comparison2_barCharts = []
    green = data_list_comp2_conv_green[0][6]
    yellow = data_list_comp2_conv_yellow[0][6]
    red1 = data_list_comp2_conv_red1[0][6]
    red2 = data_list_comp2_conv_red2[0][6]
    ws = data_list_comp2_conv_ws[0][6]
    json_comparison2_barCharts.append({'tariff': 'Convencional', 'cost_green': green, 'cost_yellow': yellow, 'cost_red1': red1, 'cost_red2': red2, 'cost_ws': ws})
    green = data_list_comp2_white_green[3][6]
    yellow = data_list_comp2_white_yellow[3][6]
    red1 = data_list_comp2_white_red1[3][6]
    red2 = data_list_comp2_white_red2[3][6]
    ws = data_list_comp2_white_ws[3][6]
    json_comparison2_barCharts.append({'tariff': 'Branca', 'cost_green': green, 'cost_yellow': yellow, 'cost_red1': red1, 'cost_red2': red2, 'cost_ws': ws})



    """
    Criação das variáveis de contexto para montagem da página HTML
    """
    context = {
        'meters_list': meters_list,
        'installations_meters': installations_meters,
        'meter': meter,
        'tariff_profile': tariff_profile,
        'daily_kw': daily_kw,
        'typical_kw': typical_kw,
        'json_comparison_white': json_comparison_white,  # dados da tabela 1 da comparação 1
        'json_comparison_conventional': json_comparison_conventional,  # dados da tabela 2 da comparação 1
        'json_results_comparison': json_results_comparison,  # dados de resumo da comparação 1
        'json_results_comparison_kwh': json_results_comparison_kwh,  # dados do gráfico de pizza da comparação 1
        'json_comparison2_white': json_comparison2_white,  # totais de tarifa branca da comparação 2
        'json_comparison2_conventional': json_comparison2_conventional,  # totais de tarifa conv. da comparação 2
        'json_comparison2_barCharts': json_comparison2_barCharts,
        'json_days_filter': json_days_filter,
        'json_seasons_filter': json_seasons_filter,
        'datetime_kwh_daily': datetime_kwh_daily.strftime('%Y-%m-%d'),
        'datetime_daily_ini_min': datetime_ini_min.strftime('%Y-%m-%d'),
        'datetime_daily_fin_max': datetime_fin_max.strftime('%Y-%m-%d'),
        'datetime_ini': datetime_ini.strftime('%Y-%m-%dT%H:%M'),
        'datetime_fin': datetime_fin.strftime('%Y-%m-%dT%H:%M'),
        'datetime_ini_min': datetime_ini_min.strftime('%Y-%m-%dT%H:%M'),
        'datetime_fin_max': datetime_fin_max.strftime('%Y-%m-%dT%H:%M'),
        'interval_minutes': 5,
        'step_minutes_options': [5, 30, 60, 120, 180, 240, 300, 360, 720, 1440]
    }
    response = render(request, 'argos/' + editionName + '/whitetariff.html', context)
    return response




@login_required
def detail(request, eui):
    """
    Cada dispositivo possui o tipo do servidor ao qual está associado (Local-1,
    Orbiwise-2, IMT-3 ou Daimon-4). Assim, dependendo do tipo do servidor do
    dispositivo selecionado, monta-se o comando REST API específico.
    Aqui deve-se pegar todos os payloads do dev_eui selecionado para criar a
    página com o gráfico e a tabela, conforme tipo de dispositivo.
    """
    editionName = settings.APP_CONFIG['edition'].lower()

    #verifica se o request é POST
    if request.POST:
        #request POST: foi chamado por filterDate() com um form preenchido pelo usuário
        #cria form para obter data inicial e data final de pesquisa
        form = DateFilterForm(request.POST)
        datetime_ini = form['datetime_ini'].value()
        datetime_fin = form['datetime_fin'].value()
        #converte strings para datetime
        datetime_ini = datetime.strptime(datetime_ini, ('%Y-%m-%dT%H:%M'))
        datetime_fin = datetime.strptime(datetime_fin, ('%Y-%m-%dT%H:%M'))
        #insere time zone
        datetime_ini = pytz.timezone(settings.TIME_ZONE).localize(datetime_ini)
        datetime_fin = pytz.timezone(settings.TIME_ZONE).localize(datetime_fin)

    else:
        #request GET: cria form vazio e determina data atual e 24 h para trás
        #cria form para editar data inicial e data final de pesquisa
        form = DateFilterForm()
        #inicia data inicial e final
        datetime_ini = None
        datetime_fin = None

    #obtém dispositivo selecionado pelo usuário
    device = LoraDevice.objects.get(eui__exact = eui)
    #obtém lista de tipos de dispositivos, dispositivos e gateways
    device_types_tup, devices_tup, gateways_tup = AllObjects(request)

    #determina número de registros a ser recuperado via REST API
    if datetime_ini != None:
        #calcula quantidade de minutos da data inicial até agora
        since_datetime_ini = round((timezone.now() - datetime_ini).total_seconds()/60)
        if device.device_type.interval > 0:
            num_logs = round(since_datetime_ini / device.device_type.interval)
        else:
            num_logs = 100 #default
    else:
        #calcula quantidade de minutos para as últimas 24 h
        if device.device_type.interval > 0:
            num_logs = round(24*60 / device.device_type.interval)
        else:
            num_recs = 100 #default

    """
    Avalia o modo de recuperação dos dados.
    """
    if settings.APP_CONFIG['data_mode'] == 'local':
        #recuperação do banco de dados próprio
        myData_dict = GetFromLocal(device, datetime_ini, datetime_fin)

    else:
        """
        Recuperação do banco de dados do servidor remoto.
        Avalia o servidor.
        """
        if device.server.server_id == 1:
            """
            Servidor Local (somente dispositivo para teste - tipo 3 - sensor temperatura)
            """
            myData_dict = GetFromLocal(device, datetime_ini, datetime_fin)

        elif  device.server.server_id == 2:
            """
            Servidor Orbiwise
            """
            myData_dict = GetFromOrbiwise(device)

        elif  device.server.server_id == 3:
            """
            Servidor Mauá
            """
            myData_dict = GetFromMaua(device, num_logs, datetime_ini, datetime_fin)

        elif  device.server.server_id == 4:
            """
            Servidor Daimon
            """
            myData_dict = GetFromLocal(device, datetime_ini, datetime_fin)
            # TO DO: implementar GetFromDaimon()  em substituição a GetFromLocal()
            #após descobrir como funciona REST API do Chirpstack
            #myData_dict = GetFromDaimon()

    #obtém data inicial e final dos dados recuperados
    if (len(myData_dict['logs']) > 1):
        if (datetime_ini == None and datetime_fin == None):
            datetime_ini = myData_dict['logs'][0]['datetime_rx']
            datetime_fin = myData_dict['logs'][len(myData_dict['logs'])-1]['datetime_rx']
            # obtém datas no time zone correspondente
            datetime_ini = datetime_ini.astimezone(pytz.timezone(settings.TIME_ZONE))
            datetime_fin = datetime_fin.astimezone(pytz.timezone(settings.TIME_ZONE))
    else:
        #obtém data/hora atual e 24 h para trás, inserindo time zone
        datetime_fin = timezone.now()
        datetime_ini = datetime_fin + timedelta(days=-1)

    """
    Avalia o tipo de dispositivo
    """
    if device.device_type.type_id == 1:
        """
        Dispositivo do tipo 1-sensor de tensão e corrente
        """
        #inicia listas
        dp_list = []
        dp_list_hex = []
        va_list = []
        ia_list = []
        vb_list = []
        ib_list = []
        vc_list = []
        ic_list = []

        if myData_dict['data_format'] == 'base64':
            #converte todos os data payloads para hexa
            myData_dict['logs'] = [{
                'datetime_rx': obj['datetime_rx'],
                'data_payload': base64.b64decode(obj['data_payload']).hex().upper(),
                'snr': obj['snr'],
                'rssi': obj['rssi']
                } for obj in myData_dict['logs']]

        #converte payloads, separando os campos pela vírgula
        dp_list = [bytes.fromhex(obj['data_payload']).decode().split(',') for obj in myData_dict['logs']]
        #converte payloads de base64 para hexa
        dp_list_hex = [obj['data_payload'] for obj in myData_dict['logs']]
        #monta listas convertendo de ASCII para float
        for dp in dp_list:
            va_list.append(float(dp[1]))
            ia_list.append(float(dp[2]))
            vb_list.append(float(dp[3]))
            ib_list.append(float(dp[4]))
            vc_list.append(float(dp[5]))
            ic_list.append(float(dp[6]))
            #end for

        #extrai itens de data
        date_list = [obj['datetime_rx'] for obj in myData_dict['logs']]
        date_list2 = date_list.copy()
        #proteção contra lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            date_list.pop(0)
            date_list2.pop()
            dp_list_hex.pop(0)
            va_list.pop(0)
            ia_list.pop(0)
            vb_list.pop(0)
            ib_list.pop(0)
            vc_list.pop(0)
            ic_list.pop(0)

        """
        Calcula o tempo decorrido desde o último pacote enviado.
        """
        interval_list = []
        #proteção contra lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            for i, j in zip(date_list, date_list2):
                time_diff = i - j
                minutes = time_diff.total_seconds()/60
                interval_list.append(minutes)
        else:
            interval_list = [0, 0]

        #zipa listas
        data_list = list(zip(date_list, va_list, ia_list, vb_list, ib_list,
                             vc_list, ic_list, interval_list, dp_list_hex))
        #cria dicionário
        values_dict = [{'datetime_rx':v[0].astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
                        'va':v[1], 'vb':v[3], 'vc':v[5], 'ia':v[2], 'ib':v[4],
                        'ic':v[6], 'interval':v[7], 'data_payload':v[8]} for v in data_list]
        #cria variável de contexto
        context = {
            'device': device,
            'values': json.dumps(values_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            'datetime_ini' : datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin' : datetime_fin.strftime('%Y-%m-%dT%H:%M')
            }
        response =  render(request, 'argos/' + editionName + '/detail1.html', context)
        #end tipo 1

    elif device.device_type.type_id == 2:
        """
        Dispositivo do tipo 2-remota para medidor de energia
        """
        #extrai horários, payloads e pulsos
        pulseC_list = []
        pulseC_list2 = []
        pulseG_list = []
        pulseG_list2 = []
        lid_list = []
        status_list = []
        card_list = []
        batl_list = []
        snr_list = []
        rssi_list = []

        if myData_dict['data_format'] == 'base64':
            #converte todos os data payloads para hexa
            myData_dict['logs'] = [{
                'datetime_rx': obj['datetime_rx'],
                'data_payload': base64.b64decode(obj['data_payload']).hex().upper(),
                'snr': obj['snr'],
                'rssi': obj['rssi']
                } for obj in myData_dict['logs']]

        """
        Até 19/12/2019 os pacotes possuíam 23 bytes (46 caracteres). Nesse
        dia, a Mauá fez uma mudança no pacote, que passou a ter 25 bytes
        (50 caracteres). Dessa forma, para manter a compatibilidade com o
        histórico, é preciso verificar o tamanho do payload antes de extrair
        os dados.
        """
        for obj in myData_dict['logs']:
            if len(obj['data_payload']) == 46:
                pulseC_list.append(float.fromhex(obj['data_payload'][2:8]))
                pulseG_list.append(float.fromhex(obj['data_payload'][10:16]))
                lid_list.append(float.fromhex(obj['data_payload'][18:22]))
                status_list.append(float.fromhex(obj['data_payload'][24:28]))
                card_list.append(obj['data_payload'][30:40])
                batl_list.append(float.fromhex(obj['data_payload'][42:46])/1000)
            elif len(obj['data_payload']) == 50:
                pulseC_list.append(float.fromhex(obj['data_payload'][2:10]))
                pulseG_list.append(float.fromhex(obj['data_payload'][12:20]))
                lid_list.append(float.fromhex(obj['data_payload'][22:26]))
                status_list.append(float.fromhex(obj['data_payload'][28:32]))
                card_list.append(obj['data_payload'][34:44])
                batl_list.append(float.fromhex(obj['data_payload'][46:50])/1000)
            #end for

        pulseC_list2 = pulseC_list.copy()
        pulseG_list2 = pulseG_list.copy()

        date_list = [obj['datetime_rx'] for obj in myData_dict['logs']]
        date_list2 = date_list.copy()
        dp_list = [obj['data_payload'] for obj in myData_dict['logs']]
        snr_list = [obj['snr'] for obj in myData_dict['logs']]
        rssi_list = [obj['rssi'] for obj in myData_dict['logs']]
        #proteção contra lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            date_list.pop(0)
            date_list2.pop()
            dp_list.pop(0)
            pulseC_list.pop(0)
            pulseC_list2.pop()
            pulseG_list.pop(0)
            pulseG_list2.pop()
            lid_list.pop(0)
            status_list.pop(0)
            card_list.pop(0)
            batl_list.pop(0)
            snr_list.pop(0)
            rssi_list.pop(0)

        """
        A constante do medidor é 2000, mas convertido para Wh é 2. Para
        encontrar a demanda média em W, divide-se a energia em Wh pela
        fração de hora do intervalo de medição, que deve ser calculado a
        partir dos próprios dados.
        A constante do medidor ainda precisa ser parametrizada no modelo de
        dados.
        Além disso, os dados precisam ser tratados, pois quando se pega um
        período maior, em vários intervalos o valor dos pulsos é zero.
        """
        demC_list = []
        demG_list = []
        interval_list = []
        #proteção contra lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            #cálculo de demanda consumida e intervalo decorrido desde o último pacote
            for i, j, k, l in zip(pulseC_list, pulseC_list2, date_list, date_list2):
                if i >= 0 and j >= 0:
                    time_diff = k - l
                    minutes = time_diff.total_seconds()/60
                    interval_list.append(minutes)
                    if minutes != 0.0:
                        demC_list.append(round(((i-j)/2)/(minutes/60), 1))
                    else:
                        demC_list.append(0.0)
                else:
                    interval_list.append(0.0)
                    demC_list.append(0.0)

            #cálculo de demanda gerada
            for i, j, k in zip(pulseG_list, pulseG_list2, interval_list):
                if i >= 0 and j >= 0 and k > 0:
                    demG_list.append(round(((i-j)/2)/(k/60), 1))
                else:
                    demG_list.append(0.0)

        else:
            demC_list = [0, 0]
            demG_list = [0, 0]
            interval_list = [0, 0]

        """
        índice  0: horário
        índice  1: demanda consumida [w]
        índice  2: pulsos de energia consumida
        índice  3: demanda gerada [w]
        índice  4: pulsos de energia gerada
        índice  5: estado da tampa (aberta ou fechada)
        índice  6: estado do contator (ligado ou desligado)
        índice  7: código RFID recebido
        índice  8: nível da bateria [V]
        índice  9: intervalo desde o último envio [min]
        índice 10: payload referente aos pulsos
        """
        #zipa listas
        data_list = list(zip(date_list, demC_list, pulseC_list, demG_list,
                             pulseG_list, lid_list, status_list, card_list,
                             batl_list, interval_list, dp_list, snr_list,
                             rssi_list))
        #cria dicionário de valores para plotar
        values_dict = [{'datetime_rx': v[0].astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
                        'demC':v[1], 'pulseC':v[2], 'demG':v[3], 'pulseG':v[4],
                        'lid':v[5], 'status':v[6], 'card_code':v[7], 'batl':v[8],
                        'interval':v[9], 'data_payload': v[10],
                        'snr':v[11], 'rssi':v[12]} for v in data_list]
        #cria variável de contexto
        context = {
            'device': device,
            'values': json.dumps(values_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            'datetime_ini' : datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin' : datetime_fin.strftime('%Y-%m-%dT%H:%M')
            }
        response =  render(request, 'argos/' + editionName + '/detail2.html', context)
        #end tipo 2

    elif device.device_type.type_id == 3:
        """
        Dispositivo do tipo 3-sensor de temperatura
        """
        if myData_dict['data_format'] == 'base64':
            #converte todos os data payloads para decimal
            myData_dict['logs'] = [{
                'datetime_rx': obj['datetime_rx'],
                'data_payload': base64.b64decode(obj['data_payload']).decode(),
                'snr': obj['snr'],
                'rssi': obj['rssi']
                } for obj in myData_dict['logs']]

        #monta listas de dados
        date_list = [obj['datetime_rx'] for obj in myData_dict['logs']]
        temp_list = [obj['data_payload'] for obj in myData_dict['logs']]
        #zipa listas
        values = list(zip(date_list, temp_list, temp_list))
        #cria dicionário
        values_dict = [{'datetime_rx':v[0].strftime('%d/%m/%Y %H:%M:%S'),
                        'temp':v[1], 'data_payload':v[2]} for v in values]
        #cria variável de contexto
        context = {
            'device': device,
            'values': json.dumps(values_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            'datetime_ini' : datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin' : datetime_fin.strftime('%Y-%m-%dT%H:%M')
            }
        response =  render(request, 'argos/' + editionName + '/detail3.html', context)
        #end tipo 3

    elif device.device_type.type_id == 4:
        """
        Dispositivo do tipo 4-rastreador GPS
        """
        #filtra lista de coordenadas, calcula sua média e monta dicionário com dados do mapa de calor
        center_float, heatData_dict = FilterGPSLogs(myData_dict)

        #Lista para armazenar arquivos .json já abertos
        geojsonDataCities = []
        for geojs_filename in settings.APP_CONFIG['layers']:
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), geojs_filename)) as f:
                geojsonDataCities.append(json.load(f))
            f.close()

        #lê todos os gateways
        gateways, groupsGw_str, gwDesc_list = zip(*gateways_tup)
        latlong_str = [gw.latlong.split(',') for gw in gateways]
        latlong_float = [[float(ll[0]), float(ll[1])] for ll in latlong_str]
        data_list = list(zip(gateways, latlong_float))
        #cria dicionário
        gateways_dict = [{'desc':obj[0].desc, 'gateway_id':obj[0].gateway_id, 'brand':obj[0].brand, 'model':obj[0].model, 'latlong':obj[1] } for obj in data_list]

        #recalcula coordenada central se necessário
        if center_float == [0.0, 0.0]:
            lat_float = [ll[0] for ll in latlong_float]
            long_float = [ll[1] for ll in latlong_float]
            if len(latlong_float) > 0:
                center_float = [statistics.mean(lat_float), statistics.mean(long_float)]
            else:
                center_float = [0.0, 0.0]

        #cria variável de contexto
        context = {
            'form': form,
            'datetime_ini': datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin': datetime_fin.strftime('%Y-%m-%dT%H:%M'),
            'device': device,
            'geojsonDataCities': geojsonDataCities,
            'latlong': center_float,
            'gateways': json.dumps(gateways_dict),
            'heatData': json.dumps(heatData_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            }

        response =  render(request, 'argos/' + editionName + '/detail4.html', context)
        #end tipo 4

    elif device.device_type.type_id == 5:
        """
        Dispositivo do tipo 5-sensor de temperatura e umidade
        """
        if myData_dict['data_format'] == 'base64':
            #converte todos os data payloads para decimal
            myData_dict['logs'] = [{
                'datetime_rx': obj['datetime_rx'],
                'data_payload': base64.b64decode(obj['data_payload']).hex().upper(),
                'snr': obj['snr'],
                'rssi': obj['rssi']
                } for obj in myData_dict['logs']]


        temp_list = [float.fromhex(obj['data_payload'][2:6])/10 for obj in myData_dict['logs']]
        humid_list = [float.fromhex(obj['data_payload'][8:12])/10 for obj in myData_dict['logs']]
        batl_list = [float.fromhex(obj['data_payload'][14:18])/1000 for obj in myData_dict['logs']]
        date_list = [obj['datetime_rx'] for obj in myData_dict['logs']]
        date_list2 = date_list.copy()
        dp_list = [obj['data_payload'] for obj in myData_dict['logs']]
        snr_list = [obj['snr'] for obj in myData_dict['logs']]
        rssi_list = [obj['rssi'] for obj in myData_dict['logs']]
        #proteção contra lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            date_list.pop(0)
            date_list2.pop()
            dp_list.pop(0)
            temp_list.pop(0)
            humid_list.pop(0)
            batl_list.pop(0)
            snr_list.pop(0)
            rssi_list.pop(0)

        """
        Calcula o tempo decorrido desde o último pacote enviado.
        """
        interval_list = []
        #proteção contra lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            for i, j in zip(date_list, date_list2):
                time_diff = i - j
                minutes = time_diff.total_seconds()/60
                interval_list.append(minutes)
        else:
            interval_list = [0, 0]

        #zipa listas
        data_list = list(zip(date_list, temp_list, humid_list, batl_list,
                             interval_list, dp_list, snr_list, rssi_list))
        #cria dicionário de valores para plotar
        values_dict = [{'datetime_rx':v[0].astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
                        'temp':v[1], 'humid':v[2], 'batl':v[3],
                        'interval':v[4], 'data_payload':v[5], 'snr':v[6],
                        'rssi':v[7]} for v in data_list]
        #cria variável de contexto
        context = {
            'device': device,
            'values': json.dumps(values_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            'datetime_ini' : datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin' : datetime_fin.strftime('%Y-%m-%dT%H:%M')
            }
        response =  render(request, 'argos/' + editionName + '/detail5.html', context)
        #end tipo 5
    
    elif device.device_type.type_id == 6:
        """
        Dispositivo do tipo 6-Chave Fusível
        """
        batl_list = []
        interval_list = []
        fuseCurrent1 = []
        fuseCurrent2 = []
        fuseCurrent3 = []
        voltageDetection = []
        voltageDetectionValue = []
        payloadHex_list = []
        setValue1 = 450
        setValue2 = 460
        setValue3 = 480
        
        #Payloas Exemplo = '0D0FEF0D0FEF0D0FF10D07C00C0CD3'
        #Corrente 1-> [2:6]
        #Corrente 2-> [8:12]
        #Corrente 3-> [14:18]
        #Detecção de tensão-> [20:24]
        #Bateria-> [26:30]

        if myData_dict['data_format'] == 'base64':
            #converte todos os data payloads para decimal
            myData_dict['logs'] = [{
                'datetime_rx': obj['datetime_rx'],
                'data_payload': base64.b64decode(obj['data_payload']).hex().upper(),
                'snr': obj['snr'],
                'rssi': obj['rssi']
                } for obj in myData_dict['logs']]
        

        for obj in myData_dict['logs']:
            payloadHex_list.append(obj['data_payload'])
            #Preenche lista para corrente no fusível 1
            Temp = float.fromhex(obj['data_payload'][2:6])
            if( (Temp - setValue1) < 0 ):
                fuseCurrent1.append(0)
            else:
                fuseCurrent1.append(  (Temp - setValue1)/150  )
            
            #Preenche lista para corrente no fusível 2
            Temp = float.fromhex(obj['data_payload'][8:12])
            if( (Temp - setValue2) < 0 ):
                fuseCurrent2.append(0)
            else:
                fuseCurrent2.append(  (Temp - setValue2)/150  )

            #Preenche lista para corrente no fusível 3
            Temp = float.fromhex(obj['data_payload'][14:18])
            if( (Temp - setValue3) < 0 ):
                fuseCurrent3.append(0)
            else:
                fuseCurrent3.append(  (Temp - setValue3)/150  )

            #Preenche lista para detecção de tensão
            Temp = float.fromhex(obj['data_payload'][20:24])
            voltageDetectionValue.append(Temp)
            if( Temp > 3600 or Temp < 500 ):
                voltageDetection.append("OFF")
            else:
                voltageDetection.append("ON")

            #Preenche lista para bateria
            if len(obj['data_payload']) == 30:
                batl_list.append(float.fromhex(obj['data_payload'][26:30])/1000)

        date_list = [obj['datetime_rx'] for obj in myData_dict['logs']]
        date_list2 = date_list.copy()
        snr_list = [obj['snr'] for obj in myData_dict['logs']]
        rssi_list = [obj['rssi'] for obj in myData_dict['logs']]

        #proteção conta lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            date_list.pop(0)
            date_list2.pop()
            snr_list.pop(0)
            rssi_list.pop(0)
            batl_list.pop(0)
            fuseCurrent1.pop(0)
            fuseCurrent2.pop(0)
            fuseCurrent3.pop(0)
            payloadHex_list.pop(0)
            #cálculo de intervalo decorrido desde o último pacote
            for k, l in zip(date_list, date_list2):
                time_diff = k - l
                minutes = time_diff.total_seconds()/60
                interval_list.append(minutes)
        else:
            interval_list = [0,0]

        #zipa listas
        data_list = list(zip(date_list,snr_list,rssi_list,batl_list,interval_list,
                            fuseCurrent1,fuseCurrent2,fuseCurrent3,voltageDetection,
                            voltageDetectionValue,payloadHex_list))

        #cria dict de valores para plotar
        values_dict = [{
            'datetime_rx': v[0].astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
            'snr': v[1],
            'rssi': v[2],
            'batl':v[3],
            'interval':v[4],
            'cf1':v[5],
            'cf2':v[6],
            'cf3':v[7],
            'voltDetec':v[8],
            'voltDetecValue':v[9],
            'payloadHex':v[10],
        } for v in data_list]

        
        #cria variável de contexto
        context = {
            'device': device,
            'values': json.dumps(values_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            'datetime_ini' : datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin' : datetime_fin.strftime('%Y-%m-%dT%H:%M')
            }

        response =  render(request, 'argos/' + editionName + '/detail6.html', context)

    elif device.device_type.type_id == 7:
        """
        Dispositivo do tipo 7-Corrente MT
        """
        #batl_list = []
        interval_list = []
        phaseCurrentA = []
        phaseCurrentB = []
        phaseCurrentC = []
        temperatureValue = []
        payloadHex_list = []

        if myData_dict['data_format'] == 'base64':
            #converte todos os data payloads para decimal
            myData_dict['logs'] = [{
                'datetime_rx': obj['datetime_rx'],
                'data_payload': base64.b64decode(obj['data_payload']).hex().upper(),
                'snr': obj['snr'],
                'rssi': obj['rssi']
                } for obj in myData_dict['logs']]
        
        for obj in myData_dict['logs']:
            if(len(obj['data_payload']) >= 22):
                payloadHex_list.append(obj['data_payload'])
                #Preenche lista para corrente fase A
                phaseCurrentA.append((float.fromhex(obj['data_payload'][0:4]))/1000)
                #Preenche lista para corrente fase B
                phaseCurrentB.append((float.fromhex(obj['data_payload'][4:8]))/1000)
                #Preenche lista para corrente fase C
                phaseCurrentC.append((float.fromhex(obj['data_payload'][8:12]))/1000)
                #Preenche lista para temperatura
                temperatureValue.append((float.fromhex(obj['data_payload'][20:22]))*0.25+5)
                #Preenche lista para bateria
                #batl_list.append(float.fromhex(obj['data_payload'][18:20])*2.4+900)

        date_list = [obj['datetime_rx'] for obj in myData_dict['logs']]
        date_list2 = date_list.copy()
        snr_list = [obj['snr'] for obj in myData_dict['logs']]
        rssi_list = [obj['rssi'] for obj in myData_dict['logs']]

        #proteção conta lista com menos de 2 objetos
        if len(myData_dict['logs']) >= 2:
            date_list.pop(0)
            date_list2.pop()
            snr_list.pop(0)
            rssi_list.pop(0)
            #batl_list.pop(0)
            phaseCurrentA.pop(0)
            phaseCurrentB.pop(0)
            phaseCurrentC.pop(0)
            temperatureValue.pop(0)
            payloadHex_list.pop(0)
            #cálculo de intervalo decorrido desde o último pacote
            for k, l in zip(date_list, date_list2):
                time_diff = k - l
                minutes = time_diff.total_seconds()/60
                interval_list.append(minutes)
        else:
            interval_list = [0,0]

        #zipa listas
        data_list = list(zip(date_list,snr_list,rssi_list,interval_list,
                            phaseCurrentA,phaseCurrentB,phaseCurrentC,temperatureValue,payloadHex_list))

        #cria dict de valores para plotar
        values_dict = [{
            'datetime_rx': v[0].astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%d/%m/%Y %H:%M:%S'),
            'snr': v[1],
            'rssi': v[2],
            'interval':v[3],
            'phaseCA':v[4],
            'phaseCB':v[5],
            'phaseCC':v[6],
            'temp':v[7],
            'payloadHex':v[8],
        } for v in data_list]

        
        #cria variável de contexto
        context = {
            'device': device,
            'values': json.dumps(values_dict),
            'device_type_list': device_types_tup,
            'device_list': devices_tup,
            'gateway_list': gateways_tup,
            'datetime_ini' : datetime_ini.strftime('%Y-%m-%dT%H:%M'),
            'datetime_fin' : datetime_fin.strftime('%Y-%m-%dT%H:%M')
            }

        response =  render(request, 'argos/' + editionName + '/detail7.html',context)

    return response


@login_required
def devlist(request):
    # obtém lista de tipos de dispositivos, dispositivos e gateways
    device_types_tup, devices_tup, gateways_tup = AllObjects(request)

    editionName = settings.APP_CONFIG['edition'].lower()

    return render(request, 'argos/'+ editionName +'/devlist.html', {
        'device_type_list': device_types_tup,
        'device_list': devices_tup,
        'gateway_list': gateways_tup,
    })


@api_view(['POST'])
def emergency_credit(request):
    """
    Cria uma transação de crédito de emergência para uma instalação.
    """
    emergency_value = 30;

    #obtém objeto instalação para o código enviado
    installation_list = Installation.objects.filter(code__exact = request.data['installation_code'])
    #verifica se existe instalação com esse código
    if len(installation_list) == 0:
        return Response(status = status.HTTP_404_NOT_FOUND)

    #obtém lista de transações de crédito de emergência da instalação
    emerg_trans_list = Transaction.objects.filter(action__exact = 'Emergency Credit',
        installation_code__exact = request.data['installation_code']
        ).order_by('-datetime_rx')
    #obtém lista de transações da instalação, excluindo as de ligar e desligar
    trans_list = Transaction.objects.filter(installation_code__exact = request.data['installation_code']
        ).exclude(action__exact = 'Turn On'
        ).exclude(action__exact = 'Turn Off').order_by('-datetime_rx')
    #se a lista de transações de crédito de emergência não está vazia
    if len(emerg_trans_list) != 0:
        #apenas realiza novo crédito de emergência se o último foi há mais de 30 dias
        tdelta = timezone.now() - emerg_trans_list[0].datetime_rx
        if (tdelta.days > 30):
            #calcula o novo saldo após o crédito
            if (len(trans_list) > 0):
                energy_account = trans_list[0].energy_account + emergency_value
            else:
                energy_account = emergency_value
        else:
            return Response(status = status.HTTP_409_CONFLICT)
    else:
        #calcula o novo saldo após o crédito
        if (len(trans_list) > 0):
            energy_account = trans_list[0].energy_account + emergency_value
        else:
            energy_account = emergency_value

    #cria objeto transação
    tr = Transaction(datetime_rx=timezone.now(),
    installation_code=installation_list[0].code,
    energy_value=emergency_value, energy_account=energy_account,
    action='Emergency Credit', installation=installation_list[0])
    #cria serializador
    serializer = TransactionSerializer(tr)
    #salva transação no banco de dados
    tr.save()
    return Response(serializer.data, status = status.HTTP_201_CREATED)


@login_required
def filterDate(request):
    #aqui o request sempre será POST e é para obter o dev_eui
    form = DateFilterForm(request.POST)
    device_eui = form['device_eui'].value()

    return(detail(request, device_eui))


@login_required
def geomap(request, gateway_id):
    # obtém lista de tipos de dispositivos, dispositivos e gateways
    device_types_tup, devices_tup, gateways_tup = AllObjects(request)

    #lê gateway a ser exibido no centro do geomapa
    gateway = Gateway.objects.get(gateway_id__exact = gateway_id)
    center_str = gateway.latlong.split(',')
    center_float = [float(ll) for ll in center_str]

    #obtém lista de gateways
    gateways, groupsGw_str, gwDesc_list = zip(*gateways_tup)
    gateways = list(gateways)
    latlong_str = [gw.latlong.split(',') for gw in gateways]
    latlong_float = [[float(ll[0]), float(ll[1])] for ll in latlong_str]
    data_list = list(zip(gateways, latlong_float))

    #cria dicionário
    gateways_dict = [{'desc':obj[0].desc, 'gateway_id':obj[0].gateway_id, 'brand':obj[0].brand, 'model':obj[0].model, 'latlong':obj[1] } for obj in data_list]

    #obtém lista de GPSs
    devices, groupsDev_str, devDesc_list = zip(*devices_tup)
    devices = list(devices)
    gps_list = [dev for dev in devices if dev.device_type.type_id == 4]

    """
    Obtém leitura de todos os GPSs da lista
    """
    #determina número de registros a ser recuperado via REST API
    num_logs = 100 #default
    if gps_list[0].device_type.interval > 0:
        num_logs = round(24*60 / gps_list[0].device_type.interval)

    #varre lista de GPSs
    log_list = []
    for gps in gps_list:
        """
        Avalia o modo de recuperação dos dados.
        """
        if settings.APP_CONFIG['data_mode'] == 'local':
            #recuperação do banco de dados próprio
            myData_dict = GetFromLocal(gps)

        else:
            """
            Recuperação do banco de dados do servidor remoto.
            Avalia o servidor.
            """
            if  gps.server.server_id == 3:
                """
                Servidor Mauá
                """
                myData_dict = GetFromMaua(gps, num_logs)

            elif  gps.server.server_id == 4:
                """
                Servidor Daimon
                """
                myData_dict = GetFromLocal(gps)
                # TO DO: implementar GetFromDaimon()  em substituição a GetFromLocal()
                #após descobrir como funciona REST API do Chirpstack
                #myData_dict = GetFromDaimon()
            #endif
        #endif
        log_list += myData_dict['logs']
    #endfor

    myData_dict = {
        'data_format': myData_dict['data_format'],
        'device_eui': myData_dict['device_eui'],
        'device_type': myData_dict['device_type'],
        'server': myData_dict['server'],
        'logs': log_list
        }

    #filtra lista de coordenadas, calcula sua média e monta dicionário com dados do mapa de calor
    temp, heatData_dict = FilterGPSLogs(myData_dict)

    #Lista para armazenar arquivos .json já abertos
    geojsonDataCities = []
    for geojs_filename in settings.APP_CONFIG['layers']:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), geojs_filename)) as f:
            geojsonDataCities.append(json.load(f))
        f.close()

    editionName = settings.APP_CONFIG['edition'].lower()

    context = {
        'geojsonDataCities': geojsonDataCities,
        'latlong': center_float,
        'gateways': json.dumps(gateways_dict),
        'heatData': json.dumps(heatData_dict),
        'device_type_list': device_types_tup,
        'device_list': devices_tup,
        'gateway_list': gateways_tup,
        }
    response = render(request, 'argos/' + editionName + '/geomap.html', context)

    return response


@api_view(['GET'])
def get_user(request, username):
    """
    Retorna objeto User com o user name passado
    """
    try:
        user = User.objects.get(username__exact = username)
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(status = status.HTTP_404_NOT_FOUND)


def home(request):
    editionName = settings.APP_CONFIG['edition'].lower()
    return render(request, 'argos/' + editionName + '/home.html')


@api_view(['GET'])
def installation_exists(request, installation_code):
    """
    Verifica se uma instalação específica está cadastrada no banco de dados.
    """

    #busca instalação no banco
    installation_list = Installation.objects.filter(code__exact = installation_code)

    #proteção: verifica se a lista está vazia
    if len(installation_list) == 0:
        return Response(status = status.HTTP_404_NOT_FOUND)

    #a lista não está vazia: responde com status ok
    return Response(status = status.HTTP_200_OK)


@api_view(['GET'])
def loadprofile(request, installation_code):
    """
    Calcula a curva de carga de um consumidor, sua energia gasta do início do mês
    até o dia atual e a energia projetada a ser consumida do dia atual até o fim
    do mês.
    """

    # verifica se parâmetros necessários foram definidos em appConfig.yaml
    if 'gis_db' not in settings.APP_CONFIG or 'loadshapes_db' not in settings.APP_CONFIG:
        return Response(status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    if 'filename' not in settings.APP_CONFIG['gis_db']:
        return Response(status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    if 'filename' not in settings.APP_CONFIG['loadshapes_db'] or 'pwd' not in settings.APP_CONFIG['loadshapes_db']:
        return Response(status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # cria um dicionário de-para para converter a classe de string para número conforme
    # campo CLASSE de Curvas.mdb
    consumer_class_dict = {
        'COM': 1,
        'IND': 2,
        'IPP': 4,
        'POD': 4,
        'PRO': 4,
        'RES': 0,
        'RUR': 3,
        'SER': 4
    }

    # calcula o número de dias até o momento e o número de dias até o final do mês
    now_day = datetime.now().day
    now_hour = datetime.now().hour
    now_month = datetime.now().month
    now_year = datetime.now().year
    month_days = calendar.monthrange(now_year, now_month)[1]
    days_partial = now_day - 1 + now_hour / 24.0

    """
    Conecta-se ao banco ACCESS de consumidores para obter seus dados para cálculo
    de sua curva de carga
    """
    # cria conexão com banco ACCESS
    db_name = settings.APP_CONFIG['gis_db']['filename']
    connection_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;' % (db_name,)
    try:
        conn = pyodbc.connect(connection_string)
    except:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if conn == None:
        return Response(status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # monta comando sql para obter a instalação com código "installation_code"
    sql_string = 'select TB_CR_ID, CR_KWH_MES1 from CONSUMIDOR_BT where CR_NUMERO=%s' % (installation_code,)
    cursor = conn.cursor()
    cursor.execute(sql_string)
    rows = cursor.fetchall()
    if len(rows) == 0:
        conn.close()
        return Response(status = status.HTTP_404_NOT_FOUND)

    # calcula a energia média diária do consumidor (kWh) e a demanda média mensal [kW]
    kwh_monthly = rows[0].CR_KWH_MES1
    kwh_daily_avg = kwh_monthly / month_days
    kw_monthly_avg = kwh_monthly / (month_days * 24.0)

    # obtém classe de consumo
    consumer_class_string = rows[0].TB_CR_ID

    # encerra conexão com o banco de consumidores
    cursor.close()
    conn.close()

    """
    Conecta-se ao banco ACCESS de curvas típicas de carga e calcula a curva de carga do consumidor.
    """
    # inicia conexão com o banco de curvas e as categorias da mesma classe do consumidor
    db_name = settings.APP_CONFIG['loadshapes_db']['filename']
    db_pwd = settings.APP_CONFIG['loadshapes_db']['pwd']
    connection_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;PWD=%s' % (db_name, db_pwd)
    try:
        conn = pyodbc.connect(connection_string)
    except:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if conn == None:
        return Response(status = status.HTTP_404_NOT_FOUND)

    sql_string = 'select * from CURVAS_CATEGORIA where CLASSE = %d' % (consumer_class_dict[consumer_class_string],)
    cursor = conn.cursor()
    cursor.execute(sql_string)
    rows = cursor.fetchall()
    if len(rows) == 0:
        conn.close()
        return Response(status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # verifica se a curva de carga é univocamente definida ou se deve calcular a
    # curva de carga com base na participação de mercado
    loadshapes_categories_dict = []
    for row in rows:
        if (row.MIN == -1 and row.MAX == -1) or (kwh_monthly >= row.MIN and kwh_monthly < row.MAX):
            loadshapes_categories_dict.append(dict({
                'CAT_ID': row.CAT_ID,
                'CAT_DESC': row.CAT_DESC,
                'CLASSE': row.CLASSE,
                'PART_MERC': row.PART_MERC,
                'LOADSHAPE': dict()
            }))
    cursor.close()

    # lê do banco as curvas típicas de cada categoria de interesse
    for loadshape_category in loadshapes_categories_dict:
        sql_string = 'select * from CURVAS_CURVATIPICA where PERIODO=4 and CAT_ID=%d' % (loadshape_category['CAT_ID'],)
        cursor = conn.cursor()
        cursor.execute(sql_string)
        rows = cursor.fetchall()
        # proteção
        if (len(rows) == 0):
            continue
        # supõe que existe uma curva
        row = rows[0]
        loadshape_category['LOADSHAPE'].update({'CUR_ID': row.CUR_ID, 'PERIODO': row.PERIODO, 'FAT_POT': row.FAT_POT, 'POINTS': []})
        cursor.close()

    # lê do banco os pontos de cada curva típica de cada categoria
    for loadshape_category in loadshapes_categories_dict:
        loadshape = loadshape_category['LOADSHAPE']
        sql_string = 'select MEDIA_P from CURVAS_PONTOS where CUR_ID=%d order by PTONUM' % (loadshape['CUR_ID'],)
        cursor = conn.cursor()
        cursor.execute(sql_string)
        rows = cursor.fetchall()
        for row in rows:
            loadshape['POINTS'].append(row.MEDIA_P)

    # se houver mais de uma curva típica de carga associada ao consumidor, calcula
    # uma curva de carga através de uma média ponderada
    # caso contrário, pega os valores da única curva típica de carga
    points = []
    if len(loadshapes_categories_dict) == 1:
        loadshape_category = loadshapes_categories_dict[0]
        loadshape = loadshape_category['LOADSHAPE']
        power_factor = loadshape['FAT_POT']
        for point in loadshape['POINTS']:
            points.append(point)
    else:
        weight_total = 0.0
        power_factor = 0.0
        for loadshape_category in loadshapes_categories_dict:
            market_part = loadshape_category['PART_MERC']
            weight_total += market_part
            loadshape = loadshape_category['LOADSHAPE']
            power_factor += market_part * loadshape['FAT_POT']
            if len(points) == 0:
                for point in loadshape['POINTS']:
                    points.append(market_part * point)
            else:
                for i in range(len(points)):
                    points[i] = points[i] + market_part * loadshape['POINTS'][i]
        #normaliza o fator de potência equivalente e cada ponto da curva de carga
        power_factor = power_factor / weight_total
        for i in range(len(points)):
            points[i] = points[i] / weight_total

    """
    Monta a estrutura de saída da função: um JSON com as seguintes chaves:
    kwh_partial: consumo do dia 1 até a hora atual
    kwh_projected: consumo projetado da hora atual até o final do mês
    kw_loadshape: curva de carga com os campos: hour (1,2,...,24) e kw (potência ativa)
    """
    #energias parcial e projetada
    kwh_partial = kwh_daily_avg * days_partial
    kwh_projected = kwh_daily_avg * (month_days - days_partial)

    #compõe a curva de carga
    loadshape_points = []
    for i in range(len(points)):
        pu_avg = points[i]
        hour = i+1
        kw = round(pu_avg * kw_monthly_avg, 4)
        #kvar = round(kw * math.tan(math.acos(power_factor)), 4)
        loadshape_points.append(dict({'hour': hour, 'kw': kw}))

    output_data = {
        'kwh_partial': kwh_partial,
        'kwh_projected': kwh_projected,
        'loadshape_points': loadshape_points
    }

    return Response(output_data, status = status.HTTP_200_OK)


def newUser(request):
    # obtém os campos do novo usuário a partir do form
    form = NewUserForm(request.POST)
    newUserData = {'username': form['username'].value(), 'first_name': form['first_name'].value(),
                   'last_name': form['last_name'].value(), 'email': form['email'].value(),
                   'is_active': False, 'groups': [{'name': 'CELESC-Users'}]}

    data = {}
    editionName = settings.APP_CONFIG['edition']
    template_name = 'registration/' + editionName.lower() + '/activation_email.html'

    data['response'] = 'Usuário registrado com sucesso. Você receberá um e-mail com um link para ativar sua conta.'

    try:
        """
        Usuário registrado anteriormente terá e-mail e grupo atualizados e receberá
        novo link de ativação.
        """
        user = User.objects.get(username = newUserData['username'])

    except User.DoesNotExist:
        user = User.objects.create_user(
            username = newUserData['username'],
            first_name = newUserData['first_name'],
            last_name = newUserData['last_name'],
            email = newUserData['email'],
            is_active = False,
            password='argosdaimon'
        )
    user.email = newUserData['email']

    group = None
    groups = newUserData['groups']
    group = Group.objects.get(name = groups[0]['name'])
    user.groups.add(group)
    user.save()

    message = render_to_string(template_name, {
        'protocol': 'http',
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    subject = 'Ative sua conta'
    send_mail(
        subject = subject,
        message = message,
        from_email = 'argos@daimon.com.br',
        recipient_list = [user.email],
        fail_silently = False,
        )
    return redirect('argos:registration_complete')


@api_view(['GET'])
def transactions_from_installation_code(request, installation_code):
    """
    Obtém as transações referentes a uma instalação específica.
    """
    #obtém transações de uma instalação específica, desde que não sejam de
    #ligar e desligar
    transaction_list = Transaction.objects.filter(installation_code = installation_code
        ).exclude(action__exact = 'Turn On'
        ).exclude(action__exact = 'Turn Off').order_by('-datetime_rx')

    #proteção: verifica se a lista está vazia
    if len(transaction_list) == 0:
        return Response(status = status.HTTP_404_NOT_FOUND)

    #responde com lista de transações
    serializer = TransactionSerializer(transaction_list[0])

    return Response(serializer.data)


@api_view(['GET','POST'])
def mapPoints(request):
    obj = RechargePoint.objects.all()
    serializerPoint = RechargePointSerializer(obj,many=True)

    return Response(serializerPoint.data)