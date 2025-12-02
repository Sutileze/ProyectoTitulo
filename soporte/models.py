# soporte/models.py
from django.db import models
from usuarios.models import Comerciante


class TicketSoporte(models.Model):
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En proceso'),
        ('RESUELTO', 'Resuelto'),
        ('CERRADO', 'Cerrado'),
    ]

    comerciante = models.ForeignKey(
        Comerciante,
        on_delete=models.CASCADE,
        related_name='tickets_soporte'
    )
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()

    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='MEDIA'
    )
    estado = models.CharField(
        max_length=12,
        choices=ESTADO_CHOICES,
        default='ABIERTO'
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ticket de soporte"
        verbose_name_plural = "Tickets de soporte"
        ordering = ['-creado_en']

    def __str__(self):
        return f"#{self.id} - {self.asunto}"
