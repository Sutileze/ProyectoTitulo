from datetime import timedelta
import re # NUEVA IMPORTACIÓN para el manejo de imágenes en la descripción

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

# --- CONFIGURACIÓN GLOBAL ---

ROLES = {
    'COMERCIANTE': 'Comerciante Verificado',
    'PROVEEDOR': 'Proveedor',
    'ADMIN': 'Administrador',
    'TECNICO': 'Técnico de soporte',
    'INVITADO': 'Invitado',
}

# --- DEFINICIÓN DE CATEGORÍAS SEPARADAS ---
COMMUNITY_CATEGORIES = [
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

# --- DEFINICIÓN GLOBAL DE FUENTES RSS (RESTAURADA CON FILTROS CLAVE) ---
# Se reestablecen los feeds de los diarios chilenos y se añade el de Google filtrado
RSS_FEEDS = {
    # Fuente clave para relevancia, filtrada por palabras PYME
    'Google News: PYME y Leyes': {
        'url': 'https://news.google.com/rss/search?q=%22pymes%22+OR+%22emprendedores%22+OR+%22leyes+pyme%22+site%3Adf.cl+OR+site%3Aemol.com+OR+site%3Alatercera.com&hl=es&gl=CL&ceid=CL:es',
        'key': 'google_pyme',
    },
    'Diario Financiero - Empresas (Filtrado)': {
        'url': 'https://www.diariofinanciero.cl/feed/empresas',
        'key': 'df_empresas',
    },
    'Emol - Economía (Filtrado)': {
        'url': 'http://rss.emol.com/economia.asp', 
        'key': 'emol_econ',
    },
    'La Tercera - Pulso (Negocios) (Filtrado)': {
        'url': 'https://www.latercera.com/canal/pulso/feed/',
        'key': 'pulso',
    },
    'El Dínamo - Actualidad': { 
        'url': 'https://www.eldinamo.com/feed/', 
        'key': 'dinamo',
    },
    'CIPER Chile - Investigación': {
        'url': 'https://ciperchile.cl/feed/',
        'key': 'ciper',
    },
}

def extract_image_url(entry):
    """
    Intenta extraer la URL de la imagen de una entrada de feedparser,
    revisando múltiples etiquetas y el contenido HTML del resumen/descripción.
    """
    
    # 1. Buscar en media_thumbnail, media_content, o enclosures
    for attr in ['media_thumbnail', 'media_content', 'enclosures']:
        if hasattr(entry, attr) and getattr(entry, attr):
            if isinstance(getattr(entry, attr), list):
                 for media in getattr(entry, attr):
                    if media.get('url') and 'image' in media.get('type', ''):
                        return media['url']
            elif isinstance(getattr(entry, attr), dict) and getattr(entry, attr).get('url'):
                 if 'image' in getattr(entry, attr).get('type', ''):
                     return getattr(entry, attr)['url']
    
    # Manejo de la lista en media_thumbnail directamente
    if hasattr(entry, 'media_thumbnail') and isinstance(entry.media_thumbnail, list) and entry.media_thumbnail:
        if entry.media_thumbnail[0].get('url'):
            return entry.media_thumbnail[0]['url']
        
    # 2. Buscar la etiqueta <img> dentro del contenido/resumen (Solución para feeds que embeben HTML)
    description_html = getattr(entry, 'summary', getattr(entry, 'description', ''))
    
    if isinstance(description_html, str):
        # Búsqueda de cualquier URL dentro de un tag <img>
        match = re.search(r'<img[^>]+src="([^">]+)"', description_html)
        if match:
            # Asegura que la URL de la imagen no sea un GIF o ícono pequeño
            if not match.group(1).lower().endswith(('.gif', '.ico')) and 'thumb' not in match.group(1).lower():
                return match.group(1)

    return None

# --- Funciones helper ---

def get_current_user(request):
    """Obtiene el usuario actual de la sesión."""
    comerciante_id = request.session.get('comerciante_id')
    if comerciante_id:
        try:
            return Comerciante.objects.get(id=comerciante_id) 
        except Comerciante.DoesNotExist:
            if 'comerciante_id' in request.session:
                del request.session['comerciante_id']
            return None
        except Exception as e:
            # Captura errores de DB/conexión y limpia la sesión para forzar re-login
            print(f"Error crítico en get_current_user: {e}")
            if 'comerciante_id' in request.session:
                del request.session['comerciante_id']
            return None
    return None


def is_online(last_login):
    if not last_login:
        return False
    return (timezone.now() - last_login) < timedelta(minutes=5)

def fetch_news(max_entries_per_source=15, include_image=False):
    """
    Función que obtiene noticias de todos los feeds configurados y las filtra 
    por palabras clave si no provienen de la fuente de Google ya filtrada.
    """
    all_news = []

    # Lista de palabras clave para filtrar el contenido irrelevante 
    # (basado en las temáticas que usted solicitó)
    KEYWORDS = [
        # Relevancia y gestión
        'pyme', 'emprended', 'comerciante', 'negocio', 'asesoría', 'sercotec', 
        'corfo', 'fosis', 'proveedor', 'distribuidor',
        # Economía y finanzas
        'costo', 'precio', 'inflación', 'ipc', 'consumo', 'crédito', 'caja',
        # Leyes y normativas
        'ley', 'normativa', 'laboral', 'jornada', 'salud', 'seremi', 
        'fiscalización', 'municipal', 'patente', 'tributario', 'iva', 'impuesto',
        # Tecnología y digitalización
        'digital', 'transbank', 'pos', 'qr', 'factura', 'boleta', 'inventario',
        # Seguridad
        'seguridad', 'delincuencia', 'robo', 'alerta',
    ]

    for source_title, source in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(source['url']) 
            
            # Recolectar hasta max_entries_per_source (15)
            for entry in getattr(feed, 'entries', [])[:max_entries_per_source]: 
                
                # Usar el resumen si existe, si no, el contenido completo.
                description = getattr(entry, 'summary', getattr(entry, 'content', [{'value': ''}])[0]['value'])
                
                title_lower = strip_tags(entry.title).lower()
                desc_lower = strip_tags(description).lower()
                
                # --- LÓGICA DE FILTRADO CLAVE ---
                is_relevant = False
                
                # La fuente de Google News ya está pre-filtrada por su URL, la incluimos siempre.
                if source_title.startswith('Google News'):
                    is_relevant = True
                else:
                    # Aplicar filtro de palabras clave a las fuentes generales (DF, Emol, LT, etc.)
                    for keyword in KEYWORDS:
                        if keyword in title_lower or keyword in desc_lower:
                            is_relevant = True
                            break
                
                if not is_relevant:
                    continue # Saltar la noticia si no pasa el filtro de relevancia.
                # --- FIN LÓGICA DE FILTRADO ---

                news_item = {
                    'titulo': strip_tags(entry.title),
                    'resumen': strip_tags(description),
                    'link': entry.link,
                    'source_title': source_title,
                }
                
                if include_image:
                    # Incluye la URL de la imagen si se solicita
                    news_item['image_url'] = extract_image_url(entry)
                
                all_news.append(news_item)
                
        except Exception as e:
            # En caso de error, imprime (opcional) y continúa con la siguiente fuente
            print(f"Error al obtener feed de {source_title}: {e}")
            continue 
            
    return all_news

def fetch_news_preview():
    """Función auxiliar que obtiene el preview de noticias para la barra lateral."""
    # Usar solo las fuentes más relevantes para el preview
    sources_to_preview = [
        'Google News: PYME y Leyes', 
        'Diario Financiero - Empresas (Filtrado)', 
        'La Tercera - Pulso (Negocios) (Filtrado)',
    ] 
    
    preview_news = []
    
    for source_title in sources_to_preview:
        if source_title in RSS_FEEDS:
            source = RSS_FEEDS[source_title]
            try:
                feed = feedparser.parse(source['url']) 
                
                # Solo 2 entradas para el preview, incluyendo la imagen
                for entry in getattr(feed, 'entries', [])[:2]: 
                    
                    # Se incluye la lógica de filtrado de fetch_news aquí también para el preview
                    KEYWORDS = [
                        'pyme', 'emprended', 'comerciante', 'negocio', 'ley', 'normativa', 
                        'IVA', 'fiscalización', 'patente', 'corfo', 'sercotec', 'fosis', 
                        'digital', 'seguridad', 'costo', 'precio'
                    ]
                    
                    description = getattr(entry, 'summary', getattr(entry, 'content', [{'value': ''}])[0]['value'])
                    title_lower = strip_tags(entry.title).lower()
                    desc_lower = strip_tags(description).lower()

                    is_relevant = source_title.startswith('Google News') or any(
                        keyword in title_lower or keyword in desc_lower for keyword in KEYWORDS
                    )
                    
                    if not is_relevant:
                        continue

                    preview_news.append({
                        'title': strip_tags(entry.title),
                        'link': entry.link,
                        'source_title': source_title,
                        'image_url': extract_image_url(entry), # AÑADIDO EL CAMPO DE IMAGEN
                    })
            except Exception:
                continue

    return preview_news


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
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                comerciante = Comerciante.objects.get(email=email)

                if check_password(password, comerciante.password_hash):
                    
                    # Usar sesión para multisesión
                    request.session['comerciante_id'] = comerciante.id 
                    
                    comerciante.ultima_conexion = timezone.now()
                    comerciante.save(update_fields=['ultima_conexion']) 
                    
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

    contexto = {'form': form}
    return render(request, 'usuarios/cuenta.html', contexto)


def logout_view(request):
    
    comerciante = get_current_user(request)

    if comerciante:
        messages.info(
            request,
            f'Adiós, {comerciante.nombre_apellido}. Has cerrado sesión.'
        )
    
    if 'comerciante_id' in request.session:
        del request.session['comerciante_id'] # Elimina el ID de la sesión
    
    return redirect('login')


# --- Perfil ---

def perfil_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a tu perfil.')
        return redirect('login')
    
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
    
    comerciante = get_current_user(request)

    if not comerciante:
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

    # Lógica de filtrado de Administrador
    tipo_filtro = request.GET.get('tipo_filtro', 'COMUNIDAD')
    
    # 1. Definir opciones de categorías válidas según el filtro principal
    if tipo_filtro == 'ADMIN':
        posts_query = posts_query.filter(comerciante__rol='ADMIN')
        category_options = ADMIN_CATEGORIES
    else: # 'COMUNIDAD'
        community_keys = [key for key, value in COMMUNITY_CATEGORIES]
        posts_query = posts_query.filter(categoria__in=community_keys)
        category_options = COMMUNITY_CATEGORIES

    # 2. Aplicar filtro de subcategoría (Temas del Foro)
    categoria_filtros = request.GET.getlist('categoria', [])
    
    # Obtener todas las claves válidas para el filtro actual
    valid_categories_keys = [key for key, value in category_options]
    
    if categoria_filtros and 'TODAS' not in categoria_filtros and 'TODOS' not in categoria_filtros:
        # Si se seleccionan categorías específicas (que no sean 'TODAS')
        posts = posts_query.filter(
            categoria__in=categoria_filtros
        ).order_by('-fecha_publicacion')
    else:
        # Si no hay filtro o se selecciona 'TODAS'
        posts = posts_query.filter(categoria__in=valid_categories_keys).order_by('-fecha_publicacion')
        if categoria_filtros and ('TODAS' in categoria_filtros or 'TODOS' in categoria_filtros):
            categoria_filtros = ['TODAS'] # Para mantener el filtro 'Todas' resaltado

    # 3. Restricción de publicación
    user_can_post = True
    if comerciante and comerciante.rol != 'ADMIN' and tipo_filtro == 'ADMIN':
        # Un Comerciante o Proveedor no puede publicar en el feed de ADMIN
        user_can_post = False

    # NUEVO: Carga de regiones para la barra lateral
    try:
        regiones = Region.objects.all().order_by('nombre')
    except Exception:
        regiones = [] # Retorna lista vacía si la tabla no existe o falla la importación

    top_posters = Comerciante.objects.annotate(
        post_count=Count('posts')
    ).exclude(rol='ADMIN').order_by('-post_count')[:5] #

    news_preview = fetch_news_preview() 
    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get(comerciante.rol, 'Usuario'),
        'post_form': PostForm(),
        'posts': posts,
        # Se pasa la lista completa de categorías al formulario de post y las separadas para los filtros
        'CATEGORIA_POST_CHOICES': CATEGORIA_POST_CHOICES,
        'COMMUNITY_CATEGORIES': COMMUNITY_CATEGORIES,
        'ADMIN_CATEGORIES': ADMIN_CATEGORIES,
        'categoria_seleccionada': categoria_filtros,
        'comentario_form': ComentarioForm(),
        'message': (
            f'Bienvenido a la plataforma, '
            f'{comerciante.nombre_apellido.split()[0]}.'
        ),
        'tipo_filtro': tipo_filtro,
        'regiones': regiones, # AÑADIDO al contexto
        'user_can_post': user_can_post, # NUEVA VARIABLE DE CONTEXTO
        'top_posters': top_posters,  # AÑADIDO: Lista de usuarios más activos
        'news_preview': news_preview,
    }

    return render(request, 'usuarios/plataforma_comerciante.html', context)


