from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import (
    Proveedor,
    ProductoServicio,
    Promocion,
    SolicitudContacto,
    CategoriaProveedor,
    PAISES_CHOICES,
    REGIONES_CHOICES,
    COMUNAS_CHOICES,
    REGIONES_POR_PAIS,
    COMUNAS_POR_REGION,
)


# ==================== FORMULARIOS DE AUTENTICACIÓN ====================

class LoginProveedorForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'proveedor@empresa.com'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )


class RegistroProveedorForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mínimo 8 caracteres',
            'class': 'form-control'
        }),
        max_length=255
    )
    confirm_password = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repite la contraseña',
            'class': 'form-control'
        }),
        max_length=255
    )
    
    # Redefinir campos de ubicación como ChoiceField
    pais = forms.ChoiceField(
        choices=PAISES_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_pais'})
    )
    region = forms.ChoiceField(
        choices=[('', 'Primero selecciona un país')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_region'})
    )
    comuna = forms.ChoiceField(
        choices=[('', 'Primero selecciona una región')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_comuna'})
    )
    
    class Meta:
        model = Proveedor
        fields = [
            'nombre_contacto', 'email', 'nombre_empresa', 'descripcion',
            'whatsapp', 'telefono', 'sitio_web',
            'pais', 'region', 'comuna', 'direccion', 'cobertura',
            'facebook', 'instagram', 'twitter', 'linkedin',
            'foto_perfil'
        ]
        widgets = {
            'nombre_contacto': forms.TextInput(attrs={
                'placeholder': 'Juan Pérez',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'proveedor@empresa.com',
                'class': 'form-control'
            }),
            'nombre_empresa': forms.TextInput(attrs={
                'placeholder': 'Mi Empresa SPA',
                'class': 'form-control'
            }),
            'whatsapp': forms.TextInput(attrs={
                'placeholder': '+56912345678',
                'class': 'form-control'
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '+56912345678 (opcional)',
                'class': 'form-control'
            }),
            'sitio_web': forms.URLInput(attrs={
                'placeholder': 'https://www.tuempresa.com',
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'placeholder': 'Describe tu empresa y servicios...',
                'rows': 4,
                'class': 'form-control'
            }),
            'direccion': forms.TextInput(attrs={
                'placeholder': 'Calle Principal 123, Of. 45',
                'class': 'form-control'
            }),
            'cobertura': forms.Select(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={
                'placeholder': 'https://facebook.com/tupagina',
                'class': 'form-control'
            }),
            'instagram': forms.TextInput(attrs={
                'placeholder': '@tuempresa',
                'class': 'form-control'
            }),
            'twitter': forms.TextInput(attrs={
                'placeholder': '@tuempresa',
                'class': 'form-control'
            }),
            'linkedin': forms.URLInput(attrs={
                'placeholder': 'https://linkedin.com/company/tuempresa',
                'class': 'form-control'
            }),
            'foto_perfil': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si hay un país seleccionado en POST, cargar sus regiones
        if 'pais' in self.data:
            pais_code = self.data.get('pais')
            if pais_code and pais_code in REGIONES_POR_PAIS:
                self.fields['region'].choices = [('', 'Selecciona una región')] + REGIONES_POR_PAIS[pais_code]
        
        # Si hay una región seleccionada en POST, cargar sus comunas
        if 'region' in self.data:
            region_code = self.data.get('region')
            if region_code and region_code in COMUNAS_POR_REGION:
                self.fields['comuna'].choices = [('', 'Selecciona una comuna')] + COMUNAS_POR_REGION[region_code]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Proveedor.objects.filter(email=email).exists():
            raise ValidationError('Este correo ya está registrado.')
        return email.lower()
    
    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if not whatsapp:
            raise ValidationError('El número de WhatsApp es obligatorio.')
        return whatsapp
    
    def clean_foto_perfil(self):
        foto = self.cleaned_data.get('foto_perfil')
        if foto:
            # Validar tamaño (máximo 5MB)
            if foto.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede superar los 5MB.')
            
            # Validar tipo de archivo
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = foto.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Solo se permiten imágenes JPG, PNG o WEBP.')
        
        return foto
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Las contraseñas no coinciden.')
            elif len(password) < 8:
                self.add_error('password', 'La contraseña debe tener al menos 8 caracteres.')
        
        return cleaned_data


# ==================== FORMULARIOS DE GESTIÓN ====================

class ProveedorForm(forms.ModelForm):
    """Formulario para editar perfil del proveedor"""
    
    pais = forms.ChoiceField(
        choices=PAISES_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    region = forms.ChoiceField(
        choices=REGIONES_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    comuna = forms.ChoiceField(
        choices=COMUNAS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Proveedor
        fields = [
            'nombre_empresa',
            'descripcion',
            'foto',
            'categorias',
            'pais',
            'region',
            'comuna',
            'direccion',
            'cobertura',
            'telefono',
            'whatsapp',
            'sitio_web',
            'facebook',
            'instagram',
            'twitter',
            'linkedin',
        ]
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de tu empresa'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'categorias': forms.CheckboxSelectMultiple(),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'cobertura': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control'}),
            'twitter': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
        }


class ProductoServicioForm(forms.ModelForm):
    """Formulario para productos/servicios"""
    class Meta:
        model = ProductoServicio
        fields = ['nombre', 'descripcion', 'precio_referencia', 'imagen', 'destacado', 'activo', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio_referencia': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'destacado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }


class PromocionForm(forms.ModelForm):
    """Formulario para promociones"""
    class Meta:
        model = Promocion
        fields = ['titulo', 'descripcion', 'imagen', 'fecha_inicio', 'fecha_fin', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SolicitudContactoForm(forms.ModelForm):
    """Formulario para solicitudes de contacto"""
    class Meta:
        model = SolicitudContacto
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }


