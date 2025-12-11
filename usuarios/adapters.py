from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """
        Lógica antes del login social
        """
        # Aquí puedes agregar lógica personalizada
        pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Guardar usuario con información adicional del formulario
        """
        user = super().save_user(request, sociallogin, form)
        
        # Si tienes campos adicionales en el formulario
        if form:
            # Aquí puedes guardar campos adicionales
            pass
            
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Poblar el usuario con datos del proveedor social
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Personalizar datos del usuario
        if sociallogin.account.provider == 'google':
            # Extraer nombre del email si no viene en los datos
            if not user.first_name and user.email:
                user.first_name = user.email.split('@')[0]
        
        return user