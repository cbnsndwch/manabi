from django.conf import settings

from django.contrib.auth.models import User
from account.auth_backends import AuthenticationBackend


class AuthenticationBackendWithLazySignup(AuthenticationBackend):
    
    def authenticate(self, **credentials):
        lookup_params = {}
        if settings.ACCOUNT_EMAIL_AUTHENTICATION:
            name, identity = "email", credentials.get("email")
        else:
            name, identity = "username", credentials.get("username")
        if identity is None:
            return None
        lookup_params[name] = identity
        try:
            user = User.objects.get(**lookup_params)
        except User.DoesNotExist:
            return None
        else:
            if user.check_password(credentials.get("password")):
                return user


EmailModelBackend = AuthenticationBackendWithLazySignup

