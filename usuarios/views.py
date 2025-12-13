from datetime import timedelta
import re 

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
from soporte.forms import TicketSoporteForm


# =========================================================================
# I. CONFIGURACIÓN Y CONSTANTES GLOBALES
# =========================================================================

ROLES = {
    'COMERCIANTE': 'Comerciante Verificado',
    'PROVEEDOR': 'Proveedor',
    'ADMIN': 'Administrador',
    'TECNICO': 'Técnico de soporte',
    'INVITADO': 'Invitado',
}

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

# --- CACHÉ Y RSS ---
LAST_NEWS_UPDATE_KEY = 'last_news_update'
CACHE_NEWS_KEY = 'cached_news_list'
UPDATE_INTERVAL_SECONDS = 86400  # 24 horas

RSS_FEEDS = {
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

# =========================================================================
# II. FUNCIONES AUXILIARES (HELPERS)
# =========================================================================

def get_current_user(request):
    comerciante_id = request.session.get('comerciante_id')
    if comerciante_id:
        try:
            return Comerciante.objects.get(id=comerciante_id) 
        except (Comerciante.DoesNotExist, Exception) as e:
            if 'comerciante_id' in request.session:
                del request.session['comerciante_id']
            return None
    return None


def is_online(last_login):
    if not last_login:
        return False
    return (timezone.now() - last_login) < timedelta(minutes=5)

def extract_image_url(entry):
    """Intenta extraer la URL de la imagen de una entrada de feedparser."""
    
    for attr in ['media_thumbnail', 'media_content', 'enclosures']:
        if hasattr(entry, attr) and getattr(entry, attr):
            data = getattr(entry, attr)
            if isinstance(data, list):
                 for media in data:
                    if media.get('url') and 'image' in media.get('type', ''):
                        return media['url']
            elif isinstance(data, dict) and data.get('url'):
                 if 'image' in data.get('type', ''):
                     return data['url']
    
    if hasattr(entry, 'media_thumbnail') and isinstance(entry.media_thumbnail, list) and entry.media_thumbnail:
        if entry.media_thumbnail[0].get('url'):
            return entry.media_thumbnail[0]['url']
        
    description_html = getattr(entry, 'summary', getattr(entry, 'description', ''))
    
    if isinstance(description_html, str):
        match = re.search(r'<img[^>]+src="([^">]+)"', description_html)
        if match:
            if not match.group(1).lower().endswith(('.gif', '.ico')) and 'thumb' not in match.group(1).lower():
                return match.group(1)

    return None

def fetch_news(max_entries_per_source=15, include_image=False):
    """Obtiene y filtra noticias de todos los feeds configurados."""
    all_news = []

    KEYWORDS = [
        'pyme', 'emprended', 'comerciante', 'negocio', 'asesoría', 'sercotec', 
        'corfo', 'fosis', 'proveedor', 'distribuidor',
        'costo', 'precio', 'inflación', 'ipc', 'consumo', 'crédito', 'caja',
        'ley', 'normativa', 'laboral', 'jornada', 'salud', 'seremi', 
        'fiscalización', 'municipal', 'patente', 'tributario', 'iva', 'impuesto',
        'digital', 'transbank', 'pos', 'qr', 'factura', 'boleta', 'inventario',
        'seguridad', 'delincuencia', 'robo', 'alerta',
    ]

    for source_title, source in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(source['url']) 
            
            for entry in getattr(feed, 'entries', [])[:max_entries_per_source]: 
                
                description = getattr(entry, 'summary', getattr(entry, 'content', [{'value': ''}])[0]['value'])
                
                title_lower = strip_tags(entry.title).lower()
                desc_lower = strip_tags(description).lower()
                
                is_relevant = False
                
                if source_title.startswith('Google News'):
                    is_relevant = True
                else:
                    for keyword in KEYWORDS:
                        if keyword in title_lower or keyword in desc_lower:
                            is_relevant = True
                            break
                
                if not is_relevant:
                    continue 

                news_item = {
                    'titulo': strip_tags(entry.title),
                    'resumen': strip_tags(description),
                    'link': entry.link,
                    'source_title': source_title,
                }
                
                if include_image:
                    news_item['image_url'] = extract_image_url(entry)
                
                all_news.append(news_item)
                
        except Exception as e:
            print(f"Error al obtener feed de {source_title}: {e}")
            continue 
            
    return all_news


def fetch_news_if_needed(request):
    """Controla la actualización de noticias a una vez cada 24 horas usando la sesión."""
    
    last_update = request.session.get(LAST_NEWS_UPDATE_KEY)
    current_time = timezone.now()

    # Intenta convertir el timestamp de la sesión a un objeto datetime
    if last_update:
        try:
            last_update_dt = timezone.datetime.fromtimestamp(last_update, tz=timezone.get_current_timezone())
        except (TypeError, ValueError):
            # Si el valor de la sesión es inválido, forzar actualización
            last_update_dt = None
    else:
        last_update_dt = None

    # Verificar si es la primera vez o si han pasado 24 horas
    if not last_update_dt or (current_time - last_update_dt).total_seconds() > UPDATE_INTERVAL_SECONDS:
        
        print("--- FORZANDO ACTUALIZACIÓN COMPLETA DE FEEDS (24H CUMPLIDAS) ---")
        all_news = fetch_news(max_entries_per_source=15, include_image=True)
        
        request.session[CACHE_NEWS_KEY] = all_news
        request.session[LAST_NEWS_UPDATE_KEY] = current_time.timestamp()
        request.session.modified = True 
        
        return all_news
        
    else:
        # Usar la versión en caché (rápida)
        elapsed_seconds = (current_time - last_update_dt).total_seconds()
        remaining_seconds = UPDATE_INTERVAL_SECONDS - elapsed_seconds
        
        remaining_minutes = int(remaining_seconds / 60)
        remaining_hours = int(remaining_minutes / 60)
        
        print(f"--- USANDO CACHÉ. Próxima actualización en: {remaining_hours}h {remaining_minutes % 60}m ---")
        return request.session.get(CACHE_NEWS_KEY, [])


def fetch_news_preview():
    """Función para obtener el preview de noticias para la barra lateral (sin caché de 24h)."""
    sources_to_preview = [
        'Google News: PYME y Leyes', 
        'Diario Financiero - Empresas (Filtrado)', 
        'La Tercera - Pulso (Negocios) (Filtrado)',
    ] 
    
    preview_news = []
    
    # Lógica de filtrado de keywords (redundante, pero necesaria para este helper)
    KEYWORDS = [
        'pyme', 'emprended', 'comerciante', 'negocio', 'ley', 'normativa', 
        'IVA', 'fiscalización', 'patente', 'corfo', 'sercotec', 'fosis', 
        'digital', 'seguridad', 'costo', 'precio'
    ]
    
    for source_title in sources_to_preview:
        if source_title in RSS_FEEDS:
            source = RSS_FEEDS[source_title]
            try:
                feed = feedparser.parse(source['url']) 
                
                for entry in getattr(feed, 'entries', [])[:2]: 
                    
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
                        'image_url': extract_image_url(entry), 
                    })
            except Exception:
                continue

    return preview_news


