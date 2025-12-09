from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import feedparser 
from django.utils.html import strip_tags 
from proveedor.models import Region, Comuna 

from .models import (
    Comerciante,
    Post,
    Comentario,
    INTERESTS_CHOICES,
    Proveedor,
    Propuesta,
    RUBROS_CHOICES,
    Beneficio,
    CATEGORIAS,
    CATEGORIA_POST_CHOICES,
    Aviso,  # NUEVO IMPORT
    AvisoLeido, # NUEVO IMPORT
)
from .forms import (
    RegistroComercianteForm,
    LoginForm,
    PostForm,
    ProfilePhotoForm,
    BusinessDataForm,
    ContactInfoForm,
    InterestsForm,
    ComentarioForm,
)

current_logged_in_user = None # Control de sesión global

ROLES = {
    'COMERCIANTE': 'Comerciante Verificado',
    'PROVEEDOR': 'Proveedor',
    'ADMIN': 'Administrador',
    'INVITADO': 'Invitado',
}

COMMUNITY_CATEGORIES = [# --- DEFINICIÓN DE CATEGORÍAS SEPARADAS (para filtros de foro) ---
    ('DUDA', 'Duda / Pregunta'),
    ('OPINION', 'Opinión / Debate'),
    ('RECOMENDACION', 'Recomendación'),
    ('NOTICIA', 'Noticia del Sector'),
    ('GENERAL', 'General'),
]

ADMIN_CATEGORIES = [
    ('NOTICIAS_CA', 'Noticias Club Almacén'),
    ('DESPACHOS', 'Despachos realizados'),
    ('NUEVOS_SOCIOS', 'Nuevos socios'),
    ('ACTIVIDADES', 'Actividades en curso'),
]
# --- Funciones helper ---
def is_online(last_login):
    """Verifica si el usuario estuvo activo en los últimos 5 minutos."""
    if not last_login:
        return False
    return (timezone.now() - last_login) < timedelta(minutes=5)

# --- Autenticación y cuenta ---
def index(request):
    return redirect('registro')

def registro_view(request):
    if request.method == 'POST':
        form = RegistroComercianteForm(request.POST)
        if form.is_valid():
            raw_password = form.cleaned_data.pop('password')
            hashed_password = make_password(raw_password)

            nuevo_comerciante = form.save(commit=False)
            nuevo_comerciante.password_hash = hashed_password

            comuna_final = form.cleaned_data.get('comuna')
            if comuna_final:
                nuevo_comerciante.comuna = comuna_final

            try:
                nuevo_comerciante.save()
                messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión.')
                return redirect('login')
            except IntegrityError:
                messages.error(
                    request,
                    'Este correo electrónico ya está registrado. '
                    'Por favor, inicia sesión o usa otro correo.'
                )
            except Exception as e:
                messages.error(request, f'Ocurrió un error inesperado al guardar: {e}')
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = RegistroComercianteForm()

    return render(request, 'usuarios/cuenta.html', {'form': form})

def login_view(request):
    """Maneja el inicio de sesión y la redirección según el rol del usuario."""
    global current_logged_in_user
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                comerciante = Comerciante.objects.get(email=email)

                if check_password(password, comerciante.password_hash):
                    
                    comerciante.ultima_conexion = timezone.now()
                    comerciante.save(update_fields=['ultima_conexion']) 
                    
                    current_logged_in_user = comerciante
                    
                    messages.success(request, f'¡Bienvenido {comerciante.nombre_apellido}!')

                    if comerciante.rol == 'ADMIN':
                        return redirect('panel_admin')

                    if comerciante.rol == 'TECNICO':
                        return redirect('soporte:panel_soporte')

                    if getattr(comerciante, 'es_proveedor', False):
                        return redirect('proveedor_dashboard')

                    return redirect('plataforma_comerciante')

                else:
                    messages.error(request, 'Contraseña incorrecta. Intenta nuevamente.')

            except Comerciante.DoesNotExist:
                messages.error(request, 'Este correo no está registrado. Por favor, regístrate primero.')
        else:
            messages.error(request, 'Por favor, completa todos los campos correctamente.')
    else:
        form = LoginForm()
        current_logged_in_user = None 

    contexto = {'form': form}
    return render(request, 'usuarios/cuenta.html', contexto)

def logout_view(request):
    """Cierra la sesión del usuario actual."""
    global current_logged_in_user
    if current_logged_in_user:
        messages.info(
            request,
            f'Adiós, {current_logged_in_user.nombre_apellido}. Has cerrado sesión.'
        )
        current_logged_in_user = None
    return redirect('login')

