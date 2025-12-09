# administrador/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from usuarios.models import Comerciante, Beneficio, Post, Aviso
from usuarios import views as usuarios_views # Se mantiene para acceder al usuario logueado
from usuarios.views import ADMIN_CATEGORIES # Importación de constante

from .forms import (
    ComercianteAdminForm,
    BeneficioAdminForm,
    PostAdminForm,
    AvisoForm
)

#-------------------------------------------Verificar si es admin
def require_admin():
    """Verifica si el usuario logueado actual tiene rol 'ADMIN'."""
    user = usuarios_views.current_logged_in_user
    if not user:
        return False
    return user.rol == 'ADMIN'


# ========= COMERCIANTES =========
def panel_admin_view(request):#--------------Muestra todos los comenrciantes en una tabla
    if not require_admin():
        return redirect('login')

    admin_user = usuarios_views.current_logged_in_user
    comerciantes = Comerciante.objects.all().order_by('-fecha_registro')

    return render(request, 'administrador/panel_admin.html', {
        'comerciantes': comerciantes,
        'admin': admin_user,
    })


def crear_comerciante_view(request):#--------------Crear comerciante
    if not require_admin():
        return redirect('login')

    if request.method == 'POST':
        form = ComercianteAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Comerciante creado correctamente.")
            return redirect('panel_admin')
    else:
        form = ComercianteAdminForm()

    return render(request, "administrador/crear_comerciante.html", {
        "form": form
    })


def editar_comerciante_view(request, comerciante_id):#--------------Editar comerciante
    if not require_admin():
        return redirect('login')

    comerciante = get_object_or_404(Comerciante, id=comerciante_id)

    if request.method == 'POST':
        form = ComercianteAdminForm(request.POST, instance=comerciante)
        if form.is_valid():
            form.save()
            messages.success(request, "Comerciante actualizado correctamente.")
            return redirect('panel_admin')
    else:
        form = ComercianteAdminForm(instance=comerciante)

    return render(request, "administrador/editar_comerciante.html", {
        "form": form,
        "comerciante": comerciante,
    })


def eliminar_comerciante_view(request, comerciante_id): #--------------Eliminar comerciante
    if not require_admin():
        return redirect('login')

    comerciante = get_object_or_404(Comerciante, id=comerciante_id)

    if request.method == 'POST':
        comerciante.delete()
        messages.success(request, "Comerciante eliminado correctamente.")
        return redirect('panel_admin')

    return render(request, "administrador/confirmar_eliminar.html", {
        "comerciante": comerciante
    })


# ========= POSTS (usuarios.Post) =========

def admin_posts_list(request):#--------------Lista de posts
    if not require_admin():
        return redirect('login')

    admin_user = usuarios_views.current_logged_in_user
    posts = Post.objects.select_related('comerciante').order_by('-fecha_publicacion')

    return render(request, 'administrador/posts_list.html', {
        'posts': posts,
        'admin': admin_user,
    })


def crear_post_admin_view(request):#--------------Crear post
    if not require_admin():
        return redirect('login')

    # Obtener las opciones de categoría solo para Admin
    admin_choices = ADMIN_CATEGORIES

    if request.method == 'POST':
        # Pasar las opciones filtradas al inicializar el formulario
        form = PostAdminForm(request.POST, admin_category_choices=admin_choices) 
        if form.is_valid():
            # ASIGNACIÓN CLAVE: Asignar el administrador como autor
            nuevo_post = form.save(commit=False)
            nuevo_post.comerciante = usuarios_views.current_logged_in_user # Asigna el admin logueado
            nuevo_post.save()
            messages.success(request, "Post creado correctamente.")
            return redirect('admin_posts')
    else:
        # Pasar las opciones filtradas al inicializar el formulario
        form = PostAdminForm(admin_category_choices=admin_choices)

    return render(request, 'administrador/post_form.html', {
        'form': form,
    })


def editar_post_admin_view(request, post_id):#  ------------Editar post
    if not require_admin():
        return redirect('login')

    post = get_object_or_404(Post, id=post_id)
    
    # Obtener las opciones de categoría solo para Admin
    admin_choices = ADMIN_CATEGORIES

    if request.method == 'POST':
        # Pasar las opciones filtradas al inicializar el formulario
        form = PostAdminForm(request.POST, instance=post, admin_category_choices=admin_choices) 
        if form.is_valid():
            # El autor (comerciante) no se toca en la edición, se mantiene el asignado.
            form.save() 
            messages.success(request, "Post actualizado correctamente.")
            return redirect('admin_posts')
    else:
        # Pasar las opciones filtradas al inicializar el formulario
        form = PostAdminForm(instance=post, admin_category_choices=admin_choices) 

    return render(request, 'administrador/post_form.html', {
        'form': form,
        'post': post,
    })