# =========================================================================
# III. VISTAS DE AUTENTICACIÓN Y PERFIL
# =========================================================================

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
                    'Este correo electrónico ya está registrado. Por favor, inicia sesión o usa otro correo.'
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
        messages.info(request, f'Adiós, {comerciante.nombre_apellido}. Has cerrado sesión.')
    
    if 'comerciante_id' in request.session:
        del request.session['comerciante_id'] 
    
    return redirect('login')


def perfil_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a tu perfil.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit_photo':
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=comerciante)
            if photo_form.is_valid():
                photo_form.save()
                messages.success(request, '¡Foto de perfil actualizada con éxito!')
                return redirect('perfil')
            else:
                messages.error(request, 'Error al subir la foto. Asegúrate de que sea un archivo válido.')

        elif action == 'edit_contact':
            contact_form = ContactInfoForm(request.POST, instance=comerciante)
            if contact_form.is_valid():
                nuevo_email = contact_form.cleaned_data.get('email')

                if (nuevo_email != comerciante.email and Comerciante.objects.filter(email=nuevo_email).exists()):
                    messages.error(request, 'Este correo ya está registrado por otro usuario.')
                else:
                    contact_form.save()
                    messages.success(request, 'Datos de contacto actualizados con éxito.')
                    return redirect('perfil')
            else:
                error_msgs = [f"{field.label}: {', '.join(error for error in field.errors)}" for field in contact_form if field.errors]
                messages.error(request, f'Error en los datos de contacto. {"; ".join(error_msgs)}')

        elif action == 'edit_business':
            business_form = BusinessDataForm(request.POST, instance=comerciante)
            if business_form.is_valid():
                business_form.save()
                messages.success(request, 'Datos del negocio actualizados con éxito.')
                return redirect('perfil')
            else:
                error_msgs = [f"{field.label}: {', '.join(error for error in field.errors)}" for field in business_form if field.errors]
                messages.error(request, f'Error en los datos del negocio. {"; ".join(error_msgs)}')

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

    intereses_actuales_codigos = (comerciante.intereses.split(',') if comerciante.intereses else [])
    interests_form = InterestsForm(initial={'intereses': [c for c in intereses_actuales_codigos if c]})

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


