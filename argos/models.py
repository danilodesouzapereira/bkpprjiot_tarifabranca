from datetime import datetime, time
from django.db import models
from django.contrib.auth.models import Group, User
import statistics

"""
Card: representa um cartão contendo um QR Code que possui um código e o
valor de energia em kWh a ser creditado. Também pode representar um cartão RFID.
"""
class Card(models.Model):
    # código do cartão com QR Code ou do cartão RFID
    code = models.CharField(max_length = 10)
    # valor do crédito em kWh do cartão
    value = models.IntegerField(default = 0)
    # tipo de cartão: 0 -> RFID tag; 1 -> QR Code
    card_type = models.IntegerField(default = 1)
    # variável para indicar se o cartão já foi usado
    is_used = models.BooleanField(default = False)
    def __str__(self):
        return self.code
    class Meta:
        verbose_name = "Cartão"
        verbose_name_plural = "Cartões"

"""
ElectricVehicle: representa um veículo elétrico pertencente a um Proprietário de Unidade
Consumidora (PUC) ou Proprietário de Veículo Elétrico (PVE).
"""
class ElectricVehicle(models.Model):
    # usuário do tipo 'Equatorial-Users-PVE' ou 'Equatorial-Users-PUC' dono do veículo elétrico
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    # placas do veículo elétrico
    plates = models.CharField(max_length = 7)
    def __str__(self):
        return self.plates
    class Meta:
        verbose_name = "Veículo Elétrico"
        verbose_name_plural = "Veículos Elétricos"

"""
ElectricVehicleConsumerUnitOwnerSettings: representa as preferências de um Proprietário de Unidade 
Consumidora (PUC) para recarga/descarga de seu próprio veículo elétrico em uma estação qualquer.
"""
class ElectricVehicleConsumerUnitOwnerSettings(models.Model):
    # estação de recarga para a qual se aplicam estes ajustes
    recharge_station = models.OneToOneField('RechargeStation', on_delete = models.CASCADE)
    # veículo elétrico do PUC
    electric_vehicle = models.OneToOneField('ElectricVehicle', on_delete = models.CASCADE)
    # modo do início/término de recarga/descarga: 'Manual', 'Nível de Bateria', 'Horário', 'Ambos'
    mode = models.CharField(max_length = 20, default = 'Manual')
    # nível máximo de bateria ao recarregar
    max_battery_level_on_recharge = models.IntegerField(default = 100)
    # nível mínimo de bateria ao descarregar
    min_battery_level_on_discharge = models.IntegerField(default = 30)
    # hora para início de recarga em casa
    recharge_start_time = models.TimeField(default = time(23))
    # hora para término de recarga em casa
    recharge_finish_time = models.TimeField(default = time(3))
    # hora para início de descarga em casa
    discharge_start_time = models.TimeField(default = time(17))
    # hora para término de descarga em casa
    discharge_finish_time = models.TimeField(default = time(20))
    # nível mínimo de bateria requerido
    min_battery_level_required = models.IntegerField(default = 20)
    def __str__(self):
        text = self.electric_vehicle.plates + "' settings"
        return text
    class Meta:
        verbose_name = "Preferências de um PUC para recarga/descarga de seu VE em uma estação qualquer"
        verbose_name_plural = "Preferências de um PUC para recarga/descarga de seu VE em uma estação qualquer"

