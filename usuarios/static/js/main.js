// usuarios/static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("Formulario de Comerciantes de Barrio cargado y listo para JS.");

    // Seleccionamos los enlaces de las pestañas usando su contenido de texto para robustez
    // Asegúrate de que los enlaces tengan los hrefs de Django: href="{% url 'login' %}" y href="{% url 'registro' %}"
    const loginTab = document.querySelector('a[href*="login"]');
    const registroTab = document.querySelector('a[href*="registro"]');
    const path = window.location.pathname;

    // Clases de estilo:
    const ACTIVE_CLASSES = ['border-b-primary', 'text-[#0d171b]', 'dark:text-white'];
    const INACTIVE_CLASSES = ['border-b-transparent', 'text-[#4c809a]', 'dark:text-gray-400'];

    // --- Función para resaltar la pestaña correcta ---
    function highlightTab() {
        if (!loginTab || !registroTab) return;

        // Comprobamos la URL actual para saber dónde estamos
        const isInRegistro = path.includes('registro');
        const isInLogin = path.includes('login') || (!isInRegistro && path === '/'); // Asumimos que '/' o un path sin especificar va a Login

        if (isInRegistro) {
            // Activar Registro
            registroTab.classList.add(...ACTIVE_CLASSES);
            registroTab.classList.remove(...INACTIVE_CLASSES);
            
            // Desactivar Login
            loginTab.classList.add(...INACTIVE_CLASSES);
            loginTab.classList.remove(...ACTIVE_CLASSES);

        } else if (isInLogin) {
            // Activar Login
            loginTab.classList.add(...ACTIVE_CLASSES);
            loginTab.classList.remove(...INACTIVE_CLASSES);

            // Desactivar Registro
            registroTab.classList.add(...INACTIVE_CLASSES);
            registroTab.classList.remove(...ACTIVE_CLASSES);
        }
    }

    // Ejecutar la función de resaltado al cargar
    highlightTab();

    // Nota: Mantenemos el comportamiento natural de los enlaces (navegar)
    // porque es la forma estándar de cambiar entre vistas de Login y Registro en Django.
    // No necesitamos un preventDefault() aquí, ya que queremos que el navegador
    // siga el enlace de Django para cargar la nueva página/formulario.
});

