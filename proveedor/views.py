# proveedores/views.py (CÓDIGO REVISADO, COMPLETO Y FINAL CON MANEJO DE ERRORES)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST, require_GET

from usuarios import views as usuarios_views   # si defines current_logged_in_user aquí
from usuarios.models import Comerciante

from .models import (
    Proveedor,
    SolicitudContacto,
    ProductoServicio,
    Promocion,
    CategoriaProveedor,
    Pais,
    Region,
    Comuna
)
from .forms import (
    ProveedorForm,
    ProductoServicioForm,
    PromocionForm,
    SolicitudContactoForm,
    ConfiguracionForm
)


# -----------------------
# Helpers
# -----------------------
def _get_comerciante_from_request(request):
    """
    Intentar obtener el Comerciante en el siguiente orden:
    1) usuarios_views.current_logged_in_user (si existe y no es None)
    2) request.user.comerciante (atributo relacional común)
    3) buscar en la tabla Comerciante por email del usuario (fallback no intrusivo)
    Devuelve None si no se encuentra.
    """
    # 1) preferimos el helper externo si lo provees
    try:
        if hasattr(usuarios_views, "current_logged_in_user") and usuarios_views.current_logged_in_user:
            return usuarios_views.current_logged_in_user
    except Exception:
        # no queremos que un fallo en usuarios_views rompa todo
        pass

    # 2) intentar atributo directo en user
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        # intento habitual: request.user.comerciante
        comerciante = getattr(user, "comerciante", None)
        if comerciante:
            return comerciante

        # fallback: intentar buscar por email (solo si existe email)
        email = getattr(user, "email", None)
        if email:
            try:
                return Comerciante.objects.filter(email__iexact=email).first()
            except Exception:
                pass

    return None


def _get_proveedor_for_user(request):
    """
    Intenta devolver el Proveedor relacionado con el usuario/comerciante.
    Maneja exceptions y devuelve (proveedor, error_msg) donde error_msg es None si todo ok.
    """
    comerciante = _get_comerciante_from_request(request)
    if not comerciante:
        return None, "Debes iniciar sesión como comerciante."

    try:
        proveedor = Proveedor.objects.get(usuario=comerciante)
        return proveedor, None
    except Proveedor.DoesNotExist:
        return None, "Debes crear primero un perfil de proveedor."


# ==================== VISTAS PÚBLICAS ====================

def directorio_proveedores(request):
    """
    Vista del directorio público de proveedores con filtros
    """
    proveedores = Proveedor.objects.filter(activo=True).select_related(
        'pais', 'region', 'comuna'
    ).prefetch_related('categorias')

    # Filtros desde GET
    categoria_id = request.GET.get('categoria')
    region_id = request.GET.get('region')
    comuna_id = request.GET.get('comuna')
    cobertura = request.GET.get('cobertura')
    busqueda = request.GET.get('q')

    if categoria_id:
        proveedores = proveedores.filter(categorias__id=categoria_id)

    if region_id:
        proveedores = proveedores.filter(region_id=region_id)

    if comuna_id:
        proveedores = proveedores.filter(comuna_id=comuna_id)

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
    regiones = Region.objects.all()

    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'regiones': regiones,
        'categoria_seleccionada': categoria_id,
        'region_seleccionada': region_id,
        'comuna_seleccionada': comuna_id,
        'cobertura_seleccionada': cobertura,
        'busqueda': busqueda,
    }

    return render(request, 'proveedores/directorio.html', context)


def detalle_proveedor(request, proveedor_id):
    """
    Vista del perfil público del proveedor
    """
    proveedor = get_object_or_404(
        Proveedor.objects.select_related('pais', 'region', 'comuna').prefetch_related('categorias'),
        id=proveedor_id,
        activo=True
    )

    # Incrementar visitas: envolver en try/except por si el método falla
    try:
        if hasattr(proveedor, "incrementar_visitas"):
            proveedor.incrementar_visitas()
    except Exception:
        # no interrumpir la vista por fallo en contador
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


# ==================== VISTAS DEL PERFIL DEL PROVEEDOR ====================