# --- Perfil ---
def perfil_view(request):
    """Muestra y maneja la edición del perfil del comerciante."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Por favor, inicia sesión para acceder a tu perfil.')
        return redirect('login')

    comerciante = current_logged_in_user
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit_photo':
            photo_form = ProfilePhotoForm(
                request.POST,
                request.FILES,
                instance=comerciante
            )
            if photo_form.is_valid():
                photo_form.save()
                messages.success(request, '¡Foto de perfil actualizada con éxito!')
                return redirect('perfil')
            else:
                messages.error(
                    request,
                    'Error al subir la foto. Asegúrate de que sea un archivo válido.'
                )

        elif action == 'edit_contact':
            contact_form = ContactInfoForm(request.POST, instance=comerciante)
            if contact_form.is_valid():
                nuevo_email = contact_form.cleaned_data.get('email')

                if (
                    nuevo_email != comerciante.email and
                    Comerciante.objects.filter(email=nuevo_email).exists()
                ):
                    messages.error(request, 'Este correo ya está registrado por otro usuario.')
                else:
                    contact_form.save()
                    messages.success(request, 'Datos de contacto actualizados con éxito.')
                    current_logged_in_user.email = nuevo_email
                    current_logged_in_user.whatsapp = contact_form.cleaned_data.get('whatsapp')
                    return redirect('perfil')
            else:
                error_msgs = [
                    f"{field.label}: {', '.join(error for error in field.errors)}"
                    for field in contact_form if field.errors
                ]
                messages.error(
                    request,
                    f'Error en los datos de contacto. {"; ".join(error_msgs)}'
                )

        elif action == 'edit_business':
            business_form = BusinessDataForm(request.POST, instance=comerciante)
            if business_form.is_valid():
                business_form.save()
                messages.success(request, 'Datos del negocio actualizados con éxito.')
                current_logged_in_user.nombre_negocio = business_form.cleaned_data.get(
                    'nombre_negocio'
                )
                return redirect('perfil')
            else:
                error_msgs = [
                    f"{field.label}: {', '.join(error for error in field.errors)}"
                    for field in business_form if field.errors
                ]
                messages.error(
                    request,
                    f'Error en los datos del negocio. {"; ".join(error_msgs)}'
                )

        elif action == 'edit_interests':
            interests_form = InterestsForm(request.POST)
            if interests_form.is_valid():
                intereses_seleccionados = interests_form.cleaned_data['intereses']
                intereses_csv = ','.join(intereses_seleccionados)

                comerciante.intereses = intereses_csv
                comerciante.save(update_fields=['intereses'])

                messages.success(request, 'Intereses actualizados con éxito.')
                return redirect('perfil')
            else:
                messages.error(request, 'Error al actualizar los intereses.')

    photo_form = ProfilePhotoForm()
    contact_form = ContactInfoForm(instance=comerciante)
    business_form = BusinessDataForm(instance=comerciante)

    intereses_actuales_codigos = (
        comerciante.intereses.split(',') if comerciante.intereses else []
    )
    interests_form = InterestsForm(
        initial={'intereses': [c for c in intereses_actuales_codigos if c]}
    )

    intereses_choices_dict = dict(INTERESTS_CHOICES)

    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get(comerciante.rol, 'Usuario'),
        'nombre_negocio_display': comerciante.nombre_negocio,
        'es_proveedor': comerciante.es_proveedor,

        'photo_form': photo_form,
        'contact_form': contact_form,
        'business_form': business_form,
        'interests_form': interests_form,

        'intereses_actuales_codigos': [c for c in intereses_actuales_codigos if c],
        'intereses_choices_dict': intereses_choices_dict,
    }

    return render(request, 'usuarios/perfil.html', context)

# --- Plataforma / Foro ---
def plataforma_comerciante_view(request):
    """Muestra el feed principal del foro, aplicando filtros de comunidad/admin y categoría."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(
            request,
            'Por favor, inicia sesión para acceder a la plataforma.'
        )
        return redirect('login')

    posts_query = (
        Post.objects
        .select_related('comerciante')
        .annotate(
            comentarios_count=Count('comentarios', distinct=True),
        )
        .prefetch_related(
            'comentarios',
            'comentarios__comerciante'
        )
    )

    # Lógica de filtrado por rol (Comunidad vs. Admin)
    tipo_filtro = request.GET.get('tipo_filtro', 'COMUNIDAD')
    posting_allowed = tipo_filtro != 'ADMIN'

    # 1. Definir opciones de categorías válidas según el filtro principal
    if tipo_filtro == 'ADMIN':
        posts_query = posts_query.filter(comerciante__rol='ADMIN')
        category_options_for_display = ADMIN_CATEGORIES
        valid_post_keys = [key for key, value in ADMIN_CATEGORIES]
        
    else: # 'COMUNIDAD' (Filtrando la categoría 'NOTICIA del Sector' según tu solicitud)
        # Filtra COMMUNITY_CATEGORIES para mostrar solo: dudas, opinion, recomendacion, general
        community_options_filtered = [
            (k, v) for k, v in COMMUNITY_CATEGORIES 
            if k in ['DUDA', 'OPINION', 'RECOMENDACION', 'GENERAL'] # Excluye NOTICIA
        ]
        
        valid_post_keys = [key for key, value in community_options_filtered]
        posts_query = posts_query.filter(categoria__in=valid_post_keys)
        category_options_for_display = community_options_filtered

    # 2. Aplicar filtro de subcategoría (Temas del Foro)
    categoria_filtros = request.GET.getlist('categoria', [])
    
    if categoria_filtros and 'TODAS' not in categoria_filtros and 'TODOS' not in categoria_filtros:
        # Si se seleccionan categorías específicas
        posts = posts_query.filter(
            categoria__in=categoria_filtros
        ).order_by('-fecha_publicacion')
    else:
        # Si no hay filtro, muestra todos los posts de las categorías válidas
        posts = posts_query.filter(categoria__in=valid_post_keys).order_by('-fecha_publicacion')
        if not categoria_filtros or ('TODAS' in categoria_filtros or 'TODOS' in categoria_filtros):
            categoria_filtros = ['TODOS']
    # 3. Restricción de publicación (revisión de seguridad de front-end)
    # 3. Restricción de publicación (revisión de seguridad de front-end)
    user_can_post = True
    if current_logged_in_user and current_logged_in_user.rol != 'ADMIN' and tipo_filtro == 'ADMIN':
        user_can_post = False
        
    post_form_with_choices = PostForm(category_choices=category_options_for_display)
    # --- Lógica de Avisos y Notificación ---
    hoy = timezone.now().date()
    
    # A. Obtener el número de notificaciones no leídas para el icono de la campana
    if current_logged_in_user:
        avisos_no_leidos_count = Aviso.objects.filter(
            Q(fecha_caducidad__isnull=True) | Q(fecha_caducidad__gte=hoy)
        ).exclude(
            lecturas__comerciante=current_logged_in_user
        ).count()
    else:
        avisos_no_leidos_count = 0
        
    # B. Obtener los 5 avisos más recientes y vigentes para la sección de Avisos
    top_avisos = Aviso.objects.filter(
        Q(fecha_caducidad__isnull=True) | Q(fecha_caducidad__gte=hoy)
    ).order_by('-fecha_creacion')[:5]
        
    # Carga de recursos externos
    try:
        regiones = Region.objects.all().order_by('nombre')
    except Exception:
        regiones = []

    top_posters = Comerciante.objects.annotate(
        post_count=Count('posts')
    ).exclude(rol='ADMIN').order_by('-post_count')[:5]

    news_preview = fetch_news_preview() 
    context = {
        'comerciante': current_logged_in_user,
        'rol_usuario': ROLES.get(current_logged_in_user.rol, 'Usuario'),
        'post_form': post_form_with_choices, # Pasamos el formulario con las opciones filtradas
        'posts': posts,
        'CATEGORIA_POST_CHOICES': category_options_for_display, # Pasamos lista filtrada para sidebar
        'COMMUNITY_CATEGORIES': COMMUNITY_CATEGORIES,
        'ADMIN_CATEGORIES': ADMIN_CATEGORIES,
        'categoria_seleccionada': categoria_filtros,
        'comentario_form': ComentarioForm(),
        'message': (
            f'Bienvenido a la plataforma, '
            f'{current_logged_in_user.nombre_apellido.split()[0]}.'
        ),
        'tipo_filtro': tipo_filtro,
        'regiones': regiones,
        'user_can_post': user_can_post,
        'top_posters': top_posters,
        'posting_allowed': posting_allowed,
        'top_avisos': top_avisos, # NUEVO: TOP 5 AVISOS VIGENTES
        'avisos_no_leidos_count': avisos_no_leidos_count, # NUEVO: Contador de campana
    }

    return render(request, 'usuarios/plataforma_comerciante.html', context)


