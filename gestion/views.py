from django.shortcuts import render, get_object_or_404
from .models import Vuelo, Asiento
from .models import Pasajero, Reserva
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
import uuid
from .models import Vuelo, Asiento, Pasajero, Reserva, Boleto


def lista_vuelos(request):
    vuelos = Vuelo.objects.all()
    return render(request, 'gestion/vuelos.html', {'vuelos': vuelos})

def detalle_vuelo(request, vuelo_id):
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    asientos = Asiento.objects.filter(avion=vuelo.avion, estado='disponible')
    return render(request, 'gestion/detalle_vuelo.html', {'vuelo': vuelo, 'asientos': asientos})

def crear_reserva(request, vuelo_id, asiento_id):
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    asiento = get_object_or_404(Asiento, id=asiento_id)

    # Primero chequeamos si el asiento sigue disponible
    if asiento.estado != 'disponible':
        return render(request, 'gestion/error.html', {'mensaje': 'El asiento ya fue reservado.'})

    if request.method == 'POST':
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

        # Crear la reserva
        reserva = Reserva.objects.create(
            vuelo=vuelo,
            pasajero=pasajero,
            asiento=asiento,
            estado='activa',
            fecha_reserva=timezone.now(),
            precio=vuelo.precio_base,
            codigo_reserva=str(uuid.uuid4())
        )

        # Cambiar estado del asiento a reservado
        asiento.estado = 'reservado'
        asiento.save()

        # Crear el boleto para la reserva
        boleto = Boleto.objects.create(
            reserva=reserva,
            codigo_barra=str(uuid.uuid4()),  # código único simulado
            estado='activo'
        )

        return render(request, 'gestion/reserva_exitosa.html', {'reserva': reserva, 'boleto': boleto})

    # Si no es POST, mostramos el formulario para ingresar datos
    return render(request, 'gestion/form_reserva.html', {'vuelo': vuelo, 'asiento': asiento})


#def detalle_vuelo(request, vuelo_id):
   # vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    #asientos = Asiento.objects.filter(avion=vuelo.avion, estado='disponible')
    #return render(request, 'detalle_vuelo.html', {'vuelo': vuelo, 'asientos': asientos})


def reservar_asiento(request, vuelo_id, asiento_id):
    asiento = get_object_or_404(Asiento, id=asiento_id, vuelo_id=vuelo_id)

    if asiento.disponible:
        asiento.disponible = False
        asiento.save()
        # Podés mostrar un mensaje de éxito con mensajes, pero por ahora redirigimos
        return HttpResponseRedirect(reverse('detalle_vuelo', args=[vuelo_id]))
    else:
        # Ya reservado
        return HttpResponseRedirect(reverse('detalle_vuelo', args=[vuelo_id]))
