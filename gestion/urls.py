from django.urls import path
from . import views

urlpatterns = [
    path('vuelos/', views.lista_vuelos, name='lista_vuelos'),
    path('vuelos/<int:vuelo_id>/', views.detalle_vuelo, name='detalle_vuelo'),
    path('vuelos/<int:vuelo_id>/asiento/<int:asiento_id>/reservar/', views.crear_reserva, name='crear_reserva'),
    path('vuelos/<int:vuelo_id>/', views.detalle_vuelo, name='detalle_vuelo'),
    path('vuelos/<int:vuelo_id>/reservar/<int:asiento_id>/', views.reservar_asiento, name='reservar_asiento'),


]

