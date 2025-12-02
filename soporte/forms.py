# soporte/forms.py
from django import forms
from .models import TicketSoporte


class TicketSoporteForm(forms.ModelForm):
    class Meta:
        model = TicketSoporte
        fields = ['asunto', 'descripcion', 'prioridad']
        widgets = {
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resumen del problema (ej: Error al publicar anuncio)'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe con detalle el problema que estás teniendo...'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'asunto': 'Asunto',
            'descripcion': 'Descripción',
            'prioridad': 'Prioridad',
        }
