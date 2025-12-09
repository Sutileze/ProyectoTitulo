# administrador/forms.py

from django import forms
from django.contrib.auth.hashers import make_password
from usuarios.models import Comerciante, Beneficio, Post, Aviso
from django.forms import DateInput # Importar DateInput para el widget de fecha



class ComercianteAdminForm(forms.ModelForm):
    raw_password = forms.CharField(
        required=False,
        label="Contraseña nueva",
        widget=forms.PasswordInput
    )

    class Meta:
        model = Comerciante
        fields = [
            'nombre_apellido',
            'email',
            'whatsapp',
            'relacion_negocio',
            'tipo_negocio',
            'comuna',
            'nombre_negocio',
            'rol',
            'es_proveedor',      # 👈 importante para el flujo proveedor
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)

        password = self.cleaned_data.get('raw_password')
        if password:
            instance.password_hash = make_password(password)

        if commit:
            instance.save()

        return instance


# 🔹 FORMULARIO PARA BENEFICIOS
class BeneficioAdminForm(forms.ModelForm):
    class Meta:
        model = Beneficio
        fields = [
            'titulo',
            'descripcion',
            'foto',
            'vence',
            'categoria',
            'estado',
        ]


# 🔹 FORMULARIO PARA POSTS
class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'titulo',
            'contenido',
            'categoria',
            'imagen_url',
            'etiquetas',
        ] 
    def __init__(self, *args, **kwargs):
        admin_category_choices = kwargs.pop('admin_category_choices', None)
        
        super().__init__(*args, **kwargs)

        if admin_category_choices is not None:
            self.fields['categoria'].choices = admin_category_choices

class AvisoForm(forms.ModelForm):
    """Formulario para que el administrador cree y edite Avisos."""
    class Meta:
        model = Aviso
        fields = ['titulo', 'contenido', 'tipo', 'fecha_caducidad']
        widgets = {
            # Usar DateInput para mejorar la experiencia de usuario en la selección de la fecha
            'fecha_caducidad': DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'titulo': forms.TextInput(attrs={'class': 'form-input'}),
            'contenido': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'fecha_caducidad': 'Fecha de Caducidad (Opcional)',
        }