@login_required
def perfil_proveedor(request):
    """
    Panel de control del proveedor.
    Usa el Comerciante obtenido por helper para evitar inconsistencias.
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    # Estadísticas
    total_productos = ProductoServicio.objects.filter(proveedor=proveedor).count()

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

    context = {
        'proveedor': proveedor,
        'total_productos': total_productos,
        'promociones_activas': promociones_activas,
        'solicitudes_pendientes': solicitudes_pendientes,
    }
    return render(request, 'proveedores/perfil.html', context)


@login_required
def crear_perfil_proveedor(request):
    """
    Crear perfil de proveedor ligado al Comerciante
    """
    comerciante = _get_comerciante_from_request(request)
    if not comerciante:
        messages.error(request, "Debes iniciar sesión como comerciante.")
        return redirect('login')

    # Evitar duplicar perfil
    if Proveedor.objects.filter(usuario=comerciante).exists():
        messages.info(request, "Ya tienes un perfil de proveedor.")
        return redirect('proveedores:perfil_proveedor')

    if request.method == 'POST':
        form = ProveedorForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    proveedor = form.save(commit=False)
                    proveedor.usuario = comerciante
                    # Si el formulario no trae email, tomar el del comerciante
                    proveedor.email = proveedor.email or getattr(comerciante, 'email', '')
                    proveedor.whatsapp = proveedor.whatsapp or getattr(comerciante, 'whatsapp', '') or ""
                    proveedor.save()
                    form.save_m2m()

                    # Marcar campo es_proveedor si existe en Comerciante
                    if hasattr(comerciante, "es_proveedor"):
                        comerciante.es_proveedor = True
                        comerciante.save(update_fields=["es_proveedor"])

                    messages.success(
                        request,
                        "¡Perfil de proveedor creado exitosamente! Ahora puedes gestionar tu negocio."
                    )
                    return redirect('proveedores:perfil_proveedor')
            except Exception as e:
                messages.error(request, f"Error al crear perfil: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        # Precargar algunos datos desde Comerciante (si existen)
        initial = {
            "nombre_empresa": getattr(comerciante, "nombre_negocio", None) or getattr(comerciante, "nombre_apellido", None) or getattr(comerciante, "nombre", ""),
            "whatsapp": getattr(comerciante, "whatsapp", "") or "",
            "email": getattr(comerciante, "email", "") or ""
        }
        form = ProveedorForm(initial=initial)

    return render(request, 'proveedores/crear_perfil.html', {'form': form})


@login_required
def editar_perfil_proveedor(request):
    """
    Editar perfil del proveedor
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    if request.method == 'POST':
        form = ProveedorForm(request.POST, request.FILES, instance=proveedor)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Perfil actualizado exitosamente.")
                return redirect('proveedores:perfil_proveedor')
            except Exception as e:
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = ProveedorForm(instance=proveedor)

    context = {'form': form, 'proveedor': proveedor}
    return render(request, 'proveedores/editar_perfil.html', context)


# ==================== GESTIÓN DE PRODUCTOS/SERVICIOS ====================

