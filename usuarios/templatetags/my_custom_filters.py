from django import template
from django.utils.safestring import mark_safe # <-- Necesario si fuera a inyectar HTML, pero lo usaremos para lógica.

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