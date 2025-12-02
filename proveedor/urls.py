"""
URLs para el módulo de Proveedores
Incluir en el urls.py principal del proyecto con:
    path('proveedores/', include('proveedores.urls')),
"""

from django.urls import path
from . import views

app_name = 'proveedores'

urlpatterns = [
    # ==================== VISTAS PÚBLICAS ====================
    
    # Directorio público de proveedores
    path('', views.directorio_proveedores, name='directorio_proveedores'),
    
    # Detalle público de un proveedor
    path('<int:proveedor_id>/', views.detalle_proveedor, name='detalle_proveedor'),
    
    
    # ==================== PANEL DEL PROVEEDOR ====================
    
    # Dashboard del proveedor
    path('panel/', views.perfil_proveedor, name='perfil_proveedor'),
    
    # Crear perfil de proveedor (primera vez)
    path('panel/crear/', views.crear_perfil_proveedor, name='crear_perfil_proveedor'),
    
    # Editar perfil del proveedor
    path('panel/editar/', views.editar_perfil_proveedor, name='editar_perfil_proveedor'),
    
    
    # ==================== GESTIÓN DE PRODUCTOS/SERVICIOS ====================
    
    # Lista de productos del proveedor
    path('panel/productos/', views.lista_productos, name='lista_productos'),
    
    # Crear nuevo producto/servicio
    path('panel/productos/crear/', views.crear_producto, name='crear_producto'),
    
    # Editar producto/servicio
    path('panel/productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    
    # Eliminar producto/servicio
    path('panel/productos/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    
    # Toggle destacado de producto (AJAX)
    path('panel/productos/<int:producto_id>/toggle-destacado/', views.toggle_destacado_producto, name='toggle_destacado_producto'),
    
    
    # ==================== GESTIÓN DE PROMOCIONES ====================
    
    # Lista de promociones del proveedor
    path('panel/promociones/', views.lista_promociones, name='lista_promociones'),
    
    # Crear nueva promoción
    path('panel/promociones/crear/', views.crear_promocion, name='crear_promocion'),
    
    # Editar promoción
    path('panel/promociones/<int:promocion_id>/editar/', views.editar_promocion, name='editar_promocion'),
    
    # Eliminar promoción
    path('panel/promociones/<int:promocion_id>/eliminar/', views.eliminar_promocion, name='eliminar_promocion'),
    
    
    # ==================== SOLICITUDES DE CONTACTO ====================
    
    # Enviar solicitud de contacto a un comercio
    path('panel/solicitudes/enviar/<int:comercio_id>/', views.enviar_solicitud_contacto, name='enviar_solicitud_contacto'),
    
    # Lista de solicitudes enviadas por el proveedor
    path('panel/solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
    
    
    # ==================== AJAX/API ====================
    
    # Obtener comunas de una región (para filtros dinámicos)
    path('ajax/comunas/', views.get_comunas_ajax, name='get_comunas_ajax'),

    # ==================== CONFIGURACION ====================
    path('configuracion/', views.configuracion_proveedor, name='configuracion'),
    path('confguracion/eliminar_foto/', views.eliminar_foto_perfil, name='eliminar_foto_perfil'),

]