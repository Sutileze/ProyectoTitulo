from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import feedparser 

from .models import (
    Comerciante,
    Post,
    Like,
    Comentario,
    INTERESTS_CHOICES,
    Beneficio,
    NIVELES,
    CATEGORIAS,
    Proveedor,
    Propuesta,
    RUBROS_CHOICES,
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

def calcular_nivel_y_progreso(puntos):
    NIVELES_VALORES = [nivel[0] for nivel in NIVELES]
    UMBRAL_PUNTOS = 100
    MAX_NIVEL_INDEX = len(NIVELES_VALORES) - 1

    nivel_index = min(MAX_NIVEL_INDEX, puntos // UMBRAL_PUNTOS)
    nivel_actual_codigo = NIVELES_VALORES[nivel_index]
    current_threshold = nivel_index * UMBRAL_PUNTOS

    if nivel_actual_codigo == 'DIAMANTE':
        progreso_porcentaje = 100
        puntos_restantes = 0
        puntos_siguiente_nivel = puntos
        proximo_nivel_display = 'Máximo'
    else:
        next_threshold = (nivel_index + 1) * UMBRAL_PUNTOS
        puntos_en_nivel = puntos - current_threshold
        puntos_a_avanzar = UMBRAL_PUNTOS

        puntos_restantes = next_threshold - puntos
        progreso_porcentaje = int((puntos_en_nivel / puntos_a_avanzar) * 100)
        puntos_siguiente_nivel = next_threshold
        proximo_nivel_display = dict(NIVELES).get(
            NIVELES_VALORES[nivel_index + 1],
            'N/A'
        )

    return {
        'nivel_codigo': nivel_actual_codigo,
        'puntos_restantes': puntos_restantes,
        'puntos_siguiente_nivel': puntos_siguiente_nivel,
        'progreso_porcentaje': progreso_porcentaje,
        'proximo_nivel': proximo_nivel_display,
    }


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

            nuevo_comerciante.puntos = 0
            nuevo_comerciante.nivel_actual = 'BRONCE'

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


# usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from .forms import LoginForm
from .models import Comerciante
   # si lo tienes en utils

current_logged_in_user = None  # asegúrate de tener esto definido arriba


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
                    # Actualizar nivel y última conexión
                    progreso = calcular_nivel_y_progreso(comerciante.puntos)
                    comerciante.nivel_actual = progreso['nivel_codigo']
                    comerciante.ultima_conexion = timezone.now()
                    comerciante.save(update_fields=['ultima_conexion', 'nivel_actual']) 
                    
                    # Guardamos en la variable global usada en admin/soporte
                    current_logged_in_user = comerciante
                    
                    messages.success(request, f'¡Bienvenido {comerciante.nombre_apellido}!')

                    # 🔹 1. Si es ADMIN → panel admin
                    if comerciante.rol == 'ADMIN':
                        return redirect('panel_admin')

                    # 🔹 2. Si es TÉCNICO → panel de soporte
                    if comerciante.rol == 'TECNICO':
                        return redirect('soporte:panel_soporte')


                    # 🔹 3. Si es proveedor → panel proveedor
                    if getattr(comerciante, 'es_proveedor', False):
                        return redirect('proveedor_dashboard')

                    # 🔹 4. Si no, plataforma normal
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
    progreso = calcular_nivel_y_progreso(comerciante.puntos)

    if comerciante.nivel_actual != progreso['nivel_codigo']:
        comerciante.nivel_actual = progreso['nivel_codigo']
        comerciante.save(update_fields=['nivel_actual'])

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

        'puntos_actuales': comerciante.puntos,
        'nivel_actual': dict(NIVELES).get(comerciante.nivel_actual, 'Desconocido'),
        'puntos_restantes': progreso['puntos_restantes'],
        'progreso_porcentaje': progreso['progreso_porcentaje'],
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
            likes_count=Count('likes', distinct=True),
            is_liked=Count(
                'likes',
                filter=Q(likes__comerciante=current_logged_in_user)
            )
        )
        .prefetch_related(
            'comentarios',
            'comentarios__comerciante'
        )
    )

    categoria_filtros = request.GET.getlist('categoria', [])

    if categoria_filtros and 'TODAS' not in categoria_filtros:
        posts = posts_query.filter(
            categoria__in=categoria_filtros
        ).order_by('-fecha_publicacion')
    else:
        posts = posts_query.all().order_by('-fecha_publicacion')
        if not categoria_filtros or 'TODAS' in categoria_filtros:
            categoria_filtros = ['TODOS']

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
            likes_count=Count('likes', distinct=True),
            is_liked=Count(
                'likes',
                filter=Q(likes__comerciante=current_logged_in_user)
            )
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


def like_post_view(request, post_id):
    global current_logged_in_user

    if not current_logged_in_user:
        messages.error(request, 'Debes iniciar sesión para dar like.')
        return redirect('login')

    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        like, created = Like.objects.get_or_create(
            post=post,
            comerciante=current_logged_in_user
        )

        if not created:
            like.delete()
            messages.success(request, 'Dislike registrado.')
        else:
            messages.success(request, '¡Like registrado!')

    return redirect('plataforma_comerciante')


# --- Beneficios ---

