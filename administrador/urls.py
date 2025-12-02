from django.urls import path
from . import views

urlpatterns = [
    # ======== COMERCIANTES ========
    path('', views.panel_admin_view, name='panel_admin'),
    path('comerciante/crear/', views.crear_comerciante_view, name='crear_comerciante'),
    path('comerciante/editar/<int:comerciante_id>/', views.editar_comerciante_view, name='editar_comerciante'),
    path('comerciante/eliminar/<int:comerciante_id>/', views.eliminar_comerciante_view, name='eliminar_comerciante'),

    # ======== BENEFICIOS ========
    path('beneficios/', views.admin_beneficios_list, name='admin_beneficios'),
    path('beneficios/crear/', views.crear_beneficio_view, name='crear_beneficio'),
    path('beneficios/editar/<int:beneficio_id>/', views.editar_beneficio_view, name='editar_beneficio'),
    path('beneficios/eliminar/<int:beneficio_id>/', views.eliminar_beneficio_view, name='eliminar_beneficio'),

    # ======== POSTS ========
    path('posts/', views.admin_posts_list, name='admin_posts'),
    path('posts/crear/', views.crear_post_admin_view, name='crear_post_admin'),
    path('posts/editar/<int:post_id>/', views.editar_post_admin_view, name='editar_post_admin'),
    path('posts/eliminar/<int:post_id>/', views.eliminar_post_admin_view, name='eliminar_post_admin'),
]