# --- NUEVA VISTA DE NOTIFICACIONES ---
def notificaciones_view(request):
    """Muestra la lista de avisos del admin al comerciante, marcando los no leídos."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Debes iniciar sesión para ver tus notificaciones.')
        return redirect('login')

    comerciante = current_logged_in_user
    hoy = timezone.now().date()
    
    # 1. Obtener todos los avisos vigentes
    avisos_vigentes_qs = Aviso.objects.filter(
        Q(fecha_caducidad__isnull=True) | Q(fecha_caducidad__gte=hoy)
    ).order_by('-fecha_creacion')

    # 2. Anotar el estado de lectura para el usuario actual
    notifications = avisos_vigentes_qs.annotate(
        leido=Count('lecturas', filter=Q(lecturas__comerciante=comerciante))
    ).order_by('leido', '-fecha_creacion') # No leídos primero (leido=0)

    # 3. Marcar como leído si se accede a la lista (buena práctica UX)
    #    Marcamos todos los avisos VIGENTES como leídos al cargar la lista.
    for notification in notifications.filter(leido=0):
        AvisoLeido.objects.get_or_create(aviso=notification, comerciante=comerciante)
        
    context = {
        'comerciante': comerciante,
        'notifications': notifications,
    }
    
    return render(request, 'usuarios/notificaciones.html', context)


def marcar_aviso_leido(request, aviso_id):
    """Marca un aviso específico como leído para el usuario actual (usado en post/detalle)."""
    if not current_logged_in_user:
        return redirect('login')

    aviso = get_object_or_404(Aviso, id=aviso_id)
    AvisoLeido.objects.get_or_create(aviso=aviso, comerciante=current_logged_in_user)
    
    messages.success(request, f"Aviso '{aviso.titulo}' marcado como leído.")
    return redirect('notificaciones')

def publicar_post_view(request):
    """Procesa el formulario de creación de un nuevo post."""
    global current_logged_in_user

    if request.method == 'POST':
        if not current_logged_in_user:
            messages.error(request, 'Debes iniciar sesión para publicar.')
            return redirect('login')
        
        # VALIDACIÓN: Prohíbe a no-admins publicar en categorías de Admin
        is_admin_category = False
        for key, _ in ADMIN_CATEGORIES:
            if key == request.POST.get('categoria'):
                is_admin_category = True
                break
                
        if is_admin_category and current_logged_in_user.rol != 'ADMIN':
            messages.error(
                request, 
                'No tienes permiso para publicar en la categoría seleccionada.'
            )
            return redirect('plataforma_comerciante')


        try:
            form = PostForm(request.POST, request.FILES)

            if form.is_valid():
                nuevo_post = form.save(commit=False)
                nuevo_post.comerciante = current_logged_in_user

                uploaded_file = form.cleaned_data.get('uploaded_file')

                if uploaded_file:
                    file_name = default_storage.save(
                        f'posts/{uploaded_file.name}',
                        uploaded_file
                    )
                    nuevo_post.imagen_url = default_storage.url(file_name)

                nuevo_post.save()
                messages.success(
                    request,
                    '¡Publicación creada con éxito! Se ha añadido al foro.'
                )
                return redirect('plataforma_comerciante')
            else:
                messages.error(
                    request,
                    f'Error al publicar. Corrige: {form.errors.as_text()}'
                )
                return redirect('plataforma_comerciante')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al publicar: {e}')

    return redirect('plataforma_comerciante')

def post_detail_view(request, post_id):
    """Muestra el detalle de una publicación y sus comentarios."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Debes iniciar sesión para ver los detalles.')
        return redirect('login')

    post = get_object_or_404(
        Post.objects
        .select_related('comerciante')
        .annotate(
            comentarios_count=Count('comentarios', distinct=True),
        ),
        pk=post_id
    )

    comentarios = post.comentarios.select_related(
        'comerciante'
    ).all().order_by('-fecha_creacion') # Comentarios de más nuevo a más antiguo

    context = {
        'comerciante': current_logged_in_user,
        'post': post,
        'comentarios': comentarios,
        'comentario_form': ComentarioForm(),
    }
    return render(request, 'usuarios/post_detail.html', context)