def publicar_post_view(request):
    
    comerciante = get_current_user(request)

    if request.method == 'POST':
        if not comerciante:
            messages.error(request, 'Debes iniciar sesión para publicar.')
            return redirect('login')
        
        selected_category = request.POST.get('categoria')

        # Determinar si la categoría seleccionada es de Administración o Comunidad
        admin_category_keys = [key for key, _ in ADMIN_CATEGORIES]
        community_category_keys = [key for key, _ in COMMUNITY_CATEGORIES]
        
        is_admin_category = selected_category in admin_category_keys
        is_community_category = selected_category in community_category_keys
        
        # VALIDACIÓN 1: Restricción para Comerciantes/Proveedores publicando en Admin categorías (EXISTENTE)
        if is_admin_category and comerciante.rol != 'ADMIN':
            messages.error(
                request, 
                'No tienes permiso para publicar en la categoría seleccionada.'
            )
            return redirect('plataforma_comerciante')
        
        # VALIDACIÓN 2: Restricción para Admins publicando en Comunidad categorías (REGLA SOLICITADA)
        if comerciante.rol == 'ADMIN' and is_community_category:
            messages.error(
                request,
                'Como Administrador, solo puedes publicar en categorías de Administración.'
            )
            return redirect('plataforma_comerciante')
        
        
        try:
            form = PostForm(request.POST, request.FILES)

            if form.is_valid():
                nuevo_post = form.save(commit=False)
                nuevo_post.comerciante = comerciante

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
    
    comerciante = get_current_user(request)

    if not comerciante:
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
    ).all().order_by('fecha_creacion')

    context = {
        'comerciante': comerciante,
        'post': post,
        'comentarios': comentarios,
        'comentario_form': ComentarioForm(),
    }
    return render(request, 'usuarios/post_detail.html', context)