# =========================================================================
# IV. VISTAS DE COMUNIDAD (FORO)
# =========================================================================

def plataforma_comerciante_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a la plataforma.')
        return redirect('login')
        
    posts_query = (
        Post.objects
        .select_related('comerciante')
        .annotate(comentarios_count=Count('comentarios', distinct=True))
        .prefetch_related('comentarios','comentarios__comerciante')
    )

    tipo_filtro = request.GET.get('tipo_filtro', 'COMUNIDAD')
    
    if tipo_filtro == 'ADMIN':
        posts_query = posts_query.filter(comerciante__rol='ADMIN')
        category_options = ADMIN_CATEGORIES
    else: 
        community_keys = [key for key, value in COMMUNITY_CATEGORIES]
        posts_query = posts_query.filter(categoria__in=community_keys)
        category_options = COMMUNITY_CATEGORIES

    categoria_filtros = request.GET.getlist('categoria', [])
    valid_categories_keys = [key for key, value in category_options]
    
    if categoria_filtros and 'TODAS' not in categoria_filtros and 'TODOS' not in categoria_filtros:
        posts = posts_query.filter(categoria__in=categoria_filtros).order_by('-fecha_publicacion')
    else:
        posts = posts_query.filter(categoria__in=valid_categories_keys).order_by('-fecha_publicacion')
        if categoria_filtros and ('TODAS' in categoria_filtros or 'TODOS' in categoria_filtros):
            categoria_filtros = ['TODAS'] 

    user_can_post = True
    if comerciante and comerciante.rol != 'ADMIN' and tipo_filtro == 'ADMIN':
        user_can_post = False

    try:
        regiones = Region.objects.all().order_by('nombre')
    except Exception:
        regiones = [] 

    top_posters = Comerciante.objects.annotate(post_count=Count('posts')).exclude(rol='ADMIN').order_by('-post_count')[:5]

    news_preview = fetch_news_preview() 
    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get(comerciante.rol, 'Usuario'),
        'post_form': PostForm(),
        'posts': posts,
        'CATEGORIA_POST_CHOICES': CATEGORIA_POST_CHOICES,
        'COMMUNITY_CATEGORIES': COMMUNITY_CATEGORIES,
        'ADMIN_CATEGORIES': ADMIN_CATEGORIES,
        'categoria_seleccionada': categoria_filtros,
        'comentario_form': ComentarioForm(),
        'message': f'Bienvenido a la plataforma, {comerciante.nombre_apellido.split()[0]}.',
        'tipo_filtro': tipo_filtro,
        'regiones': regiones, 
        'user_can_post': user_can_post, 
        'top_posters': top_posters,  
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

        admin_category_keys = [key for key, _ in ADMIN_CATEGORIES]
        community_category_keys = [key for key, _ in COMMUNITY_CATEGORIES]
        
        is_admin_category = selected_category in admin_category_keys
        is_community_category = selected_category in community_category_keys
        
        if is_admin_category and comerciante.rol != 'ADMIN':
            messages.error(request, 'No tienes permiso para publicar en la categoría seleccionada.')
            return redirect('plataforma_comerciante')
        
        if comerciante.rol == 'ADMIN' and is_community_category:
            messages.error(request, 'Como Administrador, solo puedes publicar en categorías de Administración.')
            return redirect('plataforma_comerciante')
        
        
        try:
            form = PostForm(request.POST, request.FILES)

            if form.is_valid():
                nuevo_post = form.save(commit=False)
                nuevo_post.comerciante = comerciante

                uploaded_file = form.cleaned_data.get('uploaded_file')

                if uploaded_file:
                    file_name = default_storage.save(f'posts/{uploaded_file.name}', uploaded_file)
                    nuevo_post.imagen_url = default_storage.url(file_name)

                nuevo_post.save()
                messages.success(request, '¡Publicación creada con éxito! Se ha añadido al foro.')
                return redirect('plataforma_comerciante')
            else:
                messages.error(request, f'Error al publicar. Corrige: {form.errors.as_text()}')
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
        .annotate(comentarios_count=Count('comentarios', distinct=True)),
        pk=post_id
    )

    comentarios = post.comentarios.select_related('comerciante').all().order_by('fecha_creacion')

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
            messages.error(request, 'Error al publicar el comentario. El contenido no puede estar vacío.')

    return redirect('plataforma_comerciante')


