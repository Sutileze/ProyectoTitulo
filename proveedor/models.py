
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from usuarios.models import Comerciante

class Pais(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=3, unique=True)
    
    class Meta:
        db_table = 'pais'
        verbose_name = 'País'
        verbose_name_plural = 'Países'
    
    def __str__(self):
        return self.nombre


class Region(models.Model):
    nombre = models.CharField(max_length=100)
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='regiones')
    
    class Meta:
        db_table = 'region'
        verbose_name = 'Región'
        verbose_name_plural = 'Regiones'
    
    def __str__(self):
        return self.nombre


class Comuna(models.Model):
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='comunas')
    
    class Meta:
        db_table = 'comuna'
        verbose_name = 'Comuna'
        verbose_name_plural = 'Comunas'
    
    def __str__(self):
        return self.nombre


class CategoriaProveedor(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    icono = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categoria_proveedor'
        verbose_name = 'Categoría de Proveedor'
        verbose_name_plural = 'Categorías de Proveedores'
    
    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    # Relación con usuario
    usuario = models.OneToOneField(Comerciante, on_delete=models.CASCADE, related_name='proveedor')
    
    # Información básica
    nombre_empresa = models.CharField(max_length=200, verbose_name='Nombre de la Empresa')
    descripcion = models.TextField(verbose_name='Descripción del negocio')
    
    # Foto/Logo
    foto = models.ImageField(upload_to='proveedores/', blank=True, null=True, verbose_name='Logo/Foto')
    
    # Categorías (un proveedor puede ofrecer múltiples rubros)
    categorias = models.ManyToManyField(CategoriaProveedor, related_name='proveedores', verbose_name='Rubros que oferta')
    
    # Ubicación geográfica
    pais = models.ForeignKey(Pais, on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True, blank=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    foto_perfil = models.ImageField(upload_to='proveedores/fotos/', blank=True, null=True)
    modo_oscuro = models.BooleanField(default=False)
    notif_email = models.BooleanField(default=True)
    notif_mensajes = models.BooleanField(default=True)
    notif_pedidos = models.BooleanField(default=True)
    idioma = models.CharField(max_length=5, default='es')
    zona_horaria = models.CharField(max_length=50, default='America/Santiago')
    perfil_publico = models.BooleanField(default=True)
    mostrar_estadisticas = models.BooleanField(default=True)
    
    # Zona geográfica de cobertura
    COBERTURA_CHOICES = [
        ('local', 'Local'),
        ('comunal', 'Comunal'),
        ('regional', 'Regional'),
        ('nacional', 'Nacional'),
        ('internacional', 'Internacional'),
    ]
    cobertura = models.CharField(max_length=20, choices=COBERTURA_CHOICES, default='local', verbose_name='Zona geográfica')
    
    # Datos de contacto
    telefono_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos."
    )
    telefono = models.CharField(validators=[telefono_regex], max_length=17, blank=True, null=True)
    whatsapp = models.CharField(validators=[telefono_regex], max_length=17, verbose_name='WhatsApp')
    email = models.EmailField(verbose_name='Correo electrónico')
    sitio_web = models.URLField(blank=True, null=True, verbose_name='Sitio web')
    
    # Redes sociales
    facebook = models.URLField(blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    
    # Estado y validación
    activo = models.BooleanField(default=True)
    verificado = models.BooleanField(default=False, verbose_name='Proveedor verificado')
    destacado = models.BooleanField(default=False, verbose_name='Proveedor destacado')
    
    # Estadísticas
    visitas = models.IntegerField(default=0)
    contactos_enviados = models.IntegerField(default=0, verbose_name='Solicitudes de contacto enviadas')
    contactos_aceptados = models.IntegerField(default=0, verbose_name='Contactos aceptados')
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return self.nombre_empresa
    
    def incrementar_visitas(self):
        self.visitas += 1
        self.save(update_fields=['visitas'])
    
    def tasa_aceptacion(self):
        """Calcula el porcentaje de contactos aceptados"""
        if self.contactos_enviados > 0:
            return (self.contactos_aceptados / self.contactos_enviados) * 100
        return 0


class SolicitudContacto(models.Model):
    """
    Modelo para gestionar las solicitudes de contacto de proveedores a comercios
    Según el documento: Los proveedores pueden enviar mensajes o solicitudes de contacto
    """
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    # Aquí deberías tener un modelo Comercio similar
    # comercio = models.ForeignKey('Comercio', on_delete=models.CASCADE, related_name='solicitudes_recibidas')
    
    mensaje = models.TextField(verbose_name='Mensaje de presentación')
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'solicitud_contacto'
        verbose_name = 'Solicitud de Contacto'
        verbose_name_plural = 'Solicitudes de Contacto'
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.proveedor.nombre_empresa} - {self.estado}"
    
    def aceptar(self):
        self.estado = 'aceptada'
        from django.utils import timezone
        self.fecha_respuesta = timezone.now()
        self.save()
        
        # Actualizar contador del proveedor
        self.proveedor.contactos_aceptados += 1
        self.proveedor.save(update_fields=['contactos_aceptados'])
    
    def rechazar(self):
        self.estado = 'rechazada'
        from django.utils import timezone
        self.fecha_respuesta = timezone.now()
        self.save()

class ProductoServicio(models.Model):
    """
    Productos o servicios que ofrece el proveedor
    """
    
    # Define las opciones de categoría
    # Esto es mejor que crear una tabla de Categorías separada si las opciones son fijas y limitadas.
    CATEGORIA_CHOICES = (
        ('ALIMENTOS', 'Alimentos y Comida'),
        ('BEBIDAS', 'Bebidas y Licores'),
        ('ROPA', 'Ropa y Accesorios'),
        ('HOGAR', 'Artículos para el Hogar'),
        ('SERVICIOS', 'Servicios Profesionales'),
        ('OTRO', 'Otro / Varios'),
    )
    
    proveedor = models.ForeignKey('Proveedor', on_delete=models.CASCADE, related_name='productos_servicios')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio_referencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    
    # ✅ NUEVO CAMPO 'categoria' - Usa Choices
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES,
        default='OTRO',
        verbose_name='Categoría del Producto/Servicio'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'producto_servicio'
        verbose_name = 'Producto/Servicio'
        verbose_name_plural = 'Productos/Servicios'
    
    def __str__(self):
        return f"{self.nombre} - {self.proveedor.nombre_empresa}"


class Promocion(models.Model):
    """
    Promociones que publican los proveedores
    """
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='promociones')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='promociones/', blank=True, null=True)
    
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    activo = models.BooleanField(default=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'promocion'
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return self.titulo
    
    def esta_vigente(self):
        from django.utils import timezone
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin and self.activo