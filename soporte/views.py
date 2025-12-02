# soporte/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from usuarios import views as usuarios_views
from .models import TicketSoporte   # ✅ solo este import, sin repetir


def require_tecnico():
    """
    Verifica que el usuario actual (current_logged_in_user)
    tenga rol TECNICO.
    """
    user = usuarios_views.current_logged_in_user
    return user and user.rol == 'TECNICO'


# ========== PANEL PRINCIPAL DE SOPORTE ==========

def panel_soporte(request):
    if not require_tecnico():
        return redirect('login')

    tecnico = usuarios_views.current_logged_in_user
    tickets = TicketSoporte.objects.all()  # ← modelo correcto

    return render(request, 'soporte/panel.html', {
        'tecnico': tecnico,
        'tickets': tickets,
    })


# ========== DETALLE DE TICKET ==========

def ticket_detalle(request, ticket_id):
    """
    Muestra el detalle de un ticket y permite cambiar su estado.
    (sin modelo de respuestas, solo actualiza estado y técnico asignado)
    """
    if not require_tecnico():
        return redirect('login')

    tecnico = usuarios_views.current_logged_in_user
    ticket = get_object_or_404(TicketSoporte, id=ticket_id)

    if request.method == 'POST':
        # Esperamos un input oculto llamado "accion" desde el template
        accion = request.POST.get('accion')

        # 👇 OJO: aquí usamos los valores EXACTOS del modelo
        if accion == 'tomar':
            ticket.estado = 'EN_PROCESO'
            ticket.tecnico_asignado = tecnico
            messages.success(request, "Has tomado el ticket. Estado: EN PROCESO.")
        elif accion == 'resolver':
            ticket.estado = 'RESUELTO'
            ticket.tecnico_asignado = tecnico
            messages.success(request, "Ticket marcado como RESUELTO.")
        elif accion == 'cerrar':
            ticket.estado = 'CERRADO'
            ticket.tecnico_asignado = tecnico
            messages.success(request, "Ticket CERRADO.")
        else:
            messages.error(request, "Acción no reconocida.")

        ticket.save()
        # 🔹 Usa el nombre con namespace
        return redirect('soporte:ticket_detalle', ticket_id=ticket.id)

    return render(request, 'soporte/ticket_detalle.html', {
        'ticket': ticket,
        'tecnico': tecnico,
    })


# ========== CERRAR TICKET DIRECTO (BOTÓN RÁPIDO) ==========

def cerrar_ticket(request, ticket_id):
    """
    Cierra un ticket directamente desde el listado (sin pasar por detalle).
    """
    if not require_tecnico():
        return redirect('login')

    ticket = get_object_or_404(TicketSoporte, id=ticket_id)
    ticket.estado = 'CERRADO'
    ticket.save()

    messages.success(request, "Ticket cerrado correctamente.")
    # 🔹 Aquí estaba el error: antes usabas 'soporte_panel'
    return redirect('soporte:panel_soporte')
