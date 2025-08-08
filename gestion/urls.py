from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Gestión de vuelos
    path('vuelos/', views.lista_vuelos, name='lista_vuelos'),
    path('vuelos/<int:vuelo_id>/', views.detalle_vuelo, name='detalle_vuelo'),
    
    # Sistema de reservas
    path('vuelos/<int:vuelo_id>/asiento/<int:asiento_id>/reservar/', 
         views.crear_reserva, name='crear_reserva'),
    path('buscar-reserva/', views.buscar_reserva, name='buscar_reserva'),
    
    # Gestión de reservas (admin)
    path('reservas/', views.mis_reservas, name='mis_reservas'),
    path('reservas/<int:reserva_id>/cancelar/', 
         views.cancelar_reserva, name='cancelar_reserva'),
    
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    path('reportes/vuelos/', views.listar_vuelos_reporte, name='listar_vuelos_reporte'),
    path('reportes/vuelo/<int:vuelo_id>/pasajeros/', 
         views.reporte_pasajeros_vuelo, name='reporte_pasajeros_vuelo'),
]