def eliminar_post_admin_view(request, post_id):#--------------Eliminar post
    if not require_admin():
        return redirect('login')

    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post eliminado correctamente.")
        return redirect('admin_posts')

    return render(request, 'administrador/post_confirmar_eliminar.html', {
        'post': post
    })


# ========= BENEFICIOS (usuarios.Beneficio) =========

def admin_beneficios_list(request):#--------------Lista de beneficios
    if not require_admin():
        return redirect('login')

    admin_user = usuarios_views.current_logged_in_user
    beneficios = Beneficio.objects.all().order_by('-fecha_creacion')

    return render(request, 'administrador/beneficios_list.html', {
        'beneficios': beneficios,
        'admin': admin_user,
    })


def crear_beneficio_view(request):#--------------Crear beneficio
    if not require_admin():
        return redirect('login')

    if request.method == 'POST':
        form = BeneficioAdminForm(request.POST, request.FILES)
        if form.is_valid():
            beneficio = form.save(commit=False)
            beneficio.save()
            messages.success(request, "Beneficio creado correctamente.")
            return redirect('admin_beneficios')
    else:
        form = BeneficioAdminForm()

    return render(request, 'administrador/beneficio_form.html', {
        'form': form,
    })


def editar_beneficio_view(request, beneficio_id):#--------------Editar beneficio
    if not require_admin():
        return redirect('login')

    beneficio = get_object_or_404(Beneficio, id=beneficio_id)

    if request.method == 'POST':
        form = BeneficioAdminForm(request.POST, request.FILES, instance=beneficio)
        if form.is_valid():
            form.save()
            messages.success(request, "Beneficio actualizado correctamente.")
            return redirect('admin_beneficios')
    else:
        form = BeneficioAdminForm(instance=beneficio)

    return render(request, 'administrador/beneficio_form.html', {
        'form': form,
        'beneficio': beneficio,
    })


def eliminar_beneficio_view(request, beneficio_id):#--------------Eliminar beneficio
    if not require_admin():
        return redirect('login')

    beneficio = get_object_or_404(Beneficio, id=beneficio_id)

    if request.method == 'POST':
        beneficio.delete()
        messages.success(request, "Beneficio eliminado correctamente.")
        return redirect('admin_beneficios')

    return render(request, 'administrador/beneficio_confirmar_eliminar.html', {
        'beneficio': beneficio
    })


# ========= AVISOS DE ADMINISTRACIÓN =========

def avisos_list_view(request):
    """Muestra la lista de todos los Avisos, ordenados por fecha de creación."""
    if not require_admin():
        return redirect('login')
        
    avisos = Aviso.objects.all().order_by('-fecha_creacion')
    context = {
        'avisos': avisos,
        'title': 'Gestión de Avisos'
    }
    return render(request, 'administrador/aviso_list.html', context)


def aviso_create_view(request):
    """Permite al administrador crear un nuevo Aviso."""
    if not require_admin():
        return redirect('login')

    if request.method == 'POST':
        form = AvisoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Aviso creado y listo para los comerciantes!')
            return redirect('avisos_list')
        else:
            messages.error(request, 'Error al crear el aviso. Por favor, revisa el formulario.')
    else:
        form = AvisoForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Aviso',
        'is_new': True,
    }
    return render(request, 'administrador/aviso_form.html', context)


def aviso_update_view(request, pk):
    """Permite al administrador editar un Aviso existente."""
    if not require_admin():
        return redirect('login')
        
    aviso = get_object_or_404(Aviso, pk=pk)
    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aviso actualizado con éxito.')
            return redirect('avisos_list')
        else:
            messages.error(request, 'Error al actualizar el aviso.')
    else:
        form = AvisoForm(instance=aviso)
        
    context = {
        'form': form,
        'aviso': aviso,
        'title': f'Editar Aviso: {aviso.titulo}',
        'is_new': False,
    }
    return render(request, 'administrador/aviso_form.html', context)


def aviso_delete_view(request, pk):
    """Permite al administrador confirmar y eliminar un Aviso."""
    if not require_admin():
        return redirect('login')
        
    aviso = get_object_or_404(Aviso, pk=pk)
    
    if request.method == 'POST':
        aviso.delete()
        messages.success(request, f'Aviso "{aviso.titulo}" eliminado permanentemente.')
        return redirect('avisos_list')
        
    context = {
        'aviso': aviso,
        'title': 'Confirmar Eliminación de Aviso'
    }
    return render(request, 'administrador/aviso_confirmar_eliminar.html', context)