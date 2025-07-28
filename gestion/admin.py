from django.contrib import admin
from .models import Avion, Vuelo, Pasajero, Asiento, Reserva, Boleto

@admin.register(Avion)
class AvionAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'capacidad', 'filas', 'columnas')
    search_fields = ('modelo',)

@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'fecha_salida', 'fecha_llegada', 'estado', 'precio_base')
    list_filter = ('estado',)
    search_fields = ('origen', 'destino')
    autocomplete_fields = ['avion', 'usuario']

@admin.register(Pasajero)
class PasajeroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'documento', 'email', 'telefono')
    search_fields = ('nombre', 'documento')

@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'estado', 'avion')
    list_filter = ('tipo', 'estado')
    search_fields = ('numero',)
    autocomplete_fields = ['avion']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo_reserva', 'vuelo', 'pasajero', 'asiento', 'estado', 'fecha_reserva', 'precio')
    list_filter = ('estado',)
    search_fields = ('codigo_reserva',)
    autocomplete_fields = ['vuelo', 'pasajero', 'asiento']

@admin.register(Boleto)
class BoletoAdmin(admin.ModelAdmin):
    list_display = ('codigo_barra', 'reserva', 'fecha_emision', 'estado')
    list_filter = ('estado',)
    search_fields = ('codigo_barra',)
    autocomplete_fields = ['reserva']
