from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView
from rest_framework.authtoken import views as drf_views
from . import views

app_name = "argos"

editionName = settings.APP_CONFIG['edition'].lower()

urlpatterns = [
    # URLs específicas do aplicativo web
    # home: /
    path('', views.home, name = 'home'),
    # dash: /dash
    path('dash/', views.dash, name = 'dash'),
    # devlist: /devlist
    path('devlist/', views.devlist, name = 'devlist'),
    # filterDate: /filterDate
    path('filterDate/', views.filterDate, name = 'filterDate'),
    # detail: /<eui>/detail
    path('<eui>/detail/', views.detail, name = 'detail'),
    # geomap: /<gateway_id>/geomap
    path('<gateway_id>/geomap/', views.geomap, name = 'geomap'),

    # URL para chamada de página de Tarifa Branca
    path('whitetarifflist/', views.whitetarifflist, name='whitetarifflist'),
    path('<mac>/whitetariff/', views.whitetariff, name='whitetariff'),

    # accounts: URLs específicas para autenticação de usuário
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/' + editionName + '/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/' + editionName + '/logged_out.html'), name='logout'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/' + editionName + '/password_reset_form.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/' + editionName + '/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/' + editionName + '/password_reset_complete.html'), name='password_reset_complete'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/' + editionName + '/password_reset_confirm.html'), name='password_reset_confirm'),

    # registration: URLs específicas para criação de conta de usuário
    path('registration/account-activation/<uidb64>/<token>/', views.account_activation, name='account_activation'),
    path('registration/account-registration/', views.account_registration, name='account_registration'),
    path('registration/activation-complete', TemplateView.as_view(template_name='registration/' + editionName + '/activation_complete.html'), name='activation_complete'),
    path('registration/new-user/', views.newUser, name = 'newUser'),
    path('registration/registration-complete/', TemplateView.as_view(template_name='registration/' + editionName + '/registration_complete.html'), name='registration_complete'),
    path('registration/signup/', TemplateView.as_view(template_name='registration/' + editionName + '/signup_form.html'), name='signup'),
    path('registration/token-auth/', drf_views.obtain_auth_token),
    path('registration/user/<username>/', views.get_user),

    # rest: URLs específicas da REST API
    # card: /rest/card/<installation_code>
    path('rest/card/<installation_code>/', views.cards_usedby_installation_code),
    # installation: /rest/installation/<installation_code>
    path('rest/installation/<installation_code>/', views.installation_exists),
    # loadprofile: /rest/loadprofile/<installation_code>
    path('rest/loadprofile/<installation_code>/', views.loadprofile),
    # transaction: /rest/transaction/credit
    path('rest/transaction/credit/', views.credit),
    # transaction: /rest/transaction/emergency_credit
    path('rest/transaction/emergency_credit/',  views.emergency_credit),
    # transaction: /rest/transaction/<installation_code>
    path('rest/transaction/<installation_code>/', views.transactions_from_installation_code),

    # Flutter database view
    path('rest/mappoints/', views.mapPoints),
]
