from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


class DateFilterForm(forms.Form):
    device_eui = forms.CharField(label='EUI', max_length = 50)
    datetime_ini = forms.DateTimeField(label='Data inicial')
    datetime_fin = forms.DateTimeField(label='Data final')


class WhiteTariffForm(forms.Form):
    # filtro relativo ao gráfico de consumo medido (gráfico 2)
    datetime_ref = forms.DateTimeField(label='Data')
    # filtro relativo à data inicial e à data final (navbar à esquerda)
    datetime_ini = forms.DateTimeField(label='Data inicial')
    datetime_fin = forms.DateTimeField(label='Data final')
    # filtro relativo à data inicial e à data final (campos ocultos)
    datetime_ini_hidden = forms.DateTimeField(label='Inicial')
    datetime_fin_hidden = forms.DateTimeField(label='Final')



class IcaroAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        # elimina a confirmação de is_staff rodando o mesmo código de AuthenticationForm
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

class NewUserForm(forms.Form):
    username = forms.CharField(label='username', max_length = 50)
    first_name = forms.CharField(label='first_name', max_length=50)
    last_name = forms.CharField(label='last_name', max_length=50)
    email = forms.CharField(label='email', max_length=50)
