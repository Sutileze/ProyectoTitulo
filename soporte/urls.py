# soporte/urls.py
from django.urls import path
from . import views

app_name = 'soporte'

urlpatterns = [
    path('panel/', views.panel_soporte, name='panel_soporte'),
    path('ticket/<int:ticket_id>/', views.ticket_detalle, name='ticket_detalle'),
    path('ticket/<int:ticket_id>/cerrar/', views.cerrar_ticket, name='cerrar_ticket'),
]
