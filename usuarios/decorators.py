# usuarios/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def comerciante_login_required(function):
    """
    Decorador para requerir que el comerciante esté logueado.
    Verifica la variable global current_logged_in_user.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        from usuarios.views import current_logged_in_user
        
        if not current_logged_in_user:
            messages.error(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('registro')  # Redirige a tu página de login
        
        return function(request, *args, **kwargs)
    
    return wrap