def add_comment_view(request, post_id):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.error(request, 'No autorizado para comentar. Inicia sesión.')
        return redirect('login')

    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            nuevo_comentario = form.save(commit=False)
            nuevo_comentario.post = post
            nuevo_comentario.comerciante = comerciante
            nuevo_comentario.save()
            messages.success(request, '¡Comentario publicado con éxito!')
        else:
            messages.error(
                request,
                'Error al publicar el comentario. El contenido no puede estar vacío.'
            )

    return redirect('plataforma_comerciante')


# --- Beneficios (RESTAURADA) ---

def beneficios_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(
            request,
            'Por favor, inicia sesión para acceder a los beneficios.'
        )
        return redirect('login')

    comerciante = comerciante

    # La lista de categorías para el filtro
    CATEGORIAS_CHOICES = CATEGORIAS 
    
    category_filter = request.GET.get('category', 'TODOS')
    sort_by = request.GET.get('sort_by', '-fecha_creacion')

    beneficios_queryset = Beneficio.objects.all()

    if category_filter and category_filter != 'TODOS':
        beneficios_queryset = beneficios_queryset.filter(categoria=category_filter)

    # AJUSTADO: Eliminando opciones de ordenamiento por puntos
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


# --- Gestión de rol proveedor ---


def proveedor_dashboard_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante or not getattr(comerciante, 'es_proveedor', False):
        messages.warning(request, 'Acceso denegado. Esta interfaz es solo para Proveedores activos.')
        return redirect('perfil')
    
    from proveedor.models import Proveedor 

    try:
        proveedor_qs = Proveedor.objects.get(usuario=comerciante)
    except Proveedor.DoesNotExist:
        proveedor_qs = None

    context = {
        'comerciante': comerciante,
        'proveedor': proveedor_qs,
    }

    return render(request, 'proveedores/perfil.html', context)


