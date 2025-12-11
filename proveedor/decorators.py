

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps



def proveedor_login_required(function):
    """
    Decorador para requerir que el proveedor esté logueado.
    Verifica la variable global current_logged_in_proveedor.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        from proveedor.views import current_logged_in_proveedor
        
        if not current_logged_in_proveedor:
            messages.error(request, "Debes iniciar sesión como proveedor.")
            return redirect('proveedores:login_proveedor')
        
        return function(request, *args, **kwargs)
    
    return wrap