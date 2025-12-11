# usuarios/forms.py (CONTENIDO COMPLETO ACTUALIZADO)
from allauth.socialaccount.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from .models import (
    Comerciante, Post, Comentario, 
    RELACION_NEGOCIO_CHOICES, TIPO_NEGOCIO_CHOICES, 
    CATEGORIA_POST_CHOICES, INTERESTS_CHOICES
)

# =====================================================================
# OPCIONES DE COMUNA
# =====================================================================
COMUNA_CHOICES = [
    ('', 'Selecciona tu comuna'),
    # Región Metropolitana
    ('Santiago', 'Santiago'),
    ('Providencia', 'Providencia'),
    ('Las Condes', 'Las Condes'),
    ('Vitacura', 'Vitacura'),
    ('Ñuñoa', 'Ñuñoa'),
    ('La Reina', 'La Reina'),
    ('Peñalolén', 'Peñalolén'),
    ('Macul', 'Macul'),
    ('La Florida', 'La Florida'),
    ('Puente Alto', 'Puente Alto'),
    ('San Bernardo', 'San Bernardo'),
    ('Maipú', 'Maipú'),
    ('Pudahuel', 'Pudahuel'),
    ('Cerrillos', 'Cerrillos'),
    ('Estación Central', 'Estación Central'),
    ('Quinta Normal', 'Quinta Normal'),
    ('Recoleta', 'Recoleta'),
    ('Independencia', 'Independencia'),
    ('Conchalí', 'Conchalí'),
    ('Quilicura', 'Quilicura'),
    ('Renca', 'Renca'),
    ('Huechuraba', 'Huechuraba'),
    ('Cerro Navia', 'Cerro Navia'),
    ('Lo Prado', 'Lo Prado'),
    ('San Miguel', 'San Miguel'),
    ('La Cisterna', 'La Cisterna'),
    ('El Bosque', 'El Bosque'),
    ('Pedro Aguirre Cerda', 'Pedro Aguirre Cerda'),
    ('Lo Espejo', 'Lo Espejo'),
    ('La Granja', 'La Granja'),
    ('San Ramón', 'San Ramón'),
    ('La Pintana', 'La Pintana'),
    # Valparaíso
    ('Valparaíso', 'Valparaíso'),
    ('Viña del Mar', 'Viña del Mar'),
    ('Quilpué', 'Quilpué'),
    ('Villa Alemana', 'Villa Alemana'),
    ('Concón', 'Concón'),
    # Otras regiones principales
    ('Arica', 'Arica'),
    ('Iquique', 'Iquique'),
    ('Antofagasta', 'Antofagasta'),
    ('Calama', 'Calama'),
    ('Copiapó', 'Copiapó'),
    ('La Serena', 'La Serena'),
    ('Coquimbo', 'Coquimbo'),
    ('Rancagua', 'Rancagua'),
    ('Talca', 'Talca'),
    ('Curicó', 'Curicó'),
    ('Chillán', 'Chillán'),
    ('Concepción', 'Concepción'),
    ('Talcahuano', 'Talcahuano'),
    ('Los Ángeles', 'Los Ángeles'),
    ('Temuco', 'Temuco'),
    ('Valdivia', 'Valdivia'),
    ('Osorno', 'Osorno'),
    ('Puerto Montt', 'Puerto Montt'),
    ('Coyhaique', 'Coyhaique'),
    ('Punta Arenas', 'Punta Arenas'),
    ('OTRA', 'Otra (especificar en perfil)'),
]


