from django import template
from django.utils.safestring import mark_safe # <-- Necesario si fuera a inyectar HTML, pero lo usaremos para lógica.
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acceder a un valor de un diccionario por su clave."""
    if key in dictionary:
        return dictionary.get(key)
    return key
    
@register.filter
def add(value, arg):
    """Suma el argumento al valor."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except TypeError:
            return value

@register.filter
def split(value, arg):
    """Divide una cadena por el argumento dado."""
    if value is None:
        return []
    return value.split(arg)

@register.filter
def trim(value):
    """Elimina los espacios en blanco iniciales y finales de una cadena."""
    if isinstance(value, str):
        return value.strip()
    return value
    
@register.filter
def first_word_to_icon(value):
    """Convierte la primera palabra del tipo de notificación en un icono Material Symbols."""
    if not isinstance(value, str):
        return 'notifications_active'
        
    first_word = value.split()[0].lower()
    
    # Mapeo basado en tus categorías:
    if 'beneficio' in first_word or 'puntos' in first_word:
        return 'redeem'
    elif 'invitación' in first_word:
        return 'event'
    elif 'contenido' in first_word or 'sociales' in first_word:
        return 'videocam'
    elif 'reunión' in first_word or 'reunion' in first_word:
        return 'groups'
    else:
        return 'notifications_active' # Ícono por defecto

def first_word_to_icon(value):
    """Convierte la primera palabra del tipo de notificación en un icono Material Symbols."""
    if not isinstance(value, str):
        return 'notifications_active'
        
    word = value.lower().split()[0]
    
    # Mapeo basado en categorías de Aviso:
    if 'capacitacion' in word:
        return 'school'
    elif 'evento' in word:
        return 'event'
    elif 'sorteo' in word or 'concurso' in word:
        return 'emoji_events'
    elif 'general' in word or 'aviso' in word:
        return 'campaign' # Icono para avisos generales
    else:
        return 'notifications_active' # Icono por defecto
    
def first_word_to_icon(value):
    """Convierte el tipo de notificación en un icono Material Symbols."""
    if not value:
        return 'notifications_active'
        
    word = value.lower().split()[0]
    
    if 'capacitacion' in word:
        return 'school'       
    elif 'evento' in word:
        return 'event'        
    elif 'sorteo' in word or 'concurso' in word:
        return 'emoji_events' 
    elif 'general' in word or 'aviso' in word:
        return 'campaign'     
    else:
        return 'notifications_active' 

@register.filter
@stringfilter
def first_word_to_color_class(value):
    """Asigna una clase de color (Tailwind CSS) al tipo de notificación."""
    if not value:
        return 'text-primary' 
        
    word = value.lower().split()[0]
    
    if 'capacitacion' in word:
        return 'text-indigo-500' # Púrpura/Azul para Educación
    elif 'evento' in word:
        return 'text-green-500'  # Verde para Eventos
    elif 'sorteo' in word or 'concurso' in word:
        return 'text-yellow-500' # Amarillo/Dorado para Premios
    elif 'general' in word or 'aviso' in word:
        return 'text-red-500'    # Rojo/Naranja para Urgente
    else:
        return 'text-primary'

@register.filter
@stringfilter
def first_word_to_raw_color(value):
    """Devuelve la base del nombre del color (ej: 'red-500') para clases dinámicas."""
    if not value:
        return 'primary' 
        
    word = value.lower().split()[0]
    
    if 'capacitacion' in word:
        return 'indigo-500' # Base del color para Educación
    elif 'evento' in word:
        return 'green-500'  # Base del color para Eventos
    elif 'sorteo' in word or 'concurso' in word:
        return 'yellow-500' # Base del color para Premios
    elif 'general' in word or 'aviso' in word:
        return 'red-500'    # Base del color para Urgente
    else:
        return 'primary' # Base del color por defecto