"""
ElectricVehicleElectricVehicleOwnerSettings: representa as preferências de um Proprietário de 
Veículo Elétrico (PVE) para recarga/descarga de um veículo elétrico em uma estação qualquer.
"""
class ElectricVehicleElectricVehicleOwnerSettings(models.Model):
    # veículo elétrico para o qual se aplicam estes ajustes
    electric_vehicle = models.OneToOneField('ElectricVehicle', on_delete = models.CASCADE)
    # modo do início/término de recarga/descarga: 'Manual', 'Nível de Bateria', 'Preço', 'Ambos'
    mode = models.CharField(max_length = 20, default = 'Manual')
    # nível máximo de bateria ao recarregar
    max_battery_level_on_recharge = models.IntegerField(default = 80)
    # nível mínimo de bateria ao descarregar
    min_battery_level_on_discharge = models.IntegerField(default = 50)
    # preço máximo para recarregar
    max_price_to_recharge = models.DecimalField(max_digits = 8, decimal_places = 2, default = 600.0)
    # preço mínimo para descarregar
    min_price_to_discharge = models.DecimalField(max_digits = 8, decimal_places = 2, default = 700.0)
    # nível mínimo de bateria requerido
    min_battery_level_required = models.IntegerField(default = 20)
    def __str__(self):
        text = self.electric_vehicle.plates + "' settings"
        return text
    class Meta:
        verbose_name = "Preferências de um PVE para recarga/descarga de seu VE em uma estação qualquer"
        verbose_name_plural = "Preferências de um PVE para recarga/descarga de seu VE em uma estação qualquer"

"""
Gateway: representa um gateway LoRa.
"""
class Gateway(models.Model):
    # grupo de usuários que tem permissão para ver o gateway
    groups = models.ManyToManyField(Group)
    # servidor LoRa no qual o gateway está registrado
    server = models.ForeignKey('LoraServer', on_delete = models.CASCADE)
    # descrição do gateway
    desc = models.CharField(max_length = 50)
    # id do gateway (código alfanumérico dentro do gateway e que aparece nas
    # configurações do servidor de rede)
    gateway_id = models.CharField(max_length = 50)
    # marca do gateway
    brand = models.CharField(max_length = 50)
    # modelo do gateway
    model = models.CharField(max_length = 50)
    # localização do gateway em lat long no formato -99.999,-99.999
    latlong = models.CharField(max_length = 50)
    def __str__(self):
        text = self.gateway_id + self.desc
        return text

"""
HTTPDevice: representa um dispositivo HTTP que manda informações para um servidor HTTP.
"""
class HTTPDevice(models.Model):
    # grupos de usuários que tem permissão para ver o dispositivo
    groups = models.ManyToManyField(Group)
    # usuários que tem permissão para ver o dispositivo
    users = models.ManyToManyField(User, blank = True)
    # servidor HTTP no qual o dispositivo está registrado
    server = models.ForeignKey('HTTPServer', on_delete = models.CASCADE)
    # tipo do dispositivo
    device_type = models.ForeignKey('HTTPDeviceType', on_delete = models.CASCADE)
    # código mac do dispositivo
    mac = models.CharField(max_length = 50)
    # descrição do dispositivo
    desc = models.CharField(max_length = 50)
    def __str__(self):
        text = self.mac + ' - ' + self.desc
        return text
    class Meta:
        verbose_name = "Dispositivo HTTP"
        verbose_name_plural = "Dispositivos HTTP"

"""
HTTPDeviceType: representa um tipo de dispositivo HTTP que manda informações
para um servidor HTTP. Atualmente, há os seguintes tipos:
1-Medidor de Energia (Medidor)
2-Recarregador Veicular Bidirecional (Recarregador)
"""
class HTTPDeviceType(models.Model):
    # número inteiro do tipo de dispositivo
    type_id = models.IntegerField(default = 0)
    # descrição do tipo de dispositivo
    desc = models.CharField(max_length = 50)
    # descrição curta do dispositivo (é a que vai no navsidebar)
    shortdesc = models.CharField(max_length = 20)
    def __str__(self):
        text = str(self.type_id) + ' - ' + self.desc
        return text
    class Meta:
        verbose_name = "Tipo de Dispositivo HTTP"
        verbose_name_plural = "Tipos de Dispositivo HTTP"

"""
HTTPPayload: representa um payload HTTP enviado por um dispositivo HTTP.
Os payloads são gravados no banco local, na tabela de mesmo nome da classe, pelo
???, por meio de um ???. Quando o dispositivo está
associado ao servidor local, os payloads são recuperados desse banco. Para os
outros servidores os payloads são recuperados ???.
"""
class HTTPPayload(models.Model):
    # dispositivo que enviou o dado
    device = models.ForeignKey('HTTPDevice', on_delete = models.CASCADE)
    # data/hora de recepção do payload
    datetime_rx = models.DateTimeField()
    # payload completo em JSON
    payload = models.JSONField()
    # pacote de dados enviado dentro do payload
    data_payload = models.CharField(max_length = 256)
    def __str__(self):
        text = self.datetime_rx.strftime('%d/%m/%Y %H:%M:%S')
        return text
    class Meta:
        verbose_name = "Payload HTTP"
        verbose_name_plural = "Payloads HTTP"

