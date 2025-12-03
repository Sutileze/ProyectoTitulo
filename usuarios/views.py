from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import feedparser 
from django.utils.html import strip_tags # Necesaria para fetch_news_preview
# ELIMINADO: from proveedor.models import Region, Comuna

from .models import (
    Comerciante,
    Post,
    # ELIMINADO: Like, NIVELES
    Comentario,
    INTERESTS_CHOICES,
    Proveedor,
    Propuesta,
    RUBROS_CHOICES,
    Beneficio, # MANTENIDO: para la vista de beneficios
    CATEGORIAS, # MANTENIDO: para la vista de beneficios
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

# --- Simulación de sesión global ---
current_logged_in_user = None

ROLES = {
    'COMERCIANTE': 'Comerciante Verificado',
    'PROVEEDOR': 'Proveedor',
    'ADMIN': 'Administrador',
    'INVITADO': 'Invitado',
}


# --- Funciones helper ---

# ELIMINADO: def calcular_nivel_y_progreso(puntos):

def is_online(last_login):
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

            # ELIMINADO: Inicialización de puntos y nivel

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
    global current_logged_in_user
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                comerciante = Comerciante.objects.get(email=email)

                if check_password(password, comerciante.password_hash):
                    
                    # ELIMINADO: Lógica de actualización de nivel/puntos
                    
                    comerciante.ultima_conexion = timezone.now()
                    
                    # AJUSTADO: guardar sin nivel_actual ni puntos
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
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Por favor, inicia sesión para acceder a tu perfil.')
        return redirect('login')

    comerciante = current_logged_in_user
    
    # ELIMINADO: Lógica de cálculo y actualización de nivel/puntos

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

        # ELIMINADO: puntos/nivel del contexto
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
            # ELIMINADO: likes_count y is_liked
        )
        .prefetch_related(
            'comentarios',
            'comentarios__comerciante'
        )
    )

    # Lógica de filtrado de Administrador
    tipo_filtro = request.GET.get('tipo_filtro', 'COMUNIDAD')
    
    if tipo_filtro == 'ADMIN':
        posts_query = posts_query.filter(comerciante__rol='ADMIN')
        
    # ELIMINADO: Lógica de filtro por comuna/región

    categoria_filtros = request.GET.getlist('categoria', [])

    if categoria_filtros and 'TODAS' not in categoria_filtros:
        posts = posts_query.filter(
            categoria__in=categoria_filtros
        ).order_by('-fecha_publicacion')
    else:
        posts = posts_query.all().order_by('-fecha_publicacion')
        if not categoria_filtros or 'TODAS' in categoria_filtros:
            categoria_filtros = ['TODOS']

    # ELIMINADO: Carga de Comunas/Regiones para el contexto

    news_preview = fetch_news_preview() 
    context = {
        'comerciante': current_logged_in_user,
        'rol_usuario': ROLES.get(current_logged_in_user.rol, 'Usuario'),
        'post_form': PostForm(),
        'posts': posts,
        'CATEGORIA_POST_CHOICES': Post._meta.get_field('categoria').choices,
        'categoria_seleccionada': categoria_filtros,
        'comentario_form': ComentarioForm(),
        'message': (
            f'Bienvenido a la plataforma, '
            f'{current_logged_in_user.nombre_apellido.split()[0]}.'
        ),
        # ELIMINADO: Contexto adicional para el filtro de Comuna/Tipo
        'tipo_filtro': tipo_filtro,
    }

    return render(request, 'usuarios/plataforma_comerciante.html', context)


def publicar_post_view(request):
    global current_logged_in_user

    if request.method == 'POST':
        if not current_logged_in_user:
            messages.error(request, 'Debes iniciar sesión para publicar.')
            return redirect('login')

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
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Debes iniciar sesión para ver los detalles.')
        return redirect('login')

    post = get_object_or_404(
        Post.objects
        .select_related('comerciante')
        .annotate(
            comentarios_count=Count('comentarios', distinct=True),
            # ELIMINADO: likes_count y is_liked
        ),
        pk=post_id
    )

    comentarios = post.comentarios.select_related(
        'comerciante'
    ).all().order_by('fecha_creacion')

    context = {
        'comerciante': current_logged_in_user,
        'post': post,
        'comentarios': comentarios,
        'comentario_form': ComentarioForm(),
    }
    return render(request, 'usuarios/post_detail.html', context)


def add_comment_view(request, post_id):
    global current_logged_in_user

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

    return redirect('plataforma_comerciante')

def beneficios_view(request):
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(
            request,
            'Por favor, inicia sesión para acceder a los beneficios.'
        )
        return redirect('login')

    comerciante = current_logged_in_user

    # Se asume que CATEGORIAS se mantiene en models.py
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


# --- Directorio de proveedores ---

def directorio_view(request):
    
    rubro_filter = request.GET.get('rubro', 'TODOS')
    zona_filter = request.GET.get('zona', 'TODOS')
    sort_by = request.GET.get('ordenar_por', 'proveedor__nombre')

    propuestas_queryset = Propuesta.objects.select_related('proveedor').all()

    if rubro_filter and rubro_filter != 'TODOS':
        propuestas_queryset = propuestas_queryset.filter(
            rubros_ofertados__icontains=rubro_filter
        )
    if zona_filter and zona_filter != 'TODOS':
        propuestas_queryset = propuestas_queryset.filter(
            zona_geografica__icontains=zona_filter
        )

    valid_sort_fields = ['proveedor__nombre', '-proveedor__nombre']
    if sort_by in valid_sort_fields:
        propuestas_queryset = propuestas_queryset.order_by(sort_by)
    else:
        sort_by = 'proveedor__nombre'
        propuestas_queryset = propuestas_queryset.order_by(sort_by)

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
        'current_zona': zona_filter,
        'current_sort': sort_by,
        'comerciante': current_logged_in_user,
    }

    return render(request, 'usuarios/directorio.html', context)


def proveedor_perfil_view(request, pk):
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
    """
    Vista para que un COMERCIANTE cree un ticket de soporte.
    Usa current_logged_in_user (no Django auth).
    """
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
    """Implementa el feed RSS con una fuente única estable."""
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(request, 'Debes iniciar sesión para acceder a las noticias.')
        return redirect('login') 
        
    comerciante = current_logged_in_user
    
    noticias = []
    
    # Aquí seleccionamos la única fuente disponible y estable: GOOGLE_NEWS
    source_key = 'ESTABLE'
    source = RSS_FEEDS[source_key] 
    
    feed_title = source['title']
    feed_url = source['url']

    try:
        # 2. Parseo del RSS
        feed = feedparser.parse(feed_url)
        
        # 3. Extraer noticias (limitadas a 15 para buen rendimiento)
        for entry in getattr(feed, 'entries', [])[:15]: 
            # Usamos try-except interno para manejar entradas corruptas
            try:
                fecha_str = entry.get('published', entry.get('updated', 'Fecha no disponible'))
                
                noticias.append({
                    'titulo': entry.title,
                    'link': entry.link,
                    'fecha': fecha_str,
                    'resumen': entry.get('summary', entry.get('description', 'Contenido no disponible')), 
                    'source_key': source_key # Usamos la clave única para el color
                })
            except Exception:
                continue 

    except Exception:
        # Si la conexión falla, se retorna una lista vacía.
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
    """Restaura la vista que estaba dando AttributeError en urls.py."""
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
    # Usamos la única fuente estable definida globalmente en RSS_FEEDS
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
        # En caso de fallo, retorna una lista vacía para que el template use el fallback
        return []