# --- Directorio de proveedores ---

def directorio_view(request):
    
    comerciante = get_current_user(request) # Obtener el comerciante

    rubro_filter = request.GET.get('rubro', 'TODOS')
    # AÑADIDO: Obtener filtro de región
    region_filter_id = request.GET.get('region') 

    propuestas_queryset = Propuesta.objects.select_related('proveedor').all()

    if rubro_filter and rubro_filter != 'TODOS':
        propuestas_queryset = propuestas_queryset.filter(
            rubros_ofertados__icontains=rubro_filter
        )
    
    # NUEVO: Lógica de filtrado por Región en el Directorio
    if region_filter_id and region_filter_id != '':
        try:
            # Asumiendo que Proveedor tiene una FK a Region.
            propuestas_queryset = propuestas_queryset.filter(
                proveedor__region__id=region_filter_id
            )
        except Exception:
            # Si el modelo Proveedor no tiene la FK a Region (por si hubo errores de migración),
            # simplemente se omite el filtro.
            pass


    # ELIMINADO: zona_filter (Charfield) para usar region_filter (FK)
    # y el sort_by (se simplifica la lógica)
    sort_by = request.GET.get('ordenar_por', 'proveedor__nombre') 
    valid_sort_fields = ['proveedor__nombre', '-proveedor__nombre']
    
    if sort_by in valid_sort_fields:
        propuestas_queryset = propuestas_queryset.order_by(sort_by)
    else:
        sort_by = 'proveedor__nombre'
        propuestas_queryset = propuestas_queryset.order_by(sort_by)
        

    # NUEVO: Carga de regiones para el contexto del directorio
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
        'current_zona': region_filter_id, # Usamos la ID de región seleccionada aquí
        'current_sort': sort_by,
        'comerciante': comerciante,
        'regiones': regiones, # AÑADIDO para el filtro
        'region_seleccionada': region_filter_id,
    }

    return render(request, 'usuarios/directorio.html', context)