# =====================================================================
# FORMULARIO DE REGISTRO TRADICIONAL
# =====================================================================
class RegistroComercianteForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mínimo 8 caracteres',
            'id': 'password',
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
        }),
        max_length=255
    )
    confirm_password = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repite la contraseña',
            'id': 'confirm-password',
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
        }),
        max_length=255
    )
    
    # REDEFINIR ESTOS CAMPOS EXPLÍCITAMENTE
    relacion_negocio = forms.ChoiceField(
        choices=[('', 'Selecciona una opción')] + list(RELACION_NEGOCIO_CHOICES),
        label='Relación con el negocio',
        required=True,
        widget=forms.Select(attrs={
            'id': 'id_relacion_negocio',
            'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#0d171b] dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary border border-[#cfdfe7] dark:border-gray-600 bg-background-light dark:bg-gray-800 focus:border-primary h-12 p-[15px] text-base font-normal leading-normal appearance-none cursor-pointer'
        })
    )
    
    tipo_negocio = forms.ChoiceField(
        choices=[('', 'Selecciona un tipo')] + list(TIPO_NEGOCIO_CHOICES),
        label='Tipo de negocio',
        required=True,
        widget=forms.Select(attrs={
            'id': 'id_tipo_negocio',
            'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#0d171b] dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary border border-[#cfdfe7] dark:border-gray-600 bg-background-light dark:bg-gray-800 focus:border-primary h-12 p-[15px] text-base font-normal leading-normal appearance-none cursor-pointer'
        })
    )
    
    comuna_select = forms.ChoiceField(
        choices=COMUNA_CHOICES,
        label='Comuna',
        required=True,
        widget=forms.Select(attrs={
            'id': 'id_comuna_select',
            'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-[#0d171b] dark:text-white focus:outline-0 focus:ring-2 focus:ring-primary border border-[#cfdfe7] dark:border-gray-600 bg-background-light dark:bg-gray-800 focus:border-primary h-12 p-[15px] text-base font-normal leading-normal appearance-none cursor-pointer'
        })
    )

    class Meta:
        model = Comerciante
        fields = (
            'nombre_apellido', 'email', 'whatsapp',
            # ❌ REMOVIDOS: 'relacion_negocio', 'tipo_negocio'
            # Porque los redefinimos arriba como ChoiceField
        )
        widgets = {
            'nombre_apellido': forms.TextInput(attrs={
                'placeholder': 'Ej: Juan Pérez',
                'id': 'fullname',
                'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'tucorreo@ejemplo.com',
                'id': 'email',
                'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
            }),
            'whatsapp': forms.TextInput(attrs={
                'placeholder': '+56912345678',
                'id': 'whatsapp',
                'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
            }),
            # ❌ REMOVIDOS: widgets de relacion_negocio y tipo_negocio
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Comerciante.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email.lower()

    def clean_whatsapp(self):
     whatsapp = self.cleaned_data.get('whatsapp')
    
     # ✅ Verificar primero si whatsapp existe
     if not whatsapp:
        raise ValidationError('El número de WhatsApp es obligatorio.')
    
    # Ahora sí podemos hacer las validaciones
     if not whatsapp.startswith('+569'):
        raise ValidationError('El WhatsApp debe comenzar con +569 seguido de 8 dígitos.')
    
     if len(whatsapp) != 12:
        raise ValidationError('El formato debe ser +569XXXXXXXX (12 caracteres).')
    
     return whatsapp

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Las contraseñas no coinciden.')
            elif len(password) < 8:
                self.add_error('password', 'La contraseña debe tener al menos 8 caracteres.')

        # Mapear comuna_select a comuna
        comuna = cleaned_data.get('comuna_select')
        if comuna:
            cleaned_data['comuna'] = comuna

        return cleaned_data

# =====================================================================
# FORMULARIO DE LOGIN
# =====================================================================
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none',
            'placeholder': 'tucorreo@ejemplo.com'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none',
            'placeholder': '••••••••'
        })
    )


