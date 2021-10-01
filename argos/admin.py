from django.contrib import admin
from .models import *


class InstallationPeriodHTTPDeviceInline(admin.TabularInline):
    model = InstallationPeriodHTTPDevice
    extra = 1

class InstallationPeriodLoraDeviceInline(admin.TabularInline):
    model = InstallationPeriodLoraDevice
    extra = 1


class CardAdmin(admin.ModelAdmin):
    list_display = ['code', 'value', 'card_type', 'is_used']
    fieldsets = [
        (None, {'fields':['code', 'value', 'card_type', 'is_used']})
    ]

class ElectricVehicleAdmin(admin.ModelAdmin):
    list_display = ['user', 'plates']
    fieldsets = [
        (None, {'fields':['user', 'plates']})
    ]

class ElectricVehicleConsumerUnitOwnerSettingsAdmin(admin.ModelAdmin):
    list_display = ['recharge_station', 'electric_vehicle', 'mode', 'max_battery_level_on_recharge',
        'min_battery_level_on_discharge', 'recharge_start_time', 'recharge_finish_time',
        'discharge_start_time', 'discharge_finish_time', 'min_battery_level_required']
    fieldsets = [
        (None, {'fields':['recharge_station', 'electric_vehicle', 'mode', 'max_battery_level_on_recharge',
        'min_battery_level_on_discharge', 'recharge_start_time', 'recharge_finish_time',
        'discharge_start_time', 'discharge_finish_time', 'min_battery_level_required']})
    ]

class ElectricVehicleElectricVehicleOwnerSettingsAdmin(admin.ModelAdmin):
    list_display = ['electric_vehicle', 'mode', 'max_battery_level_on_recharge',
        'min_battery_level_on_discharge', 'max_price_to_recharge', 'min_price_to_discharge',
        'min_battery_level_required']
    fieldsets = [
        (None, {'fields':['electric_vehicle', 'mode', 'max_battery_level_on_recharge',
        'min_battery_level_on_discharge', 'max_price_to_recharge', 'min_price_to_discharge',
        'min_battery_level_required']})
    ]

class GatewayAdmin(admin.ModelAdmin):
    list_display = ['desc', 'gateway_id', 'brand', 'model', 'latlong', 'server']
    fieldsets = [
        (None, {'fields': ['desc', 'gateway_id', 'brand', 'model', 'latlong', 'server', 'groups']}),
    ]

class HTTPDeviceAdmin(admin.ModelAdmin):
    list_display = ['desc', 'mac', 'device_type', 'server']
    fieldsets = [
        (None, {'fields': ['desc', 'mac', 'device_type', 'server', 'groups', 'users']}),
    ]

class HTTPDeviceTypeAdmin(admin.ModelAdmin):
    list_display = ['type_id', 'desc', 'shortdesc']
    fieldsets = [
        (None, {'fields': ['type_id', 'desc', 'shortdesc']}),
    ]

class HTTPPayloadAdmin(admin.ModelAdmin):
    list_display = ['datetime_rx', 'payload', 'data_payload', 'device']
    fieldsets = [
        (None, {'fields': ['datetime_rx', 'payload', 'data_payload', 'device']}),
    ]

class HTTPServerAdmin(admin.ModelAdmin):
    list_display = ['server_id', 'desc', 'mqtt_data_format', 'rest_data_format']
    fieldsets = [
        (None, {'fields': ['server_id', 'desc', 'mqtt_data_format', 'rest_data_format']}),
    ]

class InstallationAdmin(admin.ModelAdmin):
    list_display = ['code', 'active', 'installation_type']
    fieldsets = [
        (None, {'fields': ['code', 'active', 'installation_type', 'groups', 'users']}),
    ]
    inlines = (InstallationPeriodHTTPDeviceInline, InstallationPeriodLoraDeviceInline)

class InstallationTypeAdmin(admin.ModelAdmin):
    list_display = ['type_id', 'desc']
    fieldsets = [
        (None, {'fields': ['type_id', 'desc']}),
    ]

class LoraDeviceAdmin(admin.ModelAdmin):
    list_display = ['desc', 'eui', 'pwd', 'device_type', 'server']
    fieldsets = [
        (None, {'fields': ['desc', 'eui', 'pwd', 'device_type', 'server', 'groups', 'users']}),
    ]

class LoraDeviceTypeAdmin(admin.ModelAdmin):
    list_display = ['type_id', 'desc', 'shortdesc', 'interval']
    fieldsets = [
        (None, {'fields': ['type_id', 'desc', 'shortdesc', 'interval']}),
    ]

class LoraPayloadAdmin(admin.ModelAdmin):
    list_display = ['datetime_rx', 'payload', 'data_payload', 'device', 'snr', 'rssi']
    fieldsets = [
        (None, {'fields': ['datetime_rx', 'payload', 'data_payload', 'device', 'snr', 'rssi']}),
    ]

class LoraServerAdmin(admin.ModelAdmin):
    list_display = ['server_id', 'desc', 'mqtt_data_format', 'rest_data_format']
    fieldsets = [
        (None, {'fields': ['server_id', 'desc', 'mqtt_data_format', 'rest_data_format']}),
    ]

