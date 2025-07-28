from django.db import models
from django.contrib.auth.models import User
import uuid

class Avion(models.Model):
    modelo = models.CharField(max_length=100)
    capacidad = models.IntegerField()
    filas = models.IntegerField()
    columnas = models.IntegerField()

    def __str__(self):
        return f"{self.modelo} - Capacidad: {self.capacidad}"

class Vuelo(models.Model):
    ESTADOS_VUELO = [
        ('programado', 'Programado'),
        ('en_vuelo', 'En vuelo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    avion = models.ForeignKey(Avion, on_delete=models.CASCADE)
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    fecha_salida = models.DateTimeField()
    fecha_llegada = models.DateTimeField()
    duracion = models.DurationField()
    estado = models.CharField(max_length=20, choices=ESTADOS_VUELO)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.origen} → {self.destino} ({self.fecha_salida.date()})"

class Pasajero(models.Model):
    TIPOS_DOCUMENTO = [
        ('dni', 'DNI'),
        ('pasaporte', 'Pasaporte'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=100)
    documento = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO)

    def __str__(self):
        return f"{self.nombre} ({self.documento})"

class Asiento(models.Model):
    TIPOS_ASIENTO = [
        ('economico', 'Económico'),
        ('premium', 'Premium'),
        ('business', 'Business'),
    ]

    ESTADOS_ASIENTO = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('ocupado', 'Ocupado'),
    ]

    avion = models.ForeignKey(Avion, on_delete=models.CASCADE)
    numero = models.CharField(max_length=5)
    fila = models.IntegerField()
    columna = models.CharField(max_length=2)
    tipo = models.CharField(max_length=20, choices=TIPOS_ASIENTO)
    estado = models.CharField(max_length=20, choices=ESTADOS_ASIENTO, default='disponible')

    def __str__(self):
        return f"Asiento {self.numero} - {self.tipo} - {self.estado}"

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    vuelo = models.ForeignKey(Vuelo, on_delete=models.CASCADE)
    pasajero = models.ForeignKey(Pasajero, on_delete=models.CASCADE)
    asiento = models.OneToOneField(Asiento, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='activa')
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_reserva = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"Reserva {self.codigo_reserva} - {self.pasajero.nombre}"

class Boleto(models.Model):
    ESTADOS_BOLETO = [
        ('emitido', 'Emitido'),
        ('anulado', 'Anulado'),
        ('usado', 'Usado'),
    ]

    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    codigo_barra = models.CharField(max_length=100, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_BOLETO, default='emitido')

    def __str__(self):
        return f"Boleto - {self.codigo_barra} - {self.estado}"