# =====================================================================
# FORMULARIO DE REGISTRO SOCIAL (Google/Facebook)
# =====================================================================
class SocialSignupForm(SignupForm):
    """
    Formulario extendido para completar el registro después de autenticarse
    con Google o Facebook.
    """
    
    nombre_apellido = forms.CharField(
        max_length=100,
        required=True,
        label='Nombre y Apellido',
        widget=forms.TextInput(attrs={
            'placeholder': 'Juan Pérez',
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none transition-colors'
        }),
        error_messages={
            'required': 'El nombre y apellido es obligatorio.'
        }
    )
    
    whatsapp = forms.CharField(
        max_length=12,
        required=True,
        label='Número de WhatsApp',
        widget=forms.TextInput(attrs={
            'placeholder': '+56912345678',
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none transition-colors'
        }),
        help_text='Formato: +569XXXXXXXX',
        error_messages={
            'required': 'El número de WhatsApp es obligatorio.'
        }
    )
    
    relacion_negocio = forms.ChoiceField(
        choices=[('', 'Selecciona una opción')] + list(RELACION_NEGOCIO_CHOICES),
        required=True,
        label='Relación con el Negocio',
        widget=forms.Select(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none appearance-none bg-white cursor-pointer transition-colors'
        }),
        error_messages={
            'required': 'Debes seleccionar tu relación con el negocio.'
        }
    )
    
    tipo_negocio = forms.ChoiceField(
        choices=[('', 'Selecciona un tipo')] + list(TIPO_NEGOCIO_CHOICES),
        required=True,
        label='Tipo de Negocio',
        widget=forms.Select(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none appearance-none bg-white cursor-pointer transition-colors'
        }),
        error_messages={
            'required': 'Debes seleccionar el tipo de negocio.'
        }
    )
    
    comuna_select = forms.ChoiceField(
        choices=COMUNA_CHOICES,
        required=True,
        label='Comuna',
        widget=forms.Select(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none appearance-none bg-white cursor-pointer transition-colors'
        }),
        error_messages={
            'required': 'Debes seleccionar tu comuna.'
        }
    )

    def clean_whatsapp(self):
        """Validar formato de WhatsApp chileno"""
        whatsapp = self.cleaned_data.get('whatsapp')
        
        if not whatsapp:
            raise ValidationError('El número de WhatsApp es obligatorio.')
        
        # Limpiar espacios
        whatsapp = whatsapp.replace(' ', '').replace('-', '')
        
        # Validar formato
        if not whatsapp.startswith('+569'):
            raise ValidationError('El WhatsApp debe comenzar con +569')
        
        if len(whatsapp) != 12:
            raise ValidationError('El formato debe ser +569XXXXXXXX (12 caracteres)')
        
        # Validar que los últimos 8 caracteres sean dígitos
        if not whatsapp[4:].isdigit():
            raise ValidationError('Los últimos 8 caracteres deben ser números')
        
        return whatsapp

    def clean_nombre_apellido(self):
        """Validar que el nombre no esté vacío y tenga formato correcto"""
        nombre = self.cleaned_data.get('nombre_apellido', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre y apellido es obligatorio.')
        
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        
        return nombre

    def clean(self):
        """Validación adicional del formulario completo"""
        cleaned_data = super().clean()
        
        # Validar que todos los campos requeridos estén presentes
        required_fields = ['nombre_apellido', 'whatsapp', 'relacion_negocio', 'tipo_negocio', 'comuna_select']
        
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'Este campo es obligatorio.')
        
        return cleaned_data

    def save(self, request):
        """
        Guardar el usuario y crear el comerciante asociado
        """
        # Guardar el usuario de Django (creado por allauth)
        user = super().save(request)
        
        try:
            # Verificar si ya existe un comerciante con este email
            comerciante = Comerciante.objects.filter(email=user.email).first()
            
            if comerciante:
                # Actualizar comerciante existente
                comerciante.nombre_apellido = self.cleaned_data['nombre_apellido']
                comerciante.whatsapp = self.cleaned_data['whatsapp']
                comerciante.relacion_negocio = self.cleaned_data['relacion_negocio']
                comerciante.tipo_negocio = self.cleaned_data['tipo_negocio']
                comerciante.comuna = self.cleaned_data['comuna_select']
                comerciante.save()
            else:
                # Crear nuevo comerciante
                comerciante = Comerciante.objects.create(
                    email=user.email,
                    nombre_apellido=self.cleaned_data['nombre_apellido'],
                    whatsapp=self.cleaned_data['whatsapp'],
                    relacion_negocio=self.cleaned_data['relacion_negocio'],
                    tipo_negocio=self.cleaned_data['tipo_negocio'],
                    comuna=self.cleaned_data['comuna_select'],
                    password_hash='',  # Usuario social, sin contraseña tradicional
                    rol='COMERCIANTE',
                )
            
            # Asociar el user de Django con el comerciante si es necesario
            # (puedes agregar un campo user en el modelo Comerciante)
            
        except Exception as e:
            # Log del error para debugging
            print(f"Error al crear comerciante: {str(e)}")
            raise ValidationError(f'Error al crear el perfil: {str(e)}')
        
        return user


