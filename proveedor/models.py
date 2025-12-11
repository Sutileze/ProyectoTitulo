from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.templatetags.static import static


# ==================== CHOICES GEOGRÁFICAS SIMPLIFICADAS ====================

PAISES_CHOICES = [
    ('', 'Selecciona un país'),
    ('CL', 'Chile'),
]

REGIONES_CHOICES = [
    ('', 'Selecciona una región'),
    ('CL-RM', 'Región Metropolitana'),
    ('CL-VS', 'Valparaíso'),
    ('CL-BI', 'Biobío'),
]

COMUNAS_CHOICES = [
    ('', 'Selecciona una comuna'),
    # Región Metropolitana
    ('RM-Santiago', 'Santiago'),
    ('RM-Maipu', 'Maipú'),
    ('RM-Puente-Alto', 'Puente Alto'),
    
    # Valparaíso
    ('VS-Valparaiso', 'Valparaíso'),
    ('VS-Vina-del-Mar', 'Viña del Mar'),
    ('VS-Quilpue', 'Quilpué'),
    
    # Biobío
    ('BI-Concepcion', 'Concepción'),
    ('BI-Talcahuano', 'Talcahuano'),
    ('BI-Los-Angeles', 'Los Ángeles'),
]

# Mapeo de regiones por país
REGIONES_POR_PAIS = {
    'CL': [
        ('CL-RM', 'Región Metropolitana'),
        ('CL-VS', 'Valparaíso'),
        ('CL-BI', 'Biobío'),
    ],
}

# Mapeo de comunas por región
COMUNAS_POR_REGION = {
    'CL-RM': [
        ('RM-Santiago', 'Santiago'),
        ('RM-Maipu', 'Maipú'),
        ('RM-Puente-Alto', 'Puente Alto'),
    ],
    'CL-VS': [
        ('VS-Valparaiso', 'Valparaíso'),
        ('VS-Vina-del-Mar', 'Viña del Mar'),
        ('VS-Quilpue', 'Quilpué'),
    ],
    'CL-BI': [
        ('BI-Concepcion', 'Concepción'),
        ('BI-Talcahuano', 'Talcahuano'),
        ('BI-Los-Angeles', 'Los Ángeles'),
    ],
}

# ==================== MODELOS ====================

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
    # ✅ AUTENTICACIÓN PROPIA
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    password_hash = models.CharField(max_length=128, verbose_name='Contraseña')
    nombre_contacto = models.CharField(max_length=200, verbose_name='Nombre de contacto')
    
    # Información básica
    nombre_empresa = models.CharField(max_length=200, verbose_name='Nombre de la Empresa')
    descripcion = models.TextField(verbose_name='Descripción del negocio')
    
    # Foto/Logo
    foto = models.ImageField(upload_to='proveedores/', blank=True, null=True, verbose_name='Logo/Foto')
    
    # Categorías (un proveedor puede ofrecer múltiples rubros)
    categorias = models.ManyToManyField(CategoriaProveedor, related_name='proveedores', blank=True, verbose_name='Rubros que oferta')
    
    # Ubicación geográfica (ahora como CHOICES)
    pais = models.CharField(max_length=2, choices=PAISES_CHOICES, blank=True, null=True, verbose_name='País')
    region = models.CharField(max_length=10, blank=True, null=True, verbose_name='Región')
    comuna = models.CharField(max_length=50, blank=True, null=True, verbose_name='Comuna')
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dirección')

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
    ultima_conexion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return self.nombre_empresa
    
    def get_profile_picture_url(self):
        if self.foto_perfil and self.foto_perfil.name:
            return self.foto_perfil.url
        return static('img/default_profile.png')
    
    def get_pais_display_name(self):
        """Retorna el nombre completo del país"""
        for codigo, nombre in PAISES_CHOICES:
            if codigo == self.pais:
                return nombre
        return self.pais
    
    def get_region_display_name(self):
        """Retorna el nombre completo de la región"""
        for codigo, nombre in REGIONES_CHOICES:
            if codigo == self.region:
                return nombre
        return self.region
    
    def get_comuna_display_name(self):
        """Retorna el nombre completo de la comuna"""
        for codigo, nombre in COMUNAS_CHOICES:
            if codigo == self.comuna:
                return nombre
        return self.comuna
    
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
    """
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
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
        self.fecha_respuesta = timezone.now()
        self.save()
        
        self.proveedor.contactos_aceptados += 1
        self.proveedor.save(update_fields=['contactos_aceptados'])
    
    def rechazar(self):
        self.estado = 'rechazada'
        self.fecha_respuesta = timezone.now()
        self.save()


class ProductoServicio(models.Model):
    """Productos o servicios que ofrece el proveedor"""
    
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
    """Promociones que publican los proveedores"""
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
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin and self.activo