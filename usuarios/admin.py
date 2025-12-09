from django.contrib import admin
from .models import (
    Comerciante,
    Post,
    Comentario,
    Beneficio,
    Proveedor,
    Propuesta,
    Aviso,  # NUEVO
    AvisoLeido,
)


@admin.register(Comerciante)
class ComercianteAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_apellido',
        'email',
        'rol',
        'comuna',
        'nombre_negocio',
        'es_proveedor',
        'fecha_registro',
        'ultima_conexion',
    )
    list_filter = (
        'rol',
        'comuna',
        'es_proveedor',
        'relacion_negocio',
        'tipo_negocio',
    )
    search_fields = ('nombre_apellido', 'email', 'nombre_negocio', 'comuna')
    readonly_fields = ('fecha_registro', 'ultima_conexion')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'comerciante', 'categoria', 'fecha_publicacion')
    list_filter = ('categoria', 'fecha_publicacion')
    search_fields = ('titulo', 'contenido', 'comerciante__nombre_apellido')


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('post', 'comerciante', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('contenido', 'comerciante__nombre_apellido', 'post__titulo')




@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'categoria',
        'estado',
        'vence',
        'fecha_creacion',
    )
    list_filter = ('categoria', 'estado')
    search_fields = ('titulo', 'descripcion')


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email_contacto', 'whatsapp_contacto', 'ultima_conexion')
    search_fields = ('nombre', 'email_contacto')


@admin.register(Propuesta)
class PropuestaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'proveedor', 'zona_geografica')
    list_filter = ('zona_geografica',)
    search_fields = ('titulo', 'proveedor__nombre', 'rubros_ofertados')

class AvisoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_caducidad', 'fecha_creacion', 'is_vigente')
    list_filter = ('tipo', 'fecha_caducidad')
    search_fields = ('titulo', 'contenido')
    readonly_fields = ('fecha_creacion',)
    
    def is_vigente(self, obj):
        return obj.is_vigente()
    is_vigente.boolean = True
    is_vigente.short_description = 'Vigente'

@admin.register(AvisoLeido)
class AvisoLeidoAdmin(admin.ModelAdmin):
    list_display = ('aviso', 'comerciante', 'fecha_lectura')
    search_fields = ('aviso__titulo', 'comerciante__nombre_apellido')
    list_filter = ('aviso__tipo',)