"""
HTTPServer: representa um servidor de rede HTTP. Atualmente, há os seguintes tipos:
1-Local
2-IMT-Instituto Mauá de Tecnologia
"""
class HTTPServer(models.Model):
    # número inteiro do servidor
    server_id = models.IntegerField(default = 0)
    # descrição do servidor
    desc = models.CharField(max_length = 50)
    # formato do data payload quando acessado via MQTT (pode ser 'hexa' ou 'base64')
    mqtt_data_format = models.CharField(max_length = 10)
    # formato do data payload quando acessado via REST (pode ser 'hexa' ou 'base64')
    rest_data_format = models.CharField(max_length = 10)
    def __str__(self):
        text = str(self.server_id) + ' - ' + self.desc
        return text
    class Meta:
        verbose_name = "Servidor HTTP"
        verbose_name_plural = "Servidores HTTP"

"""
Installation: representa uma instalação que vai receber um dispositivo LoRa ou
HTTP.
"""
class Installation(models.Model):
    # código da instalação
    code = models.CharField(max_length = 20)
    # indica se a instalação está ativa ou não
    active = models.BooleanField(default = True)
    # tipo da instalação
    installation_type = models.ForeignKey('InstallationType', on_delete = models.CASCADE)
    # grupos de usuários que tem permissão para ver a instalação
    groups = models.ManyToManyField(Group)
    # usuários que tem permissão para ver a instalação
    users = models.ManyToManyField(User, blank = True)
    # dispositivos HTTP associados à instalação
    http_devices = models.ManyToManyField(
        'HTTPDevice',
        through = 'InstallationPeriodHTTPDevice',
        through_fields = ('installation', 'device'),
    )
    # dispositivos LoRa associados à instalação
    lora_devices = models.ManyToManyField(
        'LoraDevice',
        through = 'InstallationPeriodLoraDevice',
        through_fields = ('installation', 'device'),
    )
    def __str__(self):
        return self.code
    class Meta:
        verbose_name = "Instalação"
        verbose_name_plural = "Instalações"

"""
InstallationPeriodHTTPDevice: Período em que uma instalação esteve associada a
um dispositivo HTTP. Um dispositivo HTTP pode estar associado a N instalações e
uma instalação pode estar associada a N dispositivos HTTP, o que sugere uma
relação many-to-many. Porém, essa associação ocorre por um período específico,
que tem data/hora de início e pode ou não ter data/hora de término.
"""
class InstallationPeriodHTTPDevice(models.Model):
    # instalação da associação instalação-dispositivo HTTP
    installation = models.ForeignKey('Installation', on_delete = models.CASCADE)
    # dispositivo HTTP da associação instalação-dispositivo HHTP
    device = models.ForeignKey('HTTPDevice', on_delete = models.CASCADE)
    # data/hora de início do período de associação instalação-dispositivo HTTP
    datetime_ini = models.DateTimeField()
    # data/hora de término do período de associação instalação-dispositivo HTTP
    datetime_fin = models.DateTimeField(blank = True, null = True)
    def __str__(self):
        text = self.installation.code + self.device.mac
        return text
    class Meta:
        verbose_name = "Período de Instalação do Dispositivo HTTP"
        verbose_name_plural = "Períodos de Instalação dos Dispositivos HTTP"