def proveedor_perfil_view(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    current_user = get_current_user(request) # Obtiene el usuario para mostrar su estado

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
        'current_user': current_user,
    }

    return render(request, 'usuarios/proveedor_perfil.html', context)

# Se asume que el usuario tiene la línea de importación correcta
from soporte.forms import TicketSoporteForm
# NOTA: strip_tags y re están importados arriba

def crear_ticket_soporte(request):
    """
    Vista para que un COMERCIANTE cree un ticket de soporte.
    Usa el sistema de sesión.
    """
    comerciante = get_current_user(request)
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


def noticias_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a las noticias.')
        return redirect('login')

    source_seleccionada = request.GET.get('fuente', 'TODOS')
    theme_seleccionada = request.GET.get('tematica', 'TODOS')

    # 1. Obtener todas las noticias (con el nuevo límite de 15) e incluir imagen
    # La función fetch_news ahora incluye la lógica de filtrado por palabras clave
    all_news = fetch_news(max_entries_per_source=15, include_image=True) 

    noticias_filtradas = all_news
    
    # Aplicar filtrado por fuente (si el usuario ha seleccionado una)
    if source_seleccionada != 'TODOS':
        noticias_filtradas = [
            n for n in noticias_filtradas 
            if n['source_title'] == source_seleccionada
        ]

    # La lista de fuentes disponibles para el filtro (se obtiene de las claves del diccionario)
    fuentes_disponibles = sorted(list(RSS_FEEDS.keys()))
    
    # La lista de temáticas disponibles (placeholder para el filtro que no se implementó en Python)
    tematicas_disponibles = ['Negocios', 'Leyes', 'Emprendimiento', 'Comercio'] 

    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get(comerciante.rol, 'Usuario'),
        'noticias': noticias_filtradas, 
        'fuentes': fuentes_disponibles, 
        'source_seleccionada': source_seleccionada,
        'tematicas': tematicas_disponibles, 
        'theme_seleccionada': theme_seleccionada,
    }
    return render(request, 'usuarios/noticias.html', context)


def redes_sociales_view(request):
    """Restaura la vista que estaba dando AttributeError en urls.py."""
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a esta sección.')
        return redirect('login')

    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get('COMERCIANTE', 'Usuario'),
    }

    return render(request, 'usuarios/redes_sociales.html', context)