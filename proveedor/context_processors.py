# proveedores/context_processors.py

def proveedor_context(request):
    """
    Context processor para hacer disponible el proveedor logueado
    en todos los templates
    """
    from proveedor.views import current_logged_in_proveedor
    
    return {
        'current_logged_in_proveedor': current_logged_in_proveedor
    }