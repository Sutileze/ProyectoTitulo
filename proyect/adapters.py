# tu_app/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """
        Lógica antes del login social
        """
        pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Guardar usuario con información adicional
        """
        user = super().save_user(request, sociallogin, form)
        return user