"""
InstallationPeriodLoraDevice: Período em que uma instalação esteve associada a
um dispositivo LoRa. Um dispositivo LoRa pode estar associado a N instalações e
uma instalação pode estar associada a N dispositivos LoRa, o que sugere uma
relação many-to-many. Porém, essa associação ocorre por um período específico,
que tem data/hora de início e pode ou não ter data/hora de término.
"""
class InstallationPeriodLoraDevice(models.Model):
    # instalação da associação instalação-dispositivo LoRa
    installation = models.ForeignKey('Installation', on_delete = models.CASCADE)
    # dispositivo LoRa da associação instalação-dispositivo LoRa
    device = models.ForeignKey('LoraDevice', on_delete = models.CASCADE)
    # data/hora de início do período de associação instalação-dispositivo LoRa
    datetime_ini = models.DateTimeField()
    # data/hora de término do período de associação instalação-dispositivo LoRa
    datetime_fin = models.DateTimeField(blank = True, null = True)
    def __str__(self):
        text = self.installation.code + self.device.eui
        return text
    class Meta:
        verbose_name = "Período de Instalação do Dispositivo LoRa"
        verbose_name_plural = "Períodos de Instalação dos Dispositivos LoRa"

"""
InstallationType: representa o tipo de instalação. Atualmente, há os seguintes tipos:
1-Instalação Consumidora
2-???
"""
class InstallationType(models.Model):
    # número inteiro do tipo de instalação
    type_id = models.IntegerField(default = 0)
    # descrição do tipo de instalação
    desc = models.CharField(max_length = 50)
    def __str__(self):
        text = str(self.type_id) + ' - ' + self.desc
        return text
    class Meta:
        verbose_name = "Tipo de Instalação"
        verbose_name_plural = "Tipos de Instalação"

"""
LoraDevice: representa um dispositivo LoRa que manda informações para um servidor LoRa.
"""
class LoraDevice(models.Model):
    # grupos de usuários que tem permissão para ver o dispositivo
    groups = models.ManyToManyField(Group)
    # usuários que tem permissão para ver o dispositivo
    users = models.ManyToManyField(User, blank = True)
    # servidor lora no qual o dispositivo está registrado
    server = models.ForeignKey('LoraServer', on_delete = models.CASCADE)
    # tipo do dispositivo
    device_type = models.ForeignKey('LoraDeviceType', on_delete = models.CASCADE)
    # código do dispositivo
    eui = models.CharField(max_length = 50)
    # senha do dispositivo
    pwd = models.CharField(max_length = 50)
    # descrição do dispositivo
    desc = models.CharField(max_length = 50)
    def __str__(self):
        text = self.eui + ' - ' + self.desc
        return text
    class Meta:
        verbose_name = "Dispositivo LoRa"
        verbose_name_plural = "Dispositivos LoRa"

"""
LoraDeviceType: representa um tipo de dispositivo LoRa que manda informações
para um servidor LoRa. Atualmente, há os seguintes tipos:
1-Sensor de tensão e corrente (Sensor VI)
2-Remota para medidor de energia (Remota)
3-Sensor de temperatura (Sensor T)
4-Rastreador GPS (GPS)
5-Sensor de temperatura e umidade (Sensor TU)
"""
class LoraDeviceType(models.Model):
    # número inteiro do tipo de dispositivo
    type_id = models.IntegerField(default = 0)
    # descrição do tipo de dispositivo
    desc = models.CharField(max_length = 50)
    # descrição curta do dispositivo (é a que vai no navsidebar)
    shortdesc = models.CharField(max_length = 20)
    # intervalo nominal de envio de dados em min
    interval = models.DecimalField(max_digits = 4, decimal_places = 2)
    def __str__(self):
        text = str(self.type_id) + " - " + self.desc
        return text
    class Meta:
        verbose_name = "Tipo de Dispositivo LoRa"
        verbose_name_plural = "Tipos de Dispositivo LoRa"