def add_comment_view(request, post_id):
    """Procesa el formulario para añadir un nuevo comentario y redirige al detalle del post."""
    
    # Se asegura que el usuario esté logueado
    if not current_logged_in_user:
        messages.error(request, 'No autorizado para comentar. Inicia sesión.')
        return redirect('login')

    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.post = post
            nuevo_comentario.comerciante = current_logged_in_user
            nuevo_comentario.save()
            messages.success(request, '¡Comentario publicado con éxito!')
        else:
            messages.error(
                request,
                'Error al publicar el comentario. El contenido no puede estar vacío.'
            )

    # Redirige al detalle del post después de intentar publicar (éxito o error)
    return redirect('post_detail', post_id=post.id)

def beneficios_view(request):
    """Muestra la lista de beneficios disponibles, con opciones de filtro."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(
            request,
            'Por favor, inicia sesión para acceder a los beneficios.'
        )
        return redirect('login')

    comerciante = current_logged_in_user

    # La lista de categorías para el filtro
    CATEGORIAS_CHOICES = CATEGORIAS 
    
    category_filter = request.GET.get('category', 'TODOS')
    sort_by = request.GET.get('sort_by', '-fecha_creacion')

    beneficios_queryset = Beneficio.objects.all()

    if category_filter and category_filter != 'TODOS':
        beneficios_queryset = beneficios_queryset.filter(categoria=category_filter)

    # Valida y aplica el ordenamiento
    valid_sort_fields = [
        'vence',
        '-vence',
        '-fecha_creacion',
    ]
    if sort_by in valid_sort_fields:
        beneficios_queryset = beneficios_queryset.order_by(sort_by)
    else:
        sort_by = '-fecha_creacion'
        beneficios_queryset = beneficios_queryset.order_by(sort_by)

    no_beneficios_disponibles = not beneficios_queryset.exists()

    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get(comerciante.rol, 'Usuario'),
        'beneficios': beneficios_queryset,
        'no_beneficios_disponibles': no_beneficios_disponibles,
        'CATEGORIAS': CATEGORIAS_CHOICES, 
        'current_category': category_filter,
        'current_sort': sort_by,
    }

    return render(request, 'usuarios/beneficios.html', context)

def proveedor_dashboard_view(request):
    """Muestra el panel de control del proveedor (si el usuario es proveedor)."""
    global current_logged_in_user

    if not current_logged_in_user or not getattr(current_logged_in_user, 'es_proveedor', False):
        messages.warning(request, 'Acceso denegado. Esta interfaz es solo para Proveedores activos.')
        return redirect('perfil')
    
    from proveedor.models import Proveedor 

    try:
        proveedor_qs = Proveedor.objects.get(usuario=current_logged_in_user)
    except Proveedor.DoesNotExist:
        proveedor_qs = None

    context = {
        'comerciante': current_logged_in_user,
        'proveedor': proveedor_qs,
    }

    return render(request, 'proveedores/perfil.html', context)

def directorio_view(request):
    """Muestra el directorio de proveedores con opciones de búsqueda y filtro."""
    
    rubro_filter = request.GET.get('rubro', 'TODOS')
    region_filter_id = request.GET.get('region') 

    propuestas_queryset = Propuesta.objects.select_related('proveedor').all()

    if rubro_filter and rubro_filter != 'TODOS':
        propuestas_queryset = propuestas_queryset.filter(
            rubros_ofertados__icontains=rubro_filter
        )
    
    if region_filter_id and region_filter_id != '':
        try:
            propuestas_queryset = propuestas_queryset.filter(
                proveedor__region__id=region_filter_id
            )
        except Exception:
            pass

    sort_by = request.GET.get('ordenar_por', 'proveedor__nombre') 
    valid_sort_fields = ['proveedor__nombre', '-proveedor__nombre']
    
    if sort_by in valid_sort_fields:
        propuestas_queryset = propuestas_queryset.order_by(sort_by)
    else:
        sort_by = 'proveedor__nombre'
        propuestas_queryset = propuestas_queryset.order_by(sort_by)

    try:
        regiones = Region.objects.all().order_by('nombre')
    except Exception:
        regiones = []

    context = {
        'propuestas': propuestas_queryset,
        'RUBROS_CHOICES': RUBROS_CHOICES,
        'ZONAS': [
            'Santiago Centro',
            'Providencia',
            'Ñuñoa',
            'Las Condes',
            'Maipú',
            'La Reina',
        ],
        'current_rubro': rubro_filter,
        'current_zona': region_filter_id, 
        'current_sort': sort_by,
        'comerciante': current_logged_in_user,
        'regiones': regiones,
        'region_seleccionada': region_filter_id,
    }

    return render(request, 'usuarios/directorio.html', context)

def proveedor_perfil_view(request, pk):
    """Muestra el perfil público detallado de un proveedor."""
    proveedor = get_object_or_404(Proveedor, pk=pk)

    is_online_status = is_online(proveedor.ultima_conexion)

    propuestas = Propuesta.objects.filter(proveedor=proveedor)

    rubros_list = propuestas.values_list('rubros_ofertados', flat=True)
    rubros_ofertados = ', '.join(rubros_list) if rubros_list else 'No especificados'

    zona_geografica = (
        propuestas.first().zona_geografica if propuestas.exists() else 'No especificada'
    )

    context = {
        'proveedor': proveedor,
        'propuestas': propuestas,
        'rubros_ofertados': rubros_ofertados,
        'zona_geografica': zona_geografica,
        'is_online_status': is_online_status,
        'now': timezone.now(),
        'current_user': current_logged_in_user,
    }

    return render(request, 'usuarios/proveedor_perfil.html', context)

# Se asume que el usuario tiene la línea de importación correcta
from soporte.forms import TicketSoporteForm
from django.utils.html import strip_tags

def crear_ticket_soporte(request):
    """Vista para que un COMERCIANTE cree un ticket de soporte."""
    comerciante = current_logged_in_user
    if not comerciante:
        messages.error(request, "Debes iniciar sesión para crear un ticket de soporte.")
        return redirect('login')

    if request.method == 'POST':
        form = TicketSoporteForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.comerciante = comerciante
            ticket.save()
            messages.success(request, "Tu ticket de soporte fue enviado correctamente. El equipo técnico lo revisará.")
            return redirect('plataforma_comerciante')
    else:
        form = TicketSoporteForm()

    contexto = {
        'form': form,
        'comerciante': comerciante,
    }
    return render(request, 'usuarios/soporte/crear_ticket.html', contexto)

# --- DEFINICIÓN GLOBAL DE FUENTES RSS (MÉTODO ROBUSTO: FUENTE ÚNICA Y ESTABLE) ---
RSS_FEEDS = {
    'ESTABLE': {
        'title': 'Noticias Generales de Economía Chilena',
        'url': 'https://news.google.com/rss/search?q=negocios+chile+pymes&hl=es&gl=CL&ceid=CL:es',
    }
}

def noticias_view(request):
    """Muestra noticias del sector a partir de un feed RSS estable."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Debes iniciar sesión para acceder a las noticias.')
        return redirect('login') 
        
    comerciante = current_logged_in_user
    
    noticias = []
    
    source_key = 'ESTABLE'
    source = RSS_FEEDS[source_key] 
    
    feed_title = source['title']
    feed_url = source['url']

    try:
        feed = feedparser.parse(feed_url)
        
        # Extraer noticias (limitadas a 15 para buen rendimiento)
        for entry in getattr(feed, 'entries', [])[:15]: 
            try:
                fecha_str = entry.get('published', entry.get('updated', 'Fecha no disponible'))
                
                noticias.append({
                    'titulo': entry.title,
                    'link': entry.link,
                    'fecha': fecha_str,
                    'resumen': entry.get('summary', entry.get('description', 'Contenido no disponible')), 
                    'source_key': source_key
                })
            except Exception:
                continue 

    except Exception:
        noticias = []
        feed_title = "Fallo de Conexión"
    
    context = {
        'comerciante': current_logged_in_user,
        'rol_usuario': ROLES.get('COMERCIANTE', 'Usuario'), 
        'noticias': noticias,
        'feed_title': feed_title, 
    }
    
    return render(request, 'usuarios/noticias.html', context)

def redes_sociales_view(request):
    """Muestra enlaces a las redes sociales y canales oficiales."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Por favor, inicia sesión para acceder a esta sección.')
        return redirect('login')

    context = {
        'comerciante': current_logged_in_user,
        'rol_usuario': ROLES.get('COMERCIANTE', 'Usuario'),
    }

    return render(request, 'usuarios/redes_sociales.html', context)

# --- FUNCIÓN AUXILIAR PARA OBTENER EL PREVIEW DE NOTICIAS ---
def fetch_news_preview():
    """Obtiene un extracto de noticias del feed estable para mostrar en la plataforma."""
    try:
        stable_source = RSS_FEEDS['ESTABLE'] 
        feed = feedparser.parse(stable_source['url'])
        preview_news = []
        
        # Limita a 3 ítems y limpia tags
        for entry in getattr(feed, 'entries', [])[:3]: 
            preview_news.append({
                'title': strip_tags(entry.title),
                'link': entry.link
            })
        return preview_news
    except Exception:
        return []