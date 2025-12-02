# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('perfil/', views.perfil_view, name='perfil'),
    path('plataforma/', views.plataforma_comerciante_view, name='plataforma_comerciante'),
    path('publicar/', views.publicar_post_view, name='publicar_post'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('post/<int:post_id>/comentario/', views.add_comment_view, name='add_comment'),
    path('post/<int:post_id>/like/', views.like_post_view, name='like_post'),
        # PLATFORM/FORUM
    path('plataforma/', views.plataforma_comerciante_view, name='plataforma_comerciante'),
    path('publicar/', views.publicar_post_view, name='crear_publicacion'),

    path('beneficios/', views.beneficios_view, name='beneficios'),
    path('directorio/', views.directorio_view, name='directorio'),
    path('proveedor/<int:pk>/', views.proveedor_perfil_view, name='proveedor_perfil'),
    path('proveedor/dashboard/', views.proveedor_dashboard_view, name='proveedor_dashboard'),
    path('soporte/ticket/nuevo/', views.crear_ticket_soporte, name='crear_ticket_soporte'),
        # RUTAS PRINCIPALES
    path('noticias/', views.noticias_view, name='noticias'),
    path('redes-sociales/', views.redes_sociales_view, name='redes_sociales'), 
    # DIRECTORIO DE PROVEEDORES
    # 👇 ESTA ES LA RUTA QUE FALTABA

]