def beneficios_view(request):
    global current_logged_in_user

    if not current_logged_in_user:
        messages.warning(
            request,
            'Por favor, inicia sesión para acceder a los beneficios.'
        )
        return redirect('login')

    comerciante = current_logged_in_user
    progreso = calcular_nivel_y_progreso(comerciante.puntos)

    category_filter = request.GET.get('category', 'TODOS')
    sort_by = request.GET.get('sort_by', '-fecha_creacion')

    beneficios_queryset = Beneficio.objects.all()

    if category_filter and category_filter != 'TODOS':
        beneficios_queryset = beneficios_queryset.filter(categoria=category_filter)

    valid_sort_fields = [
        'vence',
        '-vence',
        'puntos_requeridos',
        '-puntos_requeridos',
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

        'puntos_actuales': comerciante.puntos,
        'nivel_actual': dict(NIVELES).get(progreso['nivel_codigo'], 'Bronce'),
        'puntos_restantes': progreso['puntos_restantes'],
        'puntos_siguiente_nivel': progreso['puntos_siguiente_nivel'],
        'progreso_porcentaje': progreso['progreso_porcentaje'],
        'proximo_nivel': progreso['proximo_nivel'],

        'beneficios': beneficios_queryset,
        'no_beneficios_disponibles': no_beneficios_disponibles,
        'CATEGORIAS': CATEGORIAS,
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
    
    from proveedor.models import Proveedor  # importante: importar del app proveedor

    try:
        proveedor_qs = Proveedor.objects.get(usuario=current_logged_in_user)
    except Proveedor.DoesNotExist:
        proveedor_qs = None

    context = {
        'comerciante': current_logged_in_user,
        'proveedor': proveedor_qs,
    }

    # 🔴 AQUÍ estaba el problema: nombre de template
    return render(request, 'proveedores/perfil.html', context)


# --- Directorio de proveedores ---

def directorio_view(request):
    # Cargar algunos proveedores de ejemplo (solo en desarrollo)
    try:
        p1, _ = Proveedor.objects.get_or_create(
            nombre='Distribuidora El Sol',
            defaults={
                'email_contacto': 'contacto@elsol.cl',
                'whatsapp_contacto': '+56911110000',
                'descripcion': (
                    'Proveedores de frutas y verduras frescas de temporada. '
                    'Entrega a domicilio.'
                ),
                'ultima_conexion': timezone.now() - timedelta(minutes=1),
            },
        )
        p2, _ = Proveedor.objects.get_or_create(
            nombre='Carnes El Gaucho',
            defaults={
                'email_contacto': 'carnes@gaucho.cl',
                'whatsapp_contacto': '+56922220000',
                'descripcion': (
                    'Las mejores carnes de vacuno, cerdo y pollo. '
                    'Calidad garantizada.'
                ),
                'ultima_conexion': timezone.now() - timedelta(minutes=10),
            },
        )
        p3, _ = Proveedor.objects.get_or_create(
            nombre='Abarrotes Don Pepe',
            defaults={
                'email_contacto': 'info@donpepe.cl',
                'whatsapp_contacto': '+56933330000',
                'descripcion': (
                    'Amplio surtido de abarrotes, conservas y productos no perecibles.'
                ),
                'ultima_conexion': timezone.now() - timedelta(seconds=30),
            },
        )
        p4, _ = Proveedor.objects.get_or_create(
            nombre='Panadería La Espiga',
            defaults={
                'email_contacto': 'pan@espiga.cl',
                'whatsapp_contacto': '+56944440000',
                'descripcion': (
                    'Pan fresco, pasteles y bollería artesanal. Despacho diario.'
                ),
                'ultima_conexion': timezone.now() - timedelta(hours=2),
            },
        )
        p5, _ = Proveedor.objects.get_or_create(
            nombre='Limpieza Total',
            defaults={
                'email_contacto': 'limpieza@total.cl',
                'whatsapp_contacto': '+56955550000',
                'descripcion': (
                    'Productos de limpieza industrial y para el hogar. '
                    'Precios mayoristas.'
                ),
                'ultima_conexion': timezone.now() - timedelta(minutes=2),
            },
        )
        p6, _ = Proveedor.objects.get_or_create(
            nombre='Lácteos del Sur',
            defaults={
                'email_contacto': 'lacteos@sur.cl',
                'whatsapp_contacto': '+56966660000',
                'descripcion': (
                    'Leche, quesos, yogures y más. Directo del productor.'
                ),
                'ultima_conexion': timezone.now() - timedelta(minutes=1),
            },
        )

        if not Propuesta.objects.exists():
            Propuesta.objects.create(
                proveedor=p1,
                titulo='Distribuimos frutas y verduras',
                rubros_ofertados='Frutas y Verduras, Vegetales',
                zona_geografica='Santiago Centro',
            )
            Propuesta.objects.create(
                proveedor=p2,
                titulo='Carnes de alta calidad',
                rubros_ofertados='Carnes, Pollo, Pavo',
                zona_geografica='Providencia',
            )
            Propuesta.objects.create(
                proveedor=p3,
                titulo='Amplia variedad de abarrotes',
                rubros_ofertados='Abarrotes, Dulces',
                zona_geografica='Ñuñoa',
            )
            Propuesta.objects.create(
                proveedor=p4,
                titulo='Servicio de panadería diario',
                rubros_ofertados='Panadería, Pastelería',
                zona_geografica='La Reina',
            )
            Propuesta.objects.create(
                proveedor=p5,
                titulo='Insumos de limpieza mayorista',
                rubros_ofertados='Limpieza, Detergentes',
                zona_geografica='Las Condes',
            )
            Propuesta.objects.create(
                proveedor=p6,
                titulo='Venta directa de lácteos',
                rubros_ofertados='Lácteos, Quesos',
                zona_geografica='Maipú',
            )
    except Exception:
        pass

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

# al inicio del archivo ya debes tener:
from django.contrib import messages
from soporte.forms import TicketSoporteForm

# ...

def crear_ticket_soporte(request):
    """
    Vista para que un COMERCIANTE cree un ticket de soporte.
    Usa current_logged_in_user (no Django auth).
    """
    from .views import current_logged_in_user  # si ya estás en este archivo, NO repitas esto

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
