# usuarios/forms.py (CONTENIDO COMPLETO)
from allauth.socialaccount.forms import SignupForm
from django import forms
from .models import (
    Comerciante, Post, Comentario, 
    RELACION_NEGOCIO_CHOICES, TIPO_NEGOCIO_CHOICES, 
    CATEGORIA_POST_CHOICES, INTERESTS_CHOICES
) 
# Opciones de comuna
COMUNA_CHOICES = [
    ('', 'Selecciona tu comuna'),
    ('ARICA', 'Arica'),
    ('SANTIAGO', 'Santiago'),
    ('PROVIDENCIA', 'Providencia'),
    ('LA_SERENA', 'La Serena'),
    ('VALPARAISO', 'Valparaíso'),
    ('OTRO_COMUNA', '...'),
]

class RegistroComercianteForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres', 'id': 'password'}),
        max_length=255
    )
    confirm_password = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la contraseña', 'id': 'confirm-password'}),
        max_length=255
    )
    comuna_select = forms.ChoiceField(
        choices=COMUNA_CHOICES,
        label='Comuna',
        widget=forms.Select(attrs={'id': 'commune'})
    )

    class Meta:
        model = Comerciante
        fields = (
            'nombre_apellido', 'email', 'whatsapp',
            'relacion_negocio', 'tipo_negocio',
        )
        widgets = {
            'nombre_apellido': forms.TextInput(attrs={'placeholder': 'Ej: Juan Pérez', 'id': 'fullname'}),
            'email': forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com', 'id': 'email'}),
            'whatsapp': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678', 'id': 'whatsapp'}),
            'relacion_negocio': forms.Select(attrs={'id': 'business-relation'}),
            'tipo_negocio': forms.Select(attrs={'id': 'business-type'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Las contraseñas no coinciden.')

        if password and len(password) < 8:
            self.add_error('password', 'La contraseña debe tener al menos 8 caracteres.')

        comuna = cleaned_data.get('comuna_select')
        cleaned_data['comuna'] = comuna

        return cleaned_data

# ✅ Formulario de Login separado
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu correo'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
    )

# -------------------------------------------------------------------------------------
class PostForm(forms.ModelForm):
    # Campo para subida de archivo desde PC (NUEVA FUNCIONALIDAD)
    uploaded_file = forms.FileField(
        required=False,
        label='Subir Archivo (Imagen/Documento)',
        widget=forms.ClearableFileInput(attrs={
            # Estilos de Tailwind para el campo de archivo
            'class': 'form-input-file block w-full text-sm text-text-light file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 dark:file:bg-primary dark:file:text-white',
        })
    )

    # Campo para link/URL externo (NUEVA FUNCIONALIDAD)
    url_link = forms.URLField(
        required=False,
        label='Link URL',
        widget=forms.URLInput(attrs={
            'placeholder': 'Opcional: URL de una imagen externa o link',
            'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-light dark:text-text-dark focus:outline-0 focus:ring-2 focus:ring-primary border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:border-primary h-12 placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark p-[10px] text-base font-normal leading-normal'
        })
    )
    
    # Campo para etiquetas (se mantiene)
    etiquetas_input = forms.CharField(
        required=False,
        label='Etiquetas',
        help_text='Etiqueta a otros usuarios o agrega hashtags, separados por coma (ej: @JuanPerez, #Marketing)',
        widget=forms.TextInput(attrs={
            'placeholder': '@usuario, #hashtag',
            'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-light dark:text-text-dark focus:outline-0 focus:ring-2 focus:ring-primary border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:border-primary h-12 placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark p-[10px] text-base font-normal leading-normal'
        })
    )

    class Meta:
        model = Post
        fields = ('titulo', 'contenido', 'categoria') 
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Titulo',
                'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-light dark:text-text-dark focus:outline-0 focus:ring-2 focus:ring-primary border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:border-primary h-12 placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark p-[10px] text-base font-normal leading-normal'
            }),
            'contenido': forms.Textarea(attrs={
                'placeholder': 'Escribe aquí el contenido de tu publicación...',
                'rows': 5,
                'class': 'form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-text-light dark:text-text-dark focus:outline-0 focus:ring-2 focus:ring-primary border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:border-primary placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark p-[10px] text-base font-normal leading-normal'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select flex w-full min-w-0 flex-1 rounded-lg text-text-light dark:text-text-dark focus:outline-0 focus:ring-2 focus:ring-primary border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:border-primary h-12 placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark p-[10px] text-base font-normal leading-normal'
            }, choices=CATEGORIA_POST_CHOICES),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        url_link = self.cleaned_data.get('url_link')
        uploaded_file = self.cleaned_data.get('uploaded_file')
        etiquetas_input = self.cleaned_data.pop('etiquetas_input', None)

        if uploaded_file and url_link:
            self.add_error(None, "Solo puedes subir un archivo O proporcionar un link URL, no ambos.")
            
        if url_link:
            cleaned_data['imagen_url'] = url_link
        
        if etiquetas_input:
            cleaned_data['etiquetas'] = etiquetas_input
        
        return cleaned_data
    
