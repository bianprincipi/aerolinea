from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from .models import Vuelo, Asiento, Pasajero, Reserva, Boleto, Avion
import uuid
from datetime import datetime
from django.contrib.auth.models import User

# Vista de inicio
def home(request):
    """Vista principal del sistema"""
    context = {
        'total_vuelos': Vuelo.objects.count(),
        'vuelos_hoy': Vuelo.objects.filter(fecha_salida__date=timezone.now().date()).count(),
        'total_reservas': Reserva.objects.count(),
        'reservas_activas': Reserva.objects.filter(estado='activa').count(),
    }
    return render(request, 'gestion/home.html', context)

# Autenticación
def login_view(request):
    """Vista de login personalizada"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.first_name or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Credenciales inválidas')
    
    return render(request, 'registration/login.html')

def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente')
    return redirect('login')

# Gestión de Vuelos
def lista_vuelos(request):
    """Lista todos los vuelos disponibles"""
    vuelos = Vuelo.objects.select_related('avion').filter(
        estado__in=['programado', 'en_vuelo']
    ).order_by('fecha_salida')
    
    # Filtros opcionales
    origen = request.GET.get('origen')
    destino = request.GET.get('destino')
    fecha = request.GET.get('fecha')
    
    if origen:
        vuelos = vuelos.filter(origen__icontains=origen)
    if destino:
        vuelos = vuelos.filter(destino__icontains=destino)
    if fecha:
        vuelos = vuelos.filter(fecha_salida__date=fecha)
    
    return render(request, 'gestion/vuelos.html', {'vuelos': vuelos})

def detalle_vuelo(request, vuelo_id):
    """Detalle de un vuelo específico con asientos disponibles"""
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    asientos = Asiento.objects.filter(
        avion=vuelo.avion, 
        estado='disponible'
    ).order_by('fila', 'columna')
    
    # Contar asientos por tipo
    asientos_stats = {
        'total': asientos.count(),
        'economico': asientos.filter(tipo='economico').count(),
        'premium': asientos.filter(tipo='premium').count(),
        'business': asientos.filter(tipo='business').count(),
    }
    
    return render(request, 'gestion/detalle_vuelo.html', {
        'vuelo': vuelo, 
        'asientos': asientos,
        'asientos_stats': asientos_stats
    })

# Sistema de Reservas
def crear_reserva(request, vuelo_id, asiento_id):
    """Crear una nueva reserva"""
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    asiento = get_object_or_404(Asiento, id=asiento_id)

    # Verificar disponibilidad
    if asiento.estado != 'disponible':
        messages.error(request, 'El asiento ya no está disponible.')
        return redirect('detalle_vuelo', vuelo_id=vuelo_id)

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST['nombre']
            documento = request.POST['documento']
            email = request.POST['email']
            telefono = request.POST['telefono']
            fecha_nacimiento = request.POST['fecha_nacimiento']
            tipo_documento = request.POST['tipo_documento']

            # Buscar o crear pasajero
            pasajero, creado = Pasajero.objects.get_or_create(
                documento=documento,
                defaults={
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'fecha_nacimiento': fecha_nacimiento,
                    'tipo_documento': tipo_documento,
                }
            )

            # Verificar que el pasajero no tenga otra reserva en el mismo vuelo
            reserva_existente = Reserva.objects.filter(
                vuelo=vuelo, 
                pasajero=pasajero,
                estado='activa'
            ).first()
            
            if reserva_existente:
                messages.error(request, 'Este pasajero ya tiene una reserva activa en este vuelo.')
                return redirect('detalle_vuelo', vuelo_id=vuelo_id)

            # Calcular precio según tipo de asiento
            precio_multiplicador = {
                'economico': 1.0,
                'premium': 1.5,
                'business': 2.0,
            }
            precio_final = float(vuelo.precio_base) * precio_multiplicador.get(asiento.tipo, 1.0)

            # Crear la reserva
            reserva = Reserva.objects.create(
                vuelo=vuelo,
                pasajero=pasajero,
                asiento=asiento,
                estado='activa',
                precio=precio_final,
            )

            # Cambiar estado del asiento
            asiento.estado = 'reservado'
            asiento.save()

            # Crear el boleto
            boleto = Boleto.objects.create(
                reserva=reserva,
                codigo_barra=f"BOL-{uuid.uuid4().hex[:8].upper()}",
                estado='emitido'
            )

            messages.success(request, f'¡Reserva creada exitosamente! Código: {reserva.codigo_reserva}')
            return render(request, 'gestion/reserva_exitosa.html', {
                'reserva': reserva, 
                'boleto': boleto,
                'vuelo': vuelo,
                'pasajero': pasajero
            })

        except Exception as e:
            messages.error(request, f'Error al crear la reserva: {str(e)}')
            return redirect('detalle_vuelo', vuelo_id=vuelo_id)

    return render(request, 'gestion/form_reserva.html', {
        'vuelo': vuelo, 
        'asiento': asiento
    })

# Reportes
@login_required
def reportes_dashboard(request):
    """Dashboard principal de reportes"""
    context = {
        'total_vuelos': Vuelo.objects.count(),
        'vuelos_por_estado': dict(Vuelo.objects.values_list('estado').annotate(count=Count('id'))),
        'total_reservas': Reserva.objects.count(),
        'reservas_por_estado': dict(Reserva.objects.values_list('estado').annotate(count=Count('id'))),
        'total_pasajeros': Pasajero.objects.count(),
        'ingresos_totales': sum([float(r.precio) for r in Reserva.objects.filter(estado='activa')]),
    }
    return render(request, 'gestion/reportes_dashboard.html', context)

@login_required
def reporte_pasajeros_vuelo(request, vuelo_id):
    """Reporte de pasajeros por vuelo específico"""
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    reservas = Reserva.objects.select_related('pasajero', 'asiento').filter(
        vuelo=vuelo,
        estado='activa'
    ).order_by('asiento__fila', 'asiento__columna')
    
    return render(request, 'gestion/reporte_pasajeros_vuelo.html', {
        'vuelo': vuelo,
        'reservas': reservas,
        'total_pasajeros': reservas.count()
    })

@login_required
def listar_vuelos_reporte(request):
    """Lista vuelos para generar reportes"""
    vuelos = Vuelo.objects.annotate(
        total_reservas=Count('reserva', filter=Q(reserva__estado='activa'))
    ).order_by('-fecha_salida')
    
    return render(request, 'gestion/listar_vuelos_reporte.html', {'vuelos': vuelos})

# Gestión de Reservas
@login_required
def mis_reservas(request):
    """Lista todas las reservas (para administradores)"""
    reservas = Reserva.objects.select_related(
        'vuelo', 'pasajero', 'asiento'
    ).order_by('-fecha_reserva')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        reservas = reservas.filter(estado=estado)
    
    return render(request, 'gestion/mis_reservas.html', {'reservas': reservas})

@login_required
def cancelar_reserva(request, reserva_id):
    """Cancelar una reserva específica"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if request.method == 'POST':
        # Cambiar estado de la reserva
        reserva.estado = 'cancelada'
        reserva.save()
        
        # Liberar el asiento
        asiento = reserva.asiento
        asiento.estado = 'disponible'
        asiento.save()
        
        # Anular el boleto si existe
        try:
            boleto = Boleto.objects.get(reserva=reserva)
            boleto.estado = 'anulado'
            boleto.save()
        except Boleto.DoesNotExist:
            pass
        
        messages.success(request, 'Reserva cancelada exitosamente.')
        return redirect('mis_reservas')
    
    return render(request, 'gestion/confirmar_cancelacion.html', {'reserva': reserva})

def buscar_reserva(request):
    """Buscar reserva por código"""
    reserva = None
    error = None
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo_reserva')
        try:
            reserva = Reserva.objects.select_related(
                'vuelo', 'pasajero', 'asiento'
            ).get(codigo_reserva=codigo)
        except Reserva.DoesNotExist:
            error = 'No se encontró ninguna reserva con ese código.'
    
    return render(request, 'gestion/buscar_reserva.html', {
        'reserva': reserva,
        'error': error
    })

# Vista de error personalizada
def error_404(request, exception):
    return render(request, 'gestion/404.html', status=404)