# administrador/forms.py

from django import forms
from django.contrib.auth.hashers import make_password
from usuarios.models import Comerciante, Beneficio, Post


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
            'comerciante',   # para asignar a qué comerciante pertenece
        ]