class ProfilePhotoForm(forms.ModelForm):
    """Formulario para actualizar solo la foto de perfil."""
    class Meta:
        model = Comerciante
        fields = ['foto_perfil']
        
class BusinessDataForm(forms.ModelForm):
    """Formulario para actualizar los datos del negocio (Relación, Tipo, Comuna, Nombre)."""
    class Meta:
        model = Comerciante
        fields = ['relacion_negocio', 'tipo_negocio', 'comuna', 'nombre_negocio']
        
        widgets = {
            'relacion_negocio': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-white'}),
            'tipo_negocio': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-white'}),
            'comuna': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-white', 'placeholder': 'Ej: Estación Central'}),
            'nombre_negocio': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-white', 'placeholder': 'Ej: Minimarket El Sol'}),
        }

class ContactInfoForm(forms.ModelForm):
    """Formulario para actualizar el email y WhatsApp."""
    class Meta:
        model = Comerciante
        fields = ['email', 'whatsapp']
        
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-white', 'placeholder': 'tu@correo.cl'}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-white', 'placeholder': '+569XXXXXXXX'}),
        }

class InterestsForm(forms.Form):
    """Formulario para seleccionar múltiples intereses de la lista definida."""
    
    intereses = forms.MultipleChoiceField(
        choices=INTERESTS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Selecciona tus intereses"
    )

# --- FORMULARIO DE COMENTARIOS RESTAURADO ---

class ComentarioForm(forms.ModelForm):
    """Formulario para añadir un nuevo comentario."""
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'placeholder': 'Escribe tu comentario...',
                'rows': 3,
                'class': 'w-full resize-none rounded-lg border border-gray-300 dark:border-gray-600 focus:ring-primary focus:border-primary p-[10px] text-base'
            }),
        }
        labels = {
            'contenido': 'Tu Comentario'
        }


class SocialSignupForm(SignupForm):
    nombre_apellido = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Juan Pérez',
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
        })
    )
    
    whatsapp = forms.CharField(
        max_length=12,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '+56912345678',
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none'
        })
    )
    
    relacion_negocio = forms.ChoiceField(
        choices=[
            ('', 'Selecciona una opción'),
            ('DUENO', 'Dueño/a'),
            ('SOCIO', 'Socio/a'),
            ('EMPLEADO', 'Empleado/a'),
            ('FAMILIAR', 'Familiar'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none appearance-none bg-white'
        })
    )
    
    tipo_negocio = forms.ChoiceField(
        choices=[
            ('', 'Selecciona un tipo'),
            ('ALMACEN', 'Almacén'),
            ('MINIMARKET', 'Minimarket'),
            ('KIOSCO', 'Kiosco'),
            ('BOTILLERIA', 'Botillería'),
            ('OTRO', 'Otro'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none appearance-none bg-white'
        })
    )
    
    comuna_select = forms.ChoiceField(
        choices=[
            ('', 'Selecciona tu comuna'),
            ('Santiago', 'Santiago'),
            ('Las Condes', 'Las Condes'),
            ('Providencia', 'Providencia'),
            ('Maipú', 'Maipú'),
            ('La Florida', 'La Florida'),
            ('Puente Alto', 'Puente Alto'),
            # Agregar más comunas
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:border-primary focus:outline-none appearance-none bg-white'
        })
    )

    def save(self, request):
        user = super().save(request)
        
        # Crear o actualizar el comerciante
        comerciante, created = Comerciante.objects.get_or_create(
            email=user.email,
            defaults={
                'nombre_apellido': self.cleaned_data['nombre_apellido'],
                'whatsapp': self.cleaned_data['whatsapp'],
                'relacion_negocio': self.cleaned_data['relacion_negocio'],
                'tipo_negocio': self.cleaned_data['tipo_negocio'],
                'comuna': self.cleaned_data['comuna_select'],
            }
        )
        
        return user