class RechargePointAdmin(admin.ModelAdmin):
    list_display = ['recharge_station', 'desc', 'code', 'latitude', 'longitude']
    fieldsets = [
        (None, {'fields':['recharge_station', 'desc', 'code', 'latitude', 'longitude']})
    ]

class RechargeStationAdmin(admin.ModelAdmin):
    list_display = ['installation', 'user', 'desc']
    fieldsets = [
        (None, {'fields':['installation', 'user', 'desc']})
    ]

class RechargeStationConsumerUnitOwnerSettingsAdmin(admin.ModelAdmin):
    list_display = ['recharge_station', 'peak_sale_price', 'off_peak_sale_price',
        'peak_purchase_price', 'off_peak_purchase_price']
    fieldsets = [
        (None, {'fields':['recharge_station', 'peak_sale_price', 'off_peak_sale_price',
        'peak_purchase_price', 'off_peak_purchase_price']})
    ]

class RechargeStationElectricVehicleOwnerSettingsAdmin(admin.ModelAdmin):
    list_display = ['electric_vehicle', 'recharge_station', 'mode', 'max_battery_level_on_recharge',
        'min_battery_level_on_discharge', 'recharge_start_time', 'recharge_finish_time',
        'discharge_start_time', 'discharge_finish_time', 'min_battery_level_required']
    fieldsets = [
        (None, {'fields':['electric_vehicle', 'recharge_station', 'mode', 'max_battery_level_on_recharge',
        'min_battery_level_on_discharge', 'recharge_start_time', 'recharge_finish_time',
        'discharge_start_time', 'discharge_finish_time', 'min_battery_level_required']})
    ]

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['datetime_rx', 'installation_code', 'device_eui', 'card_code', 'pulseC',
        'energy_value', 'energy_account', 'action', 'status', 'installation', 'device', 'card']
    fieldsets = [
        (None, {'fields': ['datetime_rx', 'installation_code', 'device_eui', 'card_code', 'pulseC',
        'energy_value', 'energy_account', 'action', 'status', 'installation', 'device', 'card']}),
    ]

class TariffAdmin(admin.ModelAdmin):
    list_display = ['group', 'name', 'subgroup', 'classif_id', 'classif_desc', 'value']
    fieldsets = [
        (None, {'fields': ['group', 'name', 'subgroup', 'classif_id', 'classif_desc', 'value']})
    ]

class TariffFlagAdmin(admin.ModelAdmin):
    list_display = ['type_id', 'desc', 'year', 'month', 'value']
    fieldsets = [
        (None, {'fields': ['type_id', 'desc', 'year', 'month', 'value']})
    ]

class TaxIcmsAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'valueRes1', 'valueRes2', 'valueRur1', 'valueRur2', 'valueOther']
    fieldsets = [
        (None, {'fields': ['year', 'month', 'valueRes1', 'valueRes2', 'valueRur1', 'valueRur2', 'valueOther']})
    ]

class TaxPisCofinsAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'value_pis', 'value_cofins']
    fieldsets = [
        (None, {'fields': ['year', 'month', 'value_pis', 'value_cofins']})
    ]


admin.site.register(Card, CardAdmin)
admin.site.register(ElectricVehicle, ElectricVehicleAdmin)
admin.site.register(ElectricVehicleConsumerUnitOwnerSettings, ElectricVehicleConsumerUnitOwnerSettingsAdmin)
admin.site.register(ElectricVehicleElectricVehicleOwnerSettings, ElectricVehicleElectricVehicleOwnerSettingsAdmin)
admin.site.register(Gateway, GatewayAdmin)
admin.site.register(HTTPDevice, HTTPDeviceAdmin)
admin.site.register(HTTPDeviceType, HTTPDeviceTypeAdmin)
admin.site.register(HTTPPayload, HTTPPayloadAdmin)
admin.site.register(HTTPServer, HTTPServerAdmin)
admin.site.register(Installation, InstallationAdmin)
admin.site.register(InstallationType, InstallationTypeAdmin)
admin.site.register(LoraDevice, LoraDeviceAdmin)
admin.site.register(LoraDeviceType, LoraDeviceTypeAdmin)
admin.site.register(LoraPayload, LoraPayloadAdmin)
admin.site.register(LoraServer, LoraServerAdmin)
admin.site.register(RechargePoint, RechargePointAdmin)
admin.site.register(RechargeStation, RechargeStationAdmin)
admin.site.register(RechargeStationConsumerUnitOwnerSettings, RechargeStationConsumerUnitOwnerSettingsAdmin)
admin.site.register(RechargeStationElectricVehicleOwnerSettings, RechargeStationElectricVehicleOwnerSettingsAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Tariff, TariffAdmin)
admin.site.register(TariffFlag, TariffFlagAdmin)
admin.site.register(TaxPisCofins, TaxPisCofinsAdmin)
admin.site.register(TaxIcms, TaxIcmsAdmin)