# =====================================================================
# FORMULARIOS DE POSTS
# =====================================================================
class PostForm(forms.ModelForm):
    uploaded_file = forms.FileField(
        required=False,
        label='Subir Archivo (Imagen/Documento)',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-input-file block w-full text-sm text-text-light file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20',
        })
    )

    url_link = forms.URLField(
        required=False,
        label='Link URL',
        widget=forms.URLInput(attrs={
            'placeholder': 'Opcional: URL de una imagen externa o link',
            'class': 'form-input flex w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary p-3'
        })
    )
    
    etiquetas_input = forms.CharField(
        required=False,
        label='Etiquetas',
        help_text='Etiqueta a otros usuarios o agrega hashtags, separados por coma',
        widget=forms.TextInput(attrs={
            'placeholder': '@usuario, #hashtag',
            'class': 'form-input flex w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary p-3'
        })
    )

    class Meta:
        model = Post
        fields = ('titulo', 'contenido', 'categoria') 
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Título',
                'class': 'form-input flex w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary p-3'
            }),
            'contenido': forms.Textarea(attrs={
                'placeholder': 'Escribe aquí el contenido de tu publicación...',
                'rows': 5,
                'class': 'form-input flex w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary p-3'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select flex w-full rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary p-3'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        url_link = cleaned_data.get('url_link')
        uploaded_file = cleaned_data.get('uploaded_file')
        
        if uploaded_file and url_link:
            raise ValidationError("Solo puedes subir un archivo O proporcionar un link URL, no ambos.")
            
        if url_link:
            cleaned_data['imagen_url'] = url_link
        
        etiquetas_input = cleaned_data.pop('etiquetas_input', None)
        if etiquetas_input:
            cleaned_data['etiquetas'] = etiquetas_input
        
        return cleaned_data


# =====================================================================
# FORMULARIOS DE PERFIL
# =====================================================================
class ProfilePhotoForm(forms.ModelForm):
    """Formulario para actualizar solo la foto de perfil."""
    class Meta:
        model = Comerciante
        fields = ['foto_perfil']
        

class BusinessDataForm(forms.ModelForm):
    """Formulario para actualizar los datos del negocio."""
    class Meta:
        model = Comerciante
        fields = ['relacion_negocio', 'tipo_negocio', 'comuna', 'nombre_negocio']
        
        widgets = {
            'relacion_negocio': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary'}),
            'tipo_negocio': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary'}),
            'comuna': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary', 'placeholder': 'Ej: Estación Central'}),
            'nombre_negocio': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary', 'placeholder': 'Ej: Minimarket El Sol'}),
        }


class ContactInfoForm(forms.ModelForm):
    """Formulario para actualizar el email y WhatsApp."""
    class Meta:
        model = Comerciante
        fields = ['email', 'whatsapp']
        
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary', 'placeholder': 'tu@correo.cl'}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary', 'placeholder': '+569XXXXXXXX'}),
        }


class InterestsForm(forms.Form):
    """Formulario para seleccionar múltiples intereses."""
    intereses = forms.MultipleChoiceField(
        choices=INTERESTS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Selecciona tus intereses"
    )


# =====================================================================
# FORMULARIO DE COMENTARIOS
# =====================================================================
class ComentarioForm(forms.ModelForm):
    """Formulario para añadir un nuevo comentario."""
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'placeholder': 'Escribe tu comentario...',
                'rows': 3,
                'class': 'w-full resize-none rounded-lg border border-gray-300 focus:ring-primary focus:border-primary p-3'
            }),
        }
        labels = {
            'contenido': 'Tu Comentario'
        }