from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings
from django.templatetags.static import static

# --- Opciones de Selección Múltiple ---

RELACION_NEGOCIO_CHOICES = [
    ('DUEÑO', 'Dueño/a'),
    ('ADMIN', 'Administrador/a'),
    ('EMPLEADO', 'Empleado/a clave'),
    ('FAMILIAR', 'Familiar a cargo'),
]

TIPO_NEGOCIO_CHOICES = [
    ('ALMACEN', 'Almacén de Barrio'),
    ('MINIMARKET', 'Minimarket'),
    ('BOTILLERIA', 'Botillería'),
    ('PANADERIA', 'Panadería/Pastelería'),
    ('FERIA', 'Feria Libre'),
    ('KIOSCO', 'Kiosco'),
    ('FOODTRUCK', 'Food Truck/Carro de Comida'),
]

# Opciones de Intereses
INTERESTS_CHOICES = [
    ('MARKETING', 'Marketing Digital'),
    ('INVENTARIO', 'Gestión de Inventario'),
    ('PROVEEDORES', 'Proveedores Locales'),
    ('FINANZAS', 'Finanzas y Contabilidad'),
    ('CLIENTES', 'Atención al Cliente'),
    ('LEYES', 'Normativa y Leyes'),
    ('TECNOLOGIA', 'Uso de Tecnología y Apps'),
    ('REDES_SOCIALES', 'Redes Sociales para Negocios'),
    ('VENTAS', 'Técnicas de Ventas'),
    ('CREDITOS', 'Créditos y Préstamos Pyme'),
    ('IMPUESTOS', 'Impuestos y Contabilidad Básica'),
    ('DECORACION', 'Decoración y Merchandising'),
    ('SOSTENIBILIDAD', 'Sostenibilidad y Reciclaje'),
    ('SEGURIDAD', 'Seguridad del Negocio'),
    ('LOGISTICA', 'Logística y Reparto'),
    ('INNOVACION', 'Innovación en Productos'),
    ('EMPRENDIMIENTO', 'Modelos de Emprendimiento'),
    ('SEGUROS', 'Seguros para Negocios'),
]

# ----------------Categorías para publicaciones del foro (INCLUYE TODAS)
CATEGORIA_POST_CHOICES = [
    ('DUDA', 'Duda / Pregunta'),
    ('OPINION', 'Opinión / Debate'),
    ('RECOMENDACION', 'Recomendación'),
    ('NOTICIA', 'Noticia del Sector'),
    ('GENERAL', 'General'),
    # NUEVAS CATEGORÍAS DE ADMINISTRADOR
    ('NOTICIAS_CA', 'Noticias Club Almacén'),
    ('DESPACHOS', 'Despachos realizados'),
    ('NUEVOS_SOCIOS', 'Nuevos socios'),
    ('ACTIVIDADES', 'Actividades en curso'),
]

# ----------------------------Categorías para beneficios
CATEGORIAS = [
    ('DESCUENTO', 'Descuento y Ofertas'),
    ('SORTEO', 'Sorteos y Rifas'),
    ('CAPACITACION', 'Capacitación y Cursos'),
    ('ACCESO', 'Acceso Exclusivo'),
    ('EVENTO', 'Eventos Especiales'),
]

ESTADO_BENEFICIO = [
    ('ACTIVO', 'Activo'),
    ('TERMINADO', 'Terminado'),
    ('BENEFICIO_ACTIVO', 'Beneficio Reclamado'),
]


RUBROS_CHOICES = [
    ('ABARROTES', 'Abarrotes'),
    ('CARNES', 'Carnes'),
    ('LACTEOS', 'Lácteos'),
    ('FRUTAS', 'Frutas y Verduras'),
    ('LIMPIEZA', 'Limpieza'),
    ('PANADERIA', 'Panadería'),
    ('VARIOS', 'Varios'),
]