def redes_sociales_view(request):
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a esta sección.')
        return redirect('login')

    context = {
        'comerciante': comerciante,
        'rol_usuario': ROLES.get('COMERCIANTE', 'Usuario'),
    }

    return render(request, 'usuarios/redes_sociales.html', context)


# =========================================================================
# V. VISTAS DE NOTICIAS Y BENEFICIOS
# =========================================================================

def noticias_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a las noticias.')
        return redirect('login')

    source_seleccionada = request.GET.get('fuente', 'TODOS')
    theme_seleccionada = request.GET.get('tematica', 'TODOS')

    # Obtener todas las noticias, usando la caché si no ha pasado el tiempo
    all_news = fetch_news_if_needed(request) 

    noticias_filtradas = all_news
    
    if source_seleccionada != 'TODOS':
        noticias_filtradas = [n for n in noticias_filtradas if n['source_title'] == source_seleccionada]

    fuentes_disponibles = sorted(list(RSS_FEEDS.keys()))
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


def beneficios_view(request):
    
    comerciante = get_current_user(request)

    if not comerciante:
        messages.warning(request, 'Por favor, inicia sesión para acceder a los beneficios.')
        return redirect('login')

    comerciante = comerciante

    CATEGORIAS_CHOICES = CATEGORIAS 
    
    category_filter = request.GET.get('category', 'TODOS')
    sort_by = request.GET.get('sort_by', '-fecha_creacion')

    beneficios_queryset = Beneficio.objects.all()

    if category_filter and category_filter != 'TODOS':
        beneficios_queryset = beneficios_queryset.filter(categoria=category_filter)

    valid_sort_fields = ['vence', '-vence', '-fecha_creacion']
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


# =========================================================================
# VI. VISTAS DE DIRECTORIO Y PROVEEDORES
# =========================================================================

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


def directorio_view(request):
    
    comerciante = get_current_user(request) 

    rubro_filter = request.GET.get('rubro', 'TODOS')
    region_filter_id = request.GET.get('region') 

    propuestas_queryset = Propuesta.objects.select_related('proveedor').all()

    if rubro_filter and rubro_filter != 'TODOS':
        propuestas_queryset = propuestas_queryset.filter(rubros_ofertados__icontains=rubro_filter)
    
    if region_filter_id and region_filter_id != '':
        try:
            propuestas_queryset = propuestas_queryset.filter(proveedor__region__id=region_filter_id)
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
        'ZONAS': ['Santiago Centro', 'Providencia', 'Ñuñoa', 'Las Condes', 'Maipú', 'La Reina'],
        'current_rubro': rubro_filter,
        'current_zona': region_filter_id, 
        'current_sort': sort_by,
        'comerciante': comerciante,
        'regiones': regiones, 
        'region_seleccionada': region_filter_id,
    }

    return render(request, 'usuarios/directorio.html', context)


def proveedor_perfil_view(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    current_user = get_current_user(request) 

    is_online_status = is_online(proveedor.ultima_conexion)

    propuestas = Propuesta.objects.filter(proveedor=proveedor)

    rubros_list = propuestas.values_list('rubros_ofertados', flat=True)
    rubros_ofertados = ', '.join(rubros_list) if rubros_list else 'No especificados'

    zona_geografica = (propuestas.first().zona_geografica if propuestas.exists() else 'No especificada')

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


# =========================================================================
# VII. VISTAS DE SOPORTE
# =========================================================================

def crear_ticket_soporte(request):
    
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