@login_required
def lista_productos(request):
    """
    Lista de productos del proveedor con filtros funcionales
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    productos = ProductoServicio.objects.filter(proveedor=proveedor)

    categoria_choices = getattr(ProductoServicio, 'CATEGORIA_CHOICES', [])

    # Filtros
    categoria_actual = request.GET.get('categoria', '')
    if categoria_actual:
        productos = productos.filter(categoria=categoria_actual)

    estado_actual = request.GET.get('estado', '')
    if estado_actual == 'activo':
        productos = productos.filter(activo=True)
    elif estado_actual == 'inactivo':
        productos = productos.filter(activo=False)

    buscar_actual = request.GET.get('buscar', '')
    if buscar_actual:
        productos = productos.filter(
            Q(nombre__icontains=buscar_actual) |
            Q(descripcion__icontains=buscar_actual)
        )

    productos = productos.order_by('-id')

    context = {
        'proveedor': proveedor,
        'productos': productos,
        'categoria_actual': categoria_actual,
        'estado_actual': estado_actual,
        'buscar_actual': buscar_actual,
        'opciones_categoria': categoria_choices,
    }

    return render(request, 'proveedores/productos/lista.html', context)


@login_required
def crear_producto(request):
    """
    Crear nuevo producto/servicio
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    if request.method == 'POST':
        form = ProductoServicioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                producto = form.save(commit=False)
                producto.proveedor = proveedor
                producto.save()
                messages.success(request, '✅ Producto/servicio creado exitosamente.')
                return redirect('proveedores:lista_productos')
            except Exception as e:
                messages.error(request, f"Error al crear producto: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = ProductoServicioForm()

    context = {
        'form': form,
        'proveedor': proveedor
    }
    return render(request, 'proveedores/productos/crear.html', context)


@login_required
def editar_producto(request, producto_id):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    producto = get_object_or_404(
        ProductoServicio,
        id=producto_id,
        proveedor=proveedor
    )

    if request.method == 'POST':
        form = ProductoServicioForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Producto/servicio actualizado exitosamente.')
                return redirect('proveedores:lista_productos')
            except Exception as e:
                messages.error(request, f"Error al actualizar: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = ProductoServicioForm(instance=producto)

    context = {'form': form, 'producto': producto}
    return render(request, 'proveedores/productos/editar.html', context)


@login_required
@require_POST
def eliminar_producto(request, producto_id):
    """
    Solo POST: elimina permanentemente un producto
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        return redirect('proveedores:crear_perfil_proveedor')

    producto = get_object_or_404(
        ProductoServicio,
        id=producto_id,
        proveedor=proveedor
    )

    nombre_producto = producto.nombre
    try:
        producto.delete()
        messages.success(request, f'✅ Producto "{nombre_producto}" eliminado permanentemente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar producto: {e}')

    return redirect('proveedores:lista_productos')


# ==================== GESTIÓN DE PROMOCIONES ====================

@login_required
def lista_promociones(request):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    promociones = Promocion.objects.filter(proveedor=proveedor)

    estado = request.GET.get('estado', '')
    if estado == 'activas':
        promociones = promociones.filter(activo=True)
    elif estado == 'inactivas':
        promociones = promociones.filter(activo=False)

    vigencia = request.GET.get('vigencia', '')
    hoy = timezone.now().date()

    if vigencia == 'vigentes':
        promociones = promociones.filter(
            activo=True,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        )
    elif vigencia == 'programadas':
        promociones = promociones.filter(
            activo=True,
            fecha_inicio__gt=hoy
        )
    elif vigencia == 'vencidas':
        promociones = promociones.filter(fecha_fin__lt=hoy)

    buscar = request.GET.get('buscar', '')
    if buscar:
        promociones = promociones.filter(
            Q(titulo__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if fecha_desde:
        promociones = promociones.filter(fecha_inicio__gte=fecha_desde)

    if fecha_hasta:
        promociones = promociones.filter(fecha_fin__lte=fecha_hasta)

    promociones = promociones.order_by('-fecha_inicio')

    context = {
        'promociones': promociones,
        'proveedor': proveedor,
        'estado_actual': estado,
        'vigencia_actual': vigencia,
        'buscar_actual': buscar,
        'fecha_desde_actual': fecha_desde,
        'fecha_hasta_actual': fecha_hasta,
    }

    return render(request, 'proveedores/promociones/lista.html', context)


@login_required
def crear_promocion(request):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

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
                messages.error(request, f"Error al crear promoción: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = PromocionForm()

    context = {'form': form}
    return render(request, 'proveedores/promociones/crear.html', context)


@login_required
def editar_promocion(request, promocion_id):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    promocion = get_object_or_404(
        Promocion,
        id=promocion_id,
        proveedor=proveedor
    )

    if request.method == 'POST':
        form = PromocionForm(request.POST, request.FILES, instance=promocion)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Promoción actualizada exitosamente.')
                return redirect('proveedores:lista_promociones')
            except Exception as e:
                messages.error(request, f"Error al actualizar promoción: {e}")
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = PromocionForm(instance=promocion)

    context = {'form': form, 'promocion': promocion}
    return render(request, 'proveedores/promociones/editar.html', context)


@login_required
@require_POST
def eliminar_promocion(request, promocion_id):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        return redirect('proveedores:crear_perfil_proveedor')

    promocion = get_object_or_404(
        Promocion,
        id=promocion_id,
        proveedor=proveedor
    )

    titulo_promocion = promocion.titulo
    try:
        promocion.delete()
        messages.success(request, f'✅ Promoción "{titulo_promocion}" eliminada permanentemente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar promoción: {e}')

    return redirect('proveedores:lista_promociones')


# ==================== SOLICITUDES DE CONTACTO ====================

@login_required
def enviar_solicitud_contacto(request, comercio_id=None):
    """
    Enviar solicitud de contacto a un comercio.
    comercio_id es opcional en caso de que aún no tengas el modelo Comercio.
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    if request.method == 'POST':
        form = SolicitudContactoForm(request.POST)
        if form.is_valid():
            try:
                solicitud = form.save(commit=False)
                solicitud.proveedor = proveedor
                # si tienes comercio, asignarlo aquí: solicitud.comercio = comercio
                solicitud.save()
                proveedor.contactos_enviados = getattr(proveedor, 'contactos_enviados', 0) + 1
                proveedor.save(update_fields=['contactos_enviados'])
                messages.success(request, 'Solicitud de contacto enviada exitosamente.')
                return redirect('proveedores:mis_solicitudes')
            except Exception as e:
                messages.error(request, f'Error al enviar solicitud: {e}')
        else:
            messages.error(request, "Hay errores en el formulario. Revisa los campos.")
    else:
        form = SolicitudContactoForm()

    context = {
        'form': form,
        'proveedor': proveedor
    }
    return render(request, 'proveedores/solicitudes/enviar.html', context)


@login_required
def mis_solicitudes(request):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    solicitudes = SolicitudContacto.objects.filter(
        proveedor=proveedor
    ).order_by('-fecha_solicitud')

    estado = request.GET.get('estado')
    if estado:
        solicitudes = solicitudes.filter(estado=estado)

    context = {
        'solicitudes': solicitudes,
        'estado_seleccionado': estado
    }
    return render(request, 'proveedores/solicitudes/mis_solicitudes.html', context)


# ==================== VISTAS AJAX ====================

@require_GET
def get_comunas_ajax(request):
    """
    Obtener comunas de una región (para filtros dinámicos).
    No requiere login si lo quieres público; si lo quieres privado, añade @login_required.
    """
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse({'error': 'region_id requerido'}, status=400)

    try:
        comunas = Comuna.objects.filter(region_id=region_id).values('id', 'nombre')
        return JsonResponse(list(comunas), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_destacado_producto(request, producto_id):
    """
    Activar/desactivar producto destacado (POST únicamente).
    Devuelve JSON con resultado.
    """
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        return JsonResponse({'success': False, 'error': err}, status=403)

    producto = get_object_or_404(
        ProductoServicio,
        id=producto_id,
        proveedor=proveedor
    )

    try:
        producto.destacado = not bool(producto.destacado)
        producto.save(update_fields=['destacado'])
        return JsonResponse({
            'success': True,
            'destacado': producto.destacado
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== CONFIGURACIÓN ====================

@login_required
def configuracion_proveedor(request):
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    if request.method == 'POST':
        form = ConfiguracionForm(request.POST, request.FILES, instance=proveedor)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '✓ Configuración guardada correctamente.')
                return redirect('proveedores:perfil_proveedor')
            except Exception as e:
                messages.error(request, f'Error al guardar la configuración: {e}')
        else:
            messages.error(request, '❌ Error al guardar la configuración. Revisa los campos.')
    else:
        form = ConfiguracionForm(instance=proveedor)

    context = {
        'form': form,
        'proveedor': proveedor,
        'user': request.user
    }
    return render(request, 'proveedores/configuracion.html', context)


@login_required
@require_POST
def eliminar_foto_perfil(request):
    """Eliminar foto de perfil del proveedor (POST)."""
    proveedor, err = _get_proveedor_for_user(request)
    if err:
        messages.error(request, err)
        return redirect('proveedores:crear_perfil_proveedor')

    try:
        if proveedor.foto_perfil:
            # delete() del FileField/BLOB; save=True/False depende de tu versión, usar solo delete() es más seguro
            proveedor.foto_perfil.delete(save=False)
            # Si quieres limpiar el campo en el modelo:
            proveedor.foto_perfil = None
            proveedor.save(update_fields=['foto_perfil'])
            messages.success(request, '✓ Foto de perfil eliminada.')
        else:
            messages.info(request, 'No tienes foto de perfil.')
    except Exception as e:
        messages.error(request, f'Error al eliminar la foto: {e}')

    return redirect('proveedores:configuracion')
