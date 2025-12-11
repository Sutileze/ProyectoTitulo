# proveedores/urls.py

from django.urls import path
from . import views

app_name = 'proveedores'

urlpatterns = [
    # ==================== AUTENTICACIÓN ====================
    path('login/', views.login_proveedor_view, name='login_proveedor'),
    path('registro/', views.registro_proveedor_view, name='registro_proveedor'),
    path('logout/', views.logout_proveedor_view, name='logout_proveedor'),
    
    # ==================== VISTAS PÚBLICAS ====================
    path('', views.directorio_proveedores, name='directorio_proveedores'),
    path('<int:proveedor_id>/', views.detalle_proveedor, name='detalle_proveedor'),
    
    # ==================== PANEL DEL PROVEEDOR ====================
    path('dashboard/', views.dashboard_proveedor, name='dashboard_proveedor'),
    path('perfil/editar/', views.editar_perfil_proveedor, name='editar_perfil_proveedor'),
    
    # ==================== PRODUCTOS ====================
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/<int:producto_id>/toggle-destacado/', views.toggle_destacado_producto, name='toggle_destacado_producto'),
    
    # ==================== PROMOCIONES ====================
    path('promociones/', views.lista_promociones, name='lista_promociones'),
    path('promociones/crear/', views.crear_promocion, name='crear_promocion'),
    path('promociones/<int:promocion_id>/editar/', views.editar_promocion, name='editar_promocion'),
    path('promociones/<int:promocion_id>/eliminar/', views.eliminar_promocion, name='eliminar_promocion'),
    
    # ==================== SOLICITUDES ====================
    path('solicitudes/enviar/', views.enviar_solicitud_contacto, name='enviar_solicitud_contacto'),
    path('solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
    
    # ==================== AJAX ====================
    path('ajax/comunas/', views.get_comunas_ajax, name='get_comunas_ajax'),
    path('ajax/regiones/', views.get_regiones_ajax, name='ajax_regiones'),
    
]