from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Proveedor,
    ProductoServicio,
    Promocion,
    SolicitudContacto,
    CategoriaProveedor,
    Region,
    Comuna
)


class ProveedorForm(forms.ModelForm):
    """
    Formulario para crear y editar el perfil del proveedor
    """
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
            'nombre_empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de tu empresa',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe tu negocio, productos y servicios que ofreces...',
                'required': True
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'categorias': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'pais': forms.Select(attrs={
                'class': 'form-control'
            }),
            'region': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_region'
            }),
            'comuna': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_comuna'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección de tu negocio'
            }),
            'cobertura': forms.Select(attrs={
                'class': 'form-control'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56912345678',
                'required': True
            }),
            'sitio_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.tuempresa.cl'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/tuempresa'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@tuempresa'
            }),
            'twitter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@tuempresa'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/company/tuempresa'
            }),
        }
        labels = {
            'nombre_empresa': 'Nombre de la Empresa *',
            'descripcion': 'Descripción del Negocio *',
            'foto': 'Logo/Foto de la Empresa',
            'categorias': 'Rubros que ofreces *',
            'pais': 'País',
            'region': 'Región',
            'comuna': 'Comuna',
            'direccion': 'Dirección',
            'cobertura': 'Zona de Cobertura *',
            'telefono': 'Teléfono',
            'whatsapp': 'WhatsApp *',
            'sitio_web': 'Sitio Web',
            'facebook': 'Facebook',
            'instagram': 'Instagram',
            'twitter': 'Twitter / X',
            'linkedin': 'LinkedIn',
        }
        help_texts = {
            'descripcion': 'Describe qué productos o servicios ofreces y qué te hace especial.',
            'categorias': 'Selecciona todos los rubros que apliquen a tu negocio.',
            'cobertura': 'Área geográfica donde ofreces tus servicios.',
            'whatsapp': 'Principal medio de contacto para los comerciantes.',
            'instagram': 'Ingresa solo el nombre de usuario sin @',
            'twitter': 'Ingresa solo el nombre de usuario sin @',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si hay una instancia, filtrar comunas por región
        if self.instance.pk and self.instance.region:
            self.fields['comuna'].queryset = Comuna.objects.filter(
                region=self.instance.region
            )
        else:
            self.fields['comuna'].queryset = Comuna.objects.none()
        
        # Hacer que la imagen no sea requerida en edición
        if self.instance.pk:
            self.fields['foto'].required = False

    def clean_instagram(self):
        """Limpiar el campo Instagram para quitar @ si lo incluye"""
        instagram = self.cleaned_data.get('instagram', '')
        if instagram:
            instagram = instagram.strip().replace('@', '')
        return instagram

    def clean_twitter(self):
        """Limpiar el campo Twitter para quitar @ si lo incluye"""
        twitter = self.cleaned_data.get('twitter', '')
        if twitter:
            twitter = twitter.strip().replace('@', '')
        return twitter

    def clean_categorias(self):
        """Validar que se seleccione al menos una categoría"""
        categorias = self.cleaned_data.get('categorias')
        if not categorias or categorias.count() == 0:
            raise ValidationError('Debes seleccionar al menos un rubro.')
        return categorias

    def clean(self):
        """Validaciones adicionales"""
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        comuna = cleaned_data.get('comuna')
        
        # Validar que la comuna pertenezca a la región seleccionada
        if region and comuna:
            if comuna.region != region:
                raise ValidationError('La comuna seleccionada no pertenece a la región.')
        
        return cleaned_data


class ProductoServicioForm(forms.ModelForm):
    """
    Formulario para crear y editar productos/servicios del proveedor
    """
    class Meta:
        model = ProductoServicio
        fields = [
            'nombre',
            'descripcion',
            'precio_referencia',
            'imagen',
            'destacado',
            'activo',
            'categoria',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto o servicio',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe las características y beneficios...',
                'required': True
            }),
            'precio_referencia': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'destacado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),

        }
        labels = {
            'nombre': 'Nombre del Producto/Servicio *',
            'descripcion': 'Descripción *',
            'precio_referencia': 'Precio Referencial',
            'imagen': 'Imagen',
            'destacado': 'Producto Destacado',
            'activo': 'Activo',
            'categoria': 'Categoría ',
        }
        help_texts = {
            'precio_referencia': 'Precio aproximado en pesos chilenos (opcional).',
            'destacado': 'Los productos destacados aparecen primero en tu perfil.',
            'activo': 'Desmarca esta opción para ocultar temporalmente el producto.',
        }

    def clean_precio_referencia(self):
        """Validar que el precio sea positivo"""
        precio = self.cleaned_data.get('precio_referencia')
        if precio is not None and precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio


class PromocionForm(forms.ModelForm):
    """
    Formulario para crear y editar promociones
    """
    class Meta:
        model = Promocion
        fields = [
            'titulo',
            'descripcion',
            'imagen',
            'fecha_inicio',
            'fecha_fin',
            'activo',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la promoción',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe la promoción y sus condiciones...',
                'required': True
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'titulo': 'Título de la Promoción *',
            'descripcion': 'Descripción *',
            'imagen': 'Imagen de la Promoción',
            'fecha_inicio': 'Fecha de Inicio *',
            'fecha_fin': 'Fecha de Fin *',
            'activo': 'Promoción Activa',
        }
        help_texts = {
            'fecha_inicio': 'Fecha en que comienza la promoción.',
            'fecha_fin': 'Fecha en que termina la promoción.',
            'activo': 'Desmarca para pausar temporalmente la promoción.',
        }

    def clean(self):
        """Validar fechas de la promoción"""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            # Validar que la fecha de fin sea posterior a la de inicio
            if fecha_fin < fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
            
            # Validar que la fecha de fin no sea en el pasado (solo para nuevas promociones)
            if not self.instance.pk:
                hoy = timezone.now().date()
                if fecha_fin < hoy:
                    raise ValidationError({
                        'fecha_fin': 'La fecha de fin no puede ser en el pasado.'
                    })
        
        return cleaned_data


class SolicitudContactoForm(forms.ModelForm):
    """
    Formulario para enviar solicitudes de contacto a comercios
    """
    class Meta:
        model = SolicitudContacto
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Escribe un mensaje de presentación para el comerciante...\n\nEjemplo: Hola, soy proveedor de [producto/servicio] y me gustaría conectar contigo para ofrecerte...',
                'required': True
            }),
        }
        labels = {
            'mensaje': 'Mensaje de Presentación *',
        }
        help_texts = {
            'mensaje': 'Presenta tu empresa y explica qué puedes ofrecer al comerciante. Sé claro y profesional.',
        }

    def clean_mensaje(self):
        """Validar longitud mínima del mensaje"""
        mensaje = self.cleaned_data.get('mensaje', '')
        if len(mensaje.strip()) < 20:
            raise ValidationError('El mensaje debe tener al menos 20 caracteres.')
        if len(mensaje) > 1000:
            raise ValidationError('El mensaje no puede superar los 1000 caracteres.')
        return mensaje.strip()


class BusquedaProveedorForm(forms.Form):
    """
    Formulario de búsqueda y filtros para el directorio de proveedores
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar proveedores...',
        }),
        label='Búsqueda'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaProveedor.objects.filter(activo=True),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Categoría'
    )
    
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        empty_label='Todas las regiones',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'filtro_region'
        }),
        label='Región'
    )
    
    comuna = forms.ModelChoiceField(
        queryset=Comuna.objects.none(),
        required=False,
        empty_label='Todas las comunas',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'filtro_comuna'
        }),
        label='Comuna'
    )
    
    cobertura = forms.ChoiceField(
        choices=[('', 'Todas las coberturas')] + Proveedor.COBERTURA_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Cobertura'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si hay una región seleccionada, filtrar comunas
        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['comuna'].queryset = Comuna.objects.filter(
                    region_id=region_id
                ).order_by('nombre')
            except (ValueError, TypeError):
                pass


class ContactoProveedorForm(forms.Form):
    """
    Formulario simple de contacto directo (alternativo)
    """
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre',
            'required': True
        }),
        label='Nombre'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'required': True
        }),
        label='Email'
    )
    
    telefono = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+56912345678'
        }),
        label='Teléfono'
    )
    
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Escribe tu mensaje...',
            'required': True
        }),
        label='Mensaje'
    )
    
    def clean_mensaje(self):
        mensaje = self.cleaned_data.get('mensaje', '')
        if len(mensaje.strip()) < 10:
            raise ValidationError('El mensaje debe tener al menos 10 caracteres.')
        return mensaje.strip()

class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'foto_perfil',
            'modo_oscuro',
            'notif_email',
            'notif_mensajes', 
            'notif_pedidos',
            'idioma',
            'zona_horaria',
            'perfil_publico',
            'mostrar_estadisticas'
        ]
        widgets = {
            'foto_perfil': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'idioma': forms.Select(attrs={'class': 'form-control'}),
            'zona_horaria': forms.Select(attrs={'class': 'form-control'}),
        }