"""
LoraPayload: representa um payload LoRa enviado por um dispositivo LoRa.
Os payloads são gravados no banco local, na tabela de mesmo nome da classe, pelo
serviço argos_mqtt, por meio de um MQTT client. Quando o dispositivo está
associado ao servidor local, os payloads são recuperados desse banco. Para os
outros servidores os payloads são recuperados via REST API, conforme documentação
específica de cada servidor, e se apresentam no formato JSON.
"""
class LoraPayload(models.Model):
    # dispositivo que enviou o dado
    device = models.ForeignKey('LoraDevice', on_delete = models.CASCADE)
    # data/hora de recepção do payload
    datetime_rx = models.DateTimeField()
    # payload completo em JSON
    payload = models.JSONField(blank = True, null = True)
    # pacote de dados enviado dentro do payload
    data_payload = models.CharField(max_length = 256)
    # relação sinal/ruído (extraído do data_payload e gravado em campo separado)
    snr = models.DecimalField(max_digits = 8, decimal_places = 2)
    # intensidade do sinal em dB (extraído do data_payload e gravado em campo separado)
    rssi = models.DecimalField(max_digits = 8, decimal_places = 2)
    def __str__(self):
        text = self.datetime_rx.strftime('%d/%m/%Y %H:%M:%S')
        return text
    class Meta:
        verbose_name = "Payload LoRa"
        verbose_name_plural = "Payloads LoRa"

"""
LoraServer: representa um servidor de rede LoRa. Atualmente, há os seguintes tipos:
1-Local
2-Orbiwise
3-IMT-Instituto Mauá de Tecnologia
"""
class LoraServer(models.Model):
    # número inteiro do servidor
    server_id = models.IntegerField(default = 0)
    # descrição do servidor
    desc = models.CharField(max_length = 50)
    # formato do data payload quando acessado via MQTT (pode ser 'hexa' ou 'base64')
    mqtt_data_format = models.CharField(max_length = 10)
    # formato do data payload quando acessado via REST (pode ser 'hexa' ou 'base64')
    rest_data_format = models.CharField(max_length = 10)
    def __str__(self):
        text = str(self.server_id) + " - " + self.desc
        return text
    class Meta:
        verbose_name = "Servidor LoRa"
        verbose_name_plural = "Servidores LoRa"

"""
RechargePoint: representa um ponto de recarga dentro de uma instalação consumidora.
"""
class RechargePoint(models.Model):
    # estação de recarga na qual o ponto de recarga está
    recharge_station = models.ForeignKey('RechargeStation', on_delete = models.CASCADE)
    # descrição do ponto
    desc = models.CharField(max_length = 50)
    # código de identificação via QR Code
    code = models.CharField(max_length = 10)
    # latitude
    latitude = models.DecimalField(max_digits = 8, decimal_places = 5, default = 0.0)
    # longitude
    longitude = models.DecimalField(max_digits = 8, decimal_places = 5, default = 0.0)
    # status do ponto de recarga: 'Off', 'Available', 'EV connected', 'G2V', V2G'
    status = models.CharField(max_length = 20, default = 'Off')
    def __str__(self):
        return self.desc
    class Meta:
        verbose_name = "Ponto de Recarga"
        verbose_name_plural = "Pontos de Recarga"


"""
RechargeStation: representa um estação de recarga associada a uma instalação consumidora e 
pertencente a um Prorietário de Unidade Consumidora (PUC) ou Proprietário de Veículo Elétrico (PVE).
"""
class RechargeStation(models.Model):
    # instalação do tipo 'Instalação Consumidora' na qual está a estação de recarga
    installation = models.OneToOneField('Installation', on_delete = models.CASCADE)
    # usuário do tipo 'Equatorial-Users-PVE' ou 'Equatorial-Users-PUC' dono da estação
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    # descrição da estação
    desc = models.CharField(max_length = 50)
    def __str__(self):
        return self.desc

    def lat_long(self):
        recharge_points = RechargePoint.objects.filter(recharge_station = self)
        if len(recharge_points) > 0:
            latitudes = []
            longitudes = []
            for rp in recharge_points:
                latitudes.add(rp.latitude)
                longitudes.add(rp.longitude)
            return (statistics.mean(latitudes), statistics.mean(longitudes))
        else:
            return None
    class Meta:
        verbose_name = "Estação de Recarga"
        verbose_name_plural = "Estações de Recarga"


"""
RechargeStationConsumerUnitOwnerSettings: representa as preferências de um Proprietário de Unidade 
Consumidora (PUC) para recarga/descarga de um veículo elétrico qualquer.
"""
class RechargeStationConsumerUnitOwnerSettings(models.Model):
    # estação de recarga para a qual se aplicam estes ajustes
    recharge_station = models.OneToOneField('RechargeStation', on_delete = models.CASCADE)
    # preço de venda no horário de ponta
    peak_sale_price = models.DecimalField(max_digits = 8, decimal_places = 2, default = 900)
    # preço de venda no horário fora de ponta
    off_peak_sale_price = models.DecimalField(max_digits = 8, decimal_places = 2, default = 500)
    # preço de compra no horário de ponta
    peak_purchase_price = models.DecimalField(max_digits = 8, decimal_places = 2, default = 700)
    # preço de compra no horário fora de ponta
    off_peak_purchase_price = models.DecimalField(max_digits = 8, decimal_places = 2, default = 300)
    def __str__(self):
        text = self.recharge_station.desc + "' settings"
        return text
    class Meta:
        verbose_name = "Preferências de um PUC para recarga/descarga de um VE qualquer em sua estação"
        verbose_name_plural = "Preferências de um PUC para recarga/descarga de um VE qualquer em sua estação"
    
    

"""
RechargeStationElectricVehicleOwnerSettings: representa as preferências de um Proprietário de 
Veículo Elétrico (PVE) para recarga/descarga de um veículo elétrico em sua própria instalação consumidora.
"""
class RechargeStationElectricVehicleOwnerSettings(models.Model):
    # veículo elétrico para o qual se aplicam estes ajustes
    electric_vehicle = models.OneToOneField('ElectricVehicle', on_delete = models.CASCADE)
    # estação de recarga do PVE
    recharge_station = models.OneToOneField('RechargeStation', on_delete = models.CASCADE)
    # modo do início/término de recarga/descarga: 'Manual', 'Nível de Bateria', 'Horário', 'Ambos'
    mode = models.CharField(max_length = 20, default = 'Manual')
    # nível máximo de bateria ao recarregar
    max_battery_level_on_recharge = models.IntegerField(default = 100)
    # nível mínimo de bateria ao descarregar
    min_battery_level_on_discharge = models.IntegerField(default = 30)
    # hora para início de recarga em casa
    recharge_start_time = models.TimeField(default = time(23))
    # hora para término de recarga em casa
    recharge_finish_time = models.TimeField(default = time(3))
    # hora para início de descarga em casa
    discharge_start_time = models.TimeField(default = time(17))
    # hora para término de descarga em casa
    discharge_finish_time = models.TimeField(default = time(20))
    # nível mínimo de bateria requerido
    min_battery_level_required = models.IntegerField(default = 20)
    def __str__(self):
        text = self.recharge_station.desc + "' settings"
        return text
    class Meta:
        verbose_name = "Preferências de um PVE para recarga/descarga de seu VE em sua estação"
        verbose_name_plural = "Preferências de um PVE para recarga/descarga de seu VE em sua estação"

"""
Transaction: representa uma transação realizada na conta de energia de uma
instalação, referente a um dispositivo LoRa do tipo 2-Remota.
"""
class Transaction(models.Model):
    # data/hora de recebimento da transação
    datetime_rx = models.DateTimeField()
    # código da instalação a que se refere a transação
    installation_code = models.CharField(max_length = 20)
    # código do dispositivo LoRa responsável pelo envio do dado
    device_eui = models.CharField(max_length = 50, blank = True)
    # código do cartão com QR Code ou RFID enviado pelo app mobile
    card_code = models.CharField(max_length = 10, blank = True)
    # leitura de pulsos consumidos da transação recebida
    pulseC = models.IntegerField(default = 0)
    # valor do crédito/débito em kWh a ser realizado na transação
    energy_value = models.DecimalField(max_digits = 8, decimal_places = 2, default = 0.0)
    # saldo de energia em kWh após o crédito/débito especificado em energy_value
    energy_account = models.DecimalField(max_digits = 8, decimal_places = 2, default = 0.0)
    # indica tipo da transação (pode ser 'Credit', 'Debit', 'Turn On', 'Turn Off' ou 'Emergency Credit')
    action = models.CharField(max_length = 20)
    # indica o estado da instalação (pode ser 'On' ou 'Off')
    status = models.CharField(max_length = 20, blank = True)
    # instalação a que se refere o dado enviado
    installation = models.ForeignKey('Installation', on_delete = models.SET_NULL, blank = True, null = True)
    # dispositivo LoRa que enviou o dado
    device = models.ForeignKey('LoraDevice', on_delete = models.SET_NULL, blank = True, null = True)
    # cartão com QR Code ou cartão RFID enviado pelo app mobile
    card = models.ForeignKey('Card', on_delete = models.SET_NULL, blank = True, null = True)
    def __str__(self):
        text = self.datetime_rx.strftime('%d/%m/%Y %H:%M:%S')
        return text
    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"


"""
TariffFlag: representa uma bandeira tarifária
"""
class TariffFlag(models.Model):
    # número inteiro do tipo de bandeira
    type_id = models.IntegerField(default=0)
    # descrição da bandeira
    desc = models.CharField(max_length = 50)
    # ano de vigência
    year = models.IntegerField(default=0)
    # mês de vigência
    month = models.IntegerField(default=0)
    # valor (R$/kWh)
    value = models.DecimalField(max_digits = 8, decimal_places = 5, default = 0.0)
    def __str__(self):
        text = 'Bandeira - ' + str(self.month) + '/' + str(self.year) + ' - ' + str(self.value)
        return text
    class Meta:
        verbose_name = "Valor de bandeira tarifária"
        verbose_name_plural = "Valores de bandeira tarifária"


"""
Tariff: representa uma tarifa
"""
class Tariff(models.Model):
    # grupo da tarifa ('A', 'B', ...)
    group = models.CharField(max_length = 1)
    # nome da tarifa ('Convencional', 'Branca', 'Azul', ...)
    name = models.CharField(max_length=50)
    # subgrupo da tarifa convencional ('B1', 'B2', 'B4a', ...)
    subgroup = models.CharField(max_length = 3)
    # ID da classificação (1, 2, 3, ...)
    classif_id = models.IntegerField(default=0)
    # descrição da classificação
    classif_desc = models.CharField(max_length=50)
    # valor da tarifa (R$/kWh)
    value = models.DecimalField(max_digits = 8, decimal_places = 5, default = 0.0)
    def __str__(self):
        text = 'Tarifa - ' + str(self.name) + ' ' + str(self.subgroup) + ' ' + str(self.classif_desc)
        return text
    class Meta:
        verbose_name = "Valor da tarifa"
        verbose_name_plural = "Valores da tarifa"


"""
TaxPisCofins: representa os impostos PIS/COFINS de um determinado mês
"""
class TaxPisCofins(models.Model):
    # ano de vigência
    year = models.IntegerField(default=0)
    # mês de vigência
    month = models.IntegerField(default=0)
    # valor percentual do imposto referente ao PIS
    value_pis = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    # valor percentual do imposto referente ao COFINS
    value_cofins = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    def __str__(self):
        text = 'PIS/COFINS - ' + str(self.month) + '/' + str(self.year)
        return text
    class Meta:
        verbose_name = "Valor de PIS/COFINS"
        verbose_name_plural = "Valores de PIS/COFINS"


"""
TaxIcms: representa os valores de ICMS para um determinado mês
"""
class TaxIcms(models.Model):
    # ano de vigência
    year = models.IntegerField(default=0)
    # mês de vigência
    month = models.IntegerField(default=0)
    # valor percentual para consumidor residencial 1 (até 150 kWh)
    valueRes1 = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    # valor percentual para consumidor residencial 2 (acima 150 kWh)
    valueRes2 = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    # valor percentual para consumidor rural 1 (até 500 kWh)
    valueRur1 = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    # valor percentual para consumidor rural 2 (acima de 500 kWh)
    valueRur2 = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    # valor percentual para outras classes de consumidores
    valueOther = models.DecimalField(max_digits=5, decimal_places=3, default=0.0)
    def __str__(self):
        text = 'ICMS - ' + str(self.month) + '/' + str(self.year)
        return text
    class Meta:
        verbose_name = "Valor de ICMS"
        verbose_name_plural = "Valores de ICMS"