class Comerciante(models.Model):
    ROLES_CHOICES = [
        ('COMERCIANTE', 'Comerciante'),
        ('ADMIN', 'Administrador'),
        ('PROVEEDOR', 'Proveedor'),
        ('TECNICO', 'Técnico de soporte'),
    ]

    # Autenticación y contacto
    nombre_apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)

    rol = models.CharField(
        max_length=20,
        choices=ROLES_CHOICES,
        default='COMERCIANTE',
        help_text="Define si este usuario es comerciante o administrador del sistema."
    )

    whatsapp_validator = RegexValidator(
        regex=r'^\+569\d{8}$',
        message="El formato debe ser '+569XXXXXXXX'."
    )
    whatsapp = models.CharField(
        validators=[whatsapp_validator],
        max_length=12,
        blank=True,
        null=True,
        help_text="Formato: +569XXXXXXXX"
    )

    # Negocio
    relacion_negocio = models.CharField(max_length=10, choices=RELACION_NEGOCIO_CHOICES)
    tipo_negocio = models.CharField(max_length=20, choices=TIPO_NEGOCIO_CHOICES)
    comuna = models.CharField(max_length=50)
    nombre_negocio = models.CharField(max_length=100, default='Mi Negocio Local', blank=True)

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_conexion = models.DateTimeField(default=timezone.now)

    # Perfil
    foto_perfil = models.ImageField(
        upload_to='perfiles/',
        default='usuarios/img/default_profile.png',
        blank=True,
        null=True
    )
    intereses = models.CharField(
        max_length=512,
        default='',
        blank=True,
        help_text="Códigos de intereses separados por coma."
    )

    # ELIMINADO: puntos y nivel
    
    es_proveedor = models.BooleanField(default=False, verbose_name='Es Proveedor')

    class Meta:
        verbose_name = 'Comerciante'
        verbose_name_plural = 'Comerciantes'

    def __str__(self):
        return f"{self.nombre_apellido} ({self.email})"

    def get_profile_picture_url(self):
        DEFAULT_IMAGE_PATH = 'usuarios/img/default_profile.png'
        if self.foto_perfil and self.foto_perfil.name and self.foto_perfil.name != DEFAULT_IMAGE_PATH:
            return self.foto_perfil.url
        return static('img/default_profile.png')


class Post(models.Model):
    comerciante = models.ForeignKey(
        Comerciante,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Comerciante'
    )
    titulo = models.CharField(max_length=200, verbose_name='Título de la Publicación')
    contenido = models.TextField(verbose_name='Contenido del Post')
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_POST_CHOICES,
        default='GENERAL',
        verbose_name='Categoría'
    )
    imagen_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='URL de Imagen/Link de Archivo Subido'
    )
    etiquetas = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Etiquetas (@usuarios, hashtags)'
    )
    fecha_publicacion = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Publicación'
    )

    class Meta:
        verbose_name = 'Publicación de Foro'
        verbose_name_plural = 'Publicaciones de Foro'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.titulo} por {self.comerciante.nombre_apellido}"


class Comentario(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Publicación'
    )
    comerciante = models.ForeignKey(
        Comerciante,
        on_delete=models.CASCADE,
        related_name='comentarios_dados',
        verbose_name='Autor'
    )
    contenido = models.TextField(verbose_name='Comentario')
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Comentario de {self.comerciante.nombre_apellido} en {self.post.titulo[:20]}"


# ELIMINADO: Modelo Like


class Beneficio(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título del Beneficio")
    descripcion = models.TextField(verbose_name="Descripción")
    foto = models.ImageField(
        upload_to='beneficios_fotos/',
        null=True,
        blank=True,
        verbose_name="Imagen"
    )
    vence = models.DateField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIAS,
        default='DESCUENTO',
        verbose_name="Categoría"
    )
    # ELIMINADO: puntos_requeridos
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_BENEFICIO,
        default='ACTIVO'
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Subido por'
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Beneficio y Promoción'
        verbose_name_plural = 'Beneficios y Promociones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.titulo}"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500, blank=True)
    foto_perfil = models.ImageField(upload_to='proveedores/fotos/', null=True, blank=True)
    email_contacto = models.EmailField(blank=True, null=True)
    whatsapp_contacto = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        help_text="Formato: +569XXXXXXXX"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_conexion = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre

    def get_profile_picture_url(self):
        DEFAULT_IMAGE_PATH = 'usuarios/img/default_profile.png'
        if self.foto_perfil and self.foto_perfil.name and self.foto_perfil.name != DEFAULT_IMAGE_PATH:
            return self.foto_perfil.url
        return static('img/default_profile.png')


class Propuesta(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='propuestas'
    )
    titulo = models.CharField(max_length=100)
    rubros_ofertados = models.CharField(
        max_length=255,
        verbose_name='Rubros Ofertados',
        help_text='Separados por coma'
    )
    zona_geografica = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Propuesta de Proveedor"
        verbose_name_plural = "Propuestas de Proveedores"

    def __str__(self):
        return f"{self.titulo} - {self.proveedor.nombre}"