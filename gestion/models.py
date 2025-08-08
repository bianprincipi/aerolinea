from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from datetime import timedelta

class Avion(models.Model):
    modelo = models.CharField(max_length=100)
    capacidad = models.IntegerField()
    filas = models.IntegerField()
    columnas = models.IntegerField()

    def clean(self):
        """Validaciones personalizadas"""
        if self.capacidad <= 0:
            raise ValidationError("La capacidad debe ser mayor a 0")
        
        if self.filas <= 0 or self.columnas <= 0:
            raise ValidationError("Las filas y columnas deben ser mayores a 0")
        
        if self.filas * self.columnas != self.capacidad:
            raise ValidationError("La capacidad debe coincidir con filas × columnas")
        
        if self.columnas not in [4, 6]:
            raise ValidationError("Las columnas deben ser 4 o 6")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.modelo} - Capacidad: {self.capacidad}"

    class Meta:
        verbose_name_plural = "Aviones"

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
    estado = models.CharField(max_length=20, choices=ESTADOS_VUELO, default='programado')
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_salida and self.fecha_llegada:
            if self.fecha_llegada <= self.fecha_salida:
                raise ValidationError("La fecha de llegada debe ser posterior a la fecha de salida")
            
            if self.fecha_salida <= timezone.now():
                raise ValidationError("La fecha de salida debe ser futura")
        
        if self.origen == self.destino:
            raise ValidationError("El origen y destino no pueden ser iguales")
        
        if self.precio_base and self.precio_base <= 0:
            raise ValidationError("El precio base debe ser mayor a 0")
        
        # Verificar conflictos de avión
        if self.avion and self.fecha_salida and self.fecha_llegada:
            conflictos = Vuelo.objects.filter(
                avion=self.avion,
                estado__in=['programado', 'en_vuelo']
            ).exclude(pk=self.pk)
            
            for otro_vuelo in conflictos:
                if (self.fecha_salida < otro_vuelo.fecha_llegada and 
                    self.fecha_llegada > otro_vuelo.fecha_salida):
                    raise ValidationError(f"Conflicto de horario con vuelo {otro_vuelo}")

    def save(self, *args, **kwargs):
        if self.fecha_salida and self.fecha_llegada:
            self.duracion = self.fecha_llegada - self.fecha_salida
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def asientos_disponibles(self):
        return Asiento.objects.filter(avion=self.avion, estado='disponible').count()

    @property
    def porcentaje_ocupacion(self):
        ocupados = self.avion.capacidad - self.asientos_disponibles
        return (ocupados / self.avion.capacidad) * 100 if self.avion.capacidad > 0 else 0

    def __str__(self):
        return f"{self.origen} → {self.destino} ({self.fecha_salida.date()})"

    class Meta:
        ordering = ['fecha_salida']
        verbose_name_plural = "Vuelos"

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

    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_nacimiento and self.fecha_nacimiento >= timezone.now().date():
            raise ValidationError("La fecha de nacimiento debe ser anterior a hoy")
        
        if self.tipo_documento == 'dni' and (len(self.documento) < 7 or len(self.documento) > 8):
            raise ValidationError("El DNI debe tener entre 7 y 8 dígitos")
        
        if not self.nombre.strip():
            raise ValidationError("El nombre no puede estar vacío")

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().title()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def edad(self):
        if self.fecha_nacimiento:
            return (timezone.now().date() - self.fecha_nacimiento).days // 365
        return None

    def __str__(self):
        return f"{self.nombre} ({self.documento})"

    class Meta:
        verbose_name_plural = "Pasajeros"

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

    def clean(self):
        """Validaciones personalizadas"""
        if self.fila <= 0:
            raise ValidationError("La fila debe ser mayor a 0")
        
        if self.avion and self.fila > self.avion.filas:
            raise ValidationError(f"La fila no puede ser mayor a {self.avion.filas}")
        
        if self.columna not in ['A', 'B', 'C', 'D', 'E', 'F']:
            raise ValidationError("La columna debe ser una letra entre A y F")

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"{self.fila}{self.columna}"
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Asiento {self.numero} - {self.get_tipo_display()} - {self.get_estado_display()}"

    class Meta:
        unique_together = ['avion', 'numero']
        ordering = ['fila', 'columna']
        verbose_name_plural = "Asientos"

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

    def clean(self):
        """Validaciones personalizadas"""
        if self.asiento and self.vuelo and self.asiento.avion != self.vuelo.avion:
            raise ValidationError("El asiento debe pertenecer al avión del vuelo")
        
        if self.asiento and self.asiento.estado != 'disponible' and not self.pk:
            raise ValidationError("El asiento no está disponible")
        
        if self.precio and self.precio <= 0:
            raise ValidationError("El precio debe ser mayor a 0")
        
        # Verificar que el pasajero no tenga otra reserva activa en el mismo vuelo
        if self.pasajero and self.vuelo:
            reservas_existentes = Reserva.objects.filter(
                vuelo=self.vuelo,
                pasajero=self.pasajero,
                estado='activa'
            ).exclude(pk=self.pk)
            
            if reservas_existentes.exists():
                raise ValidationError("El pasajero ya tiene una reserva activa en este vuelo")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Actualizar estado del asiento
        if self.estado == 'activa':
            self.asiento.estado = 'reservado'
            self.asiento.save()
        elif self.estado == 'cancelada' and self.asiento.estado == 'reservado':
            self.asiento.estado = 'disponible' 
            self.asiento.save()

    def __str__(self):
        return f"Reserva {str(self.codigo_reserva)[:8]} - {self.pasajero.nombre}"

    class Meta:
        ordering = ['-fecha_reserva']
        verbose_name_plural = "Reservas"

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

    def clean(self):
        """Validaciones personalizadas"""
        if not self.codigo_barra:
            raise ValidationError("El código de barra es obligatorio")

    def save(self, *args, **kwargs):
        if not self.codigo_barra:
            self.codigo_barra = f"BOL-{uuid.uuid4().hex[:8].upper()}"
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Boleto - {self.codigo_barra} - {self.get_estado_display()}"

    class Meta:
        ordering = ['-fecha_emision']
        verbose_name_plural = "Boletos"