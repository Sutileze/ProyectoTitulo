# proveedores/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import IntegrityError
from django.views.decorators.http import require_POST

from .models import (
    Proveedor,
    SolicitudContacto,
    ProductoServicio,
    Promocion,
    CategoriaProveedor,
    PAISES_CHOICES,
    REGIONES_CHOICES,
    COMUNAS_CHOICES,
    REGIONES_POR_PAIS,
    COMUNAS_POR_REGION,
)
from .forms import (
    LoginProveedorForm,
    RegistroProveedorForm,
    ProveedorForm,
    ProductoServicioForm,
    PromocionForm,
    SolicitudContactoForm,
)
from .decorators import proveedor_login_required

# Variable global para el proveedor actual
current_logged_in_proveedor = None


# ==================== AUTENTICACIÓN ====================

def login_proveedor_view(request):
    """Vista de login para proveedores"""
    global current_logged_in_proveedor
    
    if request.method == 'POST':
        form = LoginProveedorForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']
            
            try:
                proveedor = Proveedor.objects.get(email=email)
                
                if check_password(password, proveedor.password_hash):
                    proveedor.ultima_conexion = timezone.now()
                    proveedor.save(update_fields=['ultima_conexion'])
                    
                    current_logged_in_proveedor = proveedor
                    messages.success(request, f'¡Bienvenido {proveedor.nombre_empresa}!')
                    
                    return redirect('proveedores:dashboard_proveedor')
                else:
                    messages.error(request, 'Contraseña incorrecta.')
                    
            except Proveedor.DoesNotExist:
                messages.error(request, 'Este correo no está registrado como proveedor.')
        else:
            messages.error(request, 'Por favor, completa todos los campos.')
    else:
        form = LoginProveedorForm()
    
    return render(request, 'proveedores/login.html', {'form': form})


