from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password


class LoginAuthorization(object):
    def authenticate(self, request, username=None, password=None):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            return None
        pwd = user.password
        pwd_valid = check_password(password, pwd)
        if pwd_valid:
            return user
        return None