def registro_proveedor_view(request):
    """Vista de registro para proveedores"""
    if request.method == 'POST':
        form = RegistroProveedorForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                raw_password = form.cleaned_data.pop('password')
                form.cleaned_data.pop('confirm_password')
                
                proveedor = form.save(commit=False)
                proveedor.password_hash = make_password(raw_password)
                proveedor.save()
                
                messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión.')
                return redirect('proveedores:login_proveedor')
                
            except IntegrityError:
                messages.error(request, 'Este correo ya está registrado.')
            except Exception as e:
                messages.error(request, f'Error al crear la cuenta: {e}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistroProveedorForm()
    
    return render(request, 'proveedores/registro.html', {'form': form})


def logout_proveedor_view(request):
    """Vista de logout para proveedores"""
    global current_logged_in_proveedor
    current_logged_in_proveedor = None
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('proveedores:login_proveedor')


# ==================== VISTAS PÚBLICAS ====================

def directorio_proveedores(request):
    """Vista del directorio público de proveedores con filtros"""
    proveedores = Proveedor.objects.filter(activo=True).prefetch_related('categorias')

    # Filtros desde GET
    categoria_id = request.GET.get('categoria')
    pais = request.GET.get('pais')
    region = request.GET.get('region')
    comuna = request.GET.get('comuna')
    cobertura = request.GET.get('cobertura')
    busqueda = request.GET.get('q')

    if categoria_id:
        proveedores = proveedores.filter(categorias__id=categoria_id)

    if pais:
        proveedores = proveedores.filter(pais=pais)

    if region:
        proveedores = proveedores.filter(region=region)

    if comuna:
        proveedores = proveedores.filter(comuna=comuna)

    if cobertura:
        proveedores = proveedores.filter(cobertura=cobertura)

    if busqueda:
        proveedores = proveedores.filter(
            Q(nombre_empresa__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    # Ordenar: destacados primero, luego por fecha
    proveedores = proveedores.order_by('-destacado', '-fecha_registro')

    # Paginación
    paginator = Paginator(proveedores, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Datos para filtros
    categorias = CategoriaProveedor.objects.filter(activo=True)
    coberturas = Proveedor.COBERTURA_CHOICES

    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'paises': PAISES_CHOICES,
        'regiones': REGIONES_CHOICES,
        'comunas': COMUNAS_CHOICES,
        'coberturas': coberturas,
        'categoria_seleccionada': categoria_id,
        'pais_seleccionado': pais,
        'region_seleccionada': region,
        'comuna_seleccionada': comuna,
        'cobertura_seleccionada': cobertura,
        'busqueda': busqueda,
    }

    return render(request, 'proveedores/directorio.html', context)


def detalle_proveedor(request, proveedor_id):
    """Vista del perfil público del proveedor"""
    proveedor = get_object_or_404(
        Proveedor.objects.prefetch_related('categorias'),
        id=proveedor_id,
        activo=True
    )

    # Incrementar visitas
    try:
        proveedor.incrementar_visitas()
    except Exception:
        pass

    # Productos y servicios del proveedor
    productos = ProductoServicio.objects.filter(
        proveedor=proveedor,
        activo=True
    ).order_by('-destacado', '-fecha_creacion')

    # Promociones vigentes
    hoy = timezone.now().date()
    promociones = Promocion.objects.filter(
        proveedor=proveedor,
        activo=True,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    ).order_by('-fecha_inicio')

    context = {
        'proveedor': proveedor,
        'productos': productos,
        'promociones': promociones,
    }

    return render(request, 'proveedores/detalle.html', context)


# ==================== PANEL DEL PROVEEDOR ====================

@proveedor_login_required
def dashboard_proveedor(request):
    """Dashboard del proveedor"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    # Estadísticas
    total_productos = ProductoServicio.objects.filter(proveedor=proveedor).count()
    productos_activos = ProductoServicio.objects.filter(proveedor=proveedor, activo=True).count()

    hoy = timezone.now().date()
    promociones_activas = Promocion.objects.filter(
        proveedor=proveedor,
        activo=True,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    ).count()

    solicitudes_pendientes = SolicitudContacto.objects.filter(
        proveedor=proveedor,
        estado='pendiente'
    ).count()

    # Productos recientes
    productos_recientes = ProductoServicio.objects.filter(
        proveedor=proveedor
    ).order_by('-fecha_creacion')[:5]

    # Promociones próximas a vencer
    promociones_proximas = Promocion.objects.filter(
        proveedor=proveedor,
        activo=True,
        fecha_fin__gte=hoy
    ).order_by('fecha_fin')[:5]

    context = {
        'proveedor': proveedor,
        'total_productos': total_productos,
        'productos_activos': productos_activos,
        'promociones_activas': promociones_activas,
        'solicitudes_pendientes': solicitudes_pendientes,
        'productos_recientes': productos_recientes,
        'promociones_proximas': promociones_proximas,
    }
    return render(request, 'proveedores/dashboard.html', context)


@proveedor_login_required
def editar_perfil_proveedor(request):
    """Editar perfil del proveedor"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    if request.method == 'POST':
        form = ProveedorForm(request.POST, request.FILES, instance=proveedor)
        if form.is_valid():
            try:
                # Guardar el formulario
                proveedor_actualizado = form.save()
                
                # CRÍTICO: Refrescar desde la base de datos para obtener todos los campos actualizados
                proveedor_actualizado.refresh_from_db()
                
                # CRÍTICO: Actualizar la variable global con los datos frescos
                current_logged_in_proveedor = proveedor_actualizado
                
                messages.success(request, "Perfil actualizado exitosamente.")
                return redirect('proveedores:editar_perfil_proveedor')  # Redirige a la misma página para ver los cambios
            except Exception as e:
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = ProveedorForm(instance=proveedor)

    context = {'form': form, 'proveedor': proveedor}
    return render(request, 'proveedores/editar_perfil.html', context)


# ==================== GESTIÓN DE PRODUCTOS ====================

@proveedor_login_required
def lista_productos(request):
    """Lista de productos del proveedor"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    productos = ProductoServicio.objects.filter(proveedor=proveedor)

    # Filtros
    categoria = request.GET.get('categoria', '')
    if categoria:
        productos = productos.filter(categoria=categoria)

    estado = request.GET.get('estado', '')
    if estado == 'activo':
        productos = productos.filter(activo=True)
    elif estado == 'inactivo':
        productos = productos.filter(activo=False)

    buscar = request.GET.get('buscar', '')
    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    productos = productos.order_by('-destacado', '-fecha_creacion')

    # Paginación
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'proveedor': proveedor,
        'page_obj': page_obj,
        'categoria_actual': categoria,
        'estado_actual': estado,
        'buscar_actual': buscar,
        'opciones_categoria': ProductoServicio.CATEGORIA_CHOICES,
    }

    return render(request, 'proveedores/productos/lista.html', context)


@proveedor_login_required
def crear_producto(request):
    """Crear nuevo producto/servicio"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    if request.method == 'POST':
        form = ProductoServicioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                producto = form.save(commit=False)
                producto.proveedor = proveedor
                producto.save()
                messages.success(request, 'Producto/servicio creado exitosamente.')
                return redirect('proveedores:lista_productos')
            except Exception as e:
                messages.error(request, f"Error al crear producto: {e}")
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = ProductoServicioForm()

    context = {'form': form, 'proveedor': proveedor}
    return render(request, 'proveedores/productos/crear.html', context)


@proveedor_login_required
def editar_producto(request, producto_id):
    """Editar producto/servicio"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    producto = get_object_or_404(ProductoServicio, id=producto_id, proveedor=proveedor)

    if request.method == 'POST':
        form = ProductoServicioForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Producto actualizado exitosamente.')
                return redirect('proveedores:lista_productos')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = ProductoServicioForm(instance=producto)

    context = {'form': form, 'producto': producto, 'proveedor': proveedor}
    return render(request, 'proveedores/productos/editar.html', context)


@proveedor_login_required
@require_POST
def eliminar_producto(request, producto_id):
    """Eliminar producto/servicio"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        return redirect('proveedores:login_proveedor')

    producto = get_object_or_404(ProductoServicio, id=producto_id, proveedor=proveedor)

    try:
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar: {e}')

    return redirect('proveedores:lista_productos')

# ==================== GESTIÓN DE PROMOCIONES ====================

@proveedor_login_required
def lista_promociones(request):
    """Lista de promociones del proveedor"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    promociones = Promocion.objects.filter(proveedor=proveedor).order_by('-fecha_inicio')

    # Filtros
    estado_filter = request.GET.get('estado', '')
    hoy = timezone.now().date()
    
    if estado_filter == 'activas':
        promociones = promociones.filter(
            activo=True,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        )
    elif estado_filter == 'proximas':
        promociones = promociones.filter(fecha_inicio__gt=hoy)
    elif estado_filter == 'vencidas':
        promociones = promociones.filter(fecha_fin__lt=hoy)

    # Paginación
    paginator = Paginator(promociones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'proveedor': proveedor,
        'estado_filter': estado_filter,
        'hoy': hoy,
    }
    return render(request, 'proveedores/promociones/lista.html', context)


@proveedor_login_required
def crear_promocion(request):
    """Crear nueva promoción"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                promocion = form.save(commit=False)
                promocion.proveedor = proveedor
                promocion.save()
                messages.success(request, 'Promoción creada exitosamente.')
                return redirect('proveedores:lista_promociones')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = PromocionForm()

    context = {'form': form, 'proveedor': proveedor}
    return render(request, 'proveedores/promociones/crear.html', context)


@proveedor_login_required
def editar_promocion(request, promocion_id):
    """Editar promoción"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    promocion = get_object_or_404(Promocion, id=promocion_id, proveedor=proveedor)

    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES, instance=promocion)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Promoción actualizada exitosamente.')
                return redirect('proveedores:lista_promociones')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = PromocionForm(instance=promocion)

    context = {'form': form, 'promocion': promocion, 'proveedor': proveedor}
    return render(request, 'proveedores/promociones/editar.html', context)


@proveedor_login_required
@require_POST
def eliminar_promocion(request, promocion_id):
    """Eliminar promoción"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        return redirect('proveedores:login_proveedor')

    promocion = get_object_or_404(Promocion, id=promocion_id, proveedor=proveedor)

    try:
        titulo = promocion.titulo
        promocion.delete()
        messages.success(request, f'Promoción "{titulo}" eliminada exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar: {e}')

    return redirect('proveedores:lista_promociones')


# ==================== SOLICITUDES DE CONTACTO ====================

@proveedor_login_required
def enviar_solicitud_contacto(request, comercio_id=None):
    """Enviar solicitud de contacto a un comercio"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    if request.method == 'POST':
        form = SolicitudContactoForm(request.POST)
        if form.is_valid():
            try:
                solicitud = form.save(commit=False)
                solicitud.proveedor = proveedor
                solicitud.save()
                
                proveedor.contactos_enviados += 1
                proveedor.save(update_fields=['contactos_enviados'])
                
                messages.success(request, 'Solicitud enviada exitosamente.')
                return redirect('proveedores:mis_solicitudes')
            except Exception as e:
                messages.error(request, f'Error al enviar solicitud: {e}')
        else:
            messages.error(request, "Hay errores en el formulario.")
    else:
        form = SolicitudContactoForm()

    context = {
        'form': form,
        'proveedor': proveedor,
        'comercio_id': comercio_id,
    }
    return render(request, 'proveedores/solicitudes/enviar.html', context)


@proveedor_login_required
def mis_solicitudes(request):
    """Lista de solicitudes del proveedor"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        messages.error(request, "Debes iniciar sesión como proveedor.")
        return redirect('proveedores:login_proveedor')

    solicitudes = SolicitudContacto.objects.filter(
        proveedor=proveedor
    ).order_by('-fecha_solicitud')

    # Filtro por estado
    estado_filter = request.GET.get('estado', '')
    if estado_filter:
        solicitudes = solicitudes.filter(estado=estado_filter)

    # Paginación
    paginator = Paginator(solicitudes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'proveedor': proveedor,
        'estado_filter': estado_filter,
        'estados': SolicitudContacto.ESTADO_CHOICES,
    }
    return render(request, 'proveedores/solicitudes/mis_solicitudes.html', context)


@proveedor_login_required
@require_POST
def cancelar_solicitud(request, solicitud_id):
    """Cancelar una solicitud de contacto"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        return redirect('proveedores:login_proveedor')

    solicitud = get_object_or_404(SolicitudContacto, id=solicitud_id, proveedor=proveedor)

    try:
        if solicitud.estado == 'pendiente':
            solicitud.estado = 'cancelada'
            solicitud.save(update_fields=['estado'])
            messages.success(request, 'Solicitud cancelada exitosamente.')
        else:
            messages.warning(request, 'Solo se pueden cancelar solicitudes pendientes.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    return redirect('proveedores:mis_solicitudes')


# ==================== AJAX ====================

@proveedor_login_required
@require_POST
def toggle_destacado_producto(request, producto_id):
    """Activar/desactivar producto destacado (AJAX)"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=403)

    producto = get_object_or_404(ProductoServicio, id=producto_id, proveedor=proveedor)

    try:
        producto.destacado = not producto.destacado
        producto.save(update_fields=['destacado'])
        return JsonResponse({
            'success': True,
            'destacado': producto.destacado,
            'message': 'Producto destacado' if producto.destacado else 'Destacado removido'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_regiones_ajax(request):
    """Vista AJAX para obtener regiones de un país"""
    pais_code = request.GET.get('pais_id')
    
    if pais_code and pais_code in REGIONES_POR_PAIS:
        regiones = [
            {'id': codigo, 'nombre': nombre}
            for codigo, nombre in REGIONES_POR_PAIS[pais_code]
        ]
        return JsonResponse({'regiones': regiones})
    
    return JsonResponse({'regiones': []})


def get_comunas_ajax(request):
    """Vista AJAX para obtener comunas de una región"""
    region_code = request.GET.get('region_id')
    
    if region_code and region_code in COMUNAS_POR_REGION:
        comunas = [
            {'id': codigo, 'nombre': nombre}
            for codigo, nombre in COMUNAS_POR_REGION[region_code]
        ]
        return JsonResponse({'comunas': comunas})
    
    return JsonResponse({'comunas': []})



@proveedor_login_required
@require_POST
def cambiar_estado_producto(request, producto_id):
    """Cambiar estado activo/inactivo de un producto (AJAX)"""
    global current_logged_in_proveedor
    proveedor = current_logged_in_proveedor
    
    if not proveedor:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=403)

    producto = get_object_or_404(ProductoServicio, id=producto_id, proveedor=proveedor)

    try:
        producto.activo = not producto.activo
        producto.save(update_fields=['activo'])
        return JsonResponse({
            'success': True,
            'activo': producto.activo,
            'message': 'Producto activado' if producto.activo else 'Producto desactivado'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)