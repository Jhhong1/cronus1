import os

import django
from django.contrib.auth.hashers import make_password

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cronus.settings')

django.setup()

client_id = 'yldmPIHSyHd2F8hIFmqPIzGSKnY6E3aboflk1jQX'
client_secret = 'i4S02vzRk38jKU5fcdg07Vaay7kPOJm2mnjFhFMcKvNFYqXCvVUJgUHP7aoHVEeghw' \
                'r9wJsvHge3SMUFEleWgUcntSZEBA4n0RDEXTc9TWU3NDUrLwklHRDASM6Nv48H'

SUPERUSER_NAME = os.getenv('SUPERUSER_NAME', 'admin')
SUPERUSER_PASSWORD = os.getenv('SUPERUSER_PASSWORD', 'adminpwd')


def register_application():
    from oauth2_provider.models import Application

    app = Application.objects.first()

    if not app:
        Application.objects.create(name='admin', client_id=client_id, client_secret=client_secret,
                                   client_type='confidential', authorization_grant_type='password')
    else:
        print("application admin already exists")


def create_superuser():
    from users.models import UserProfile

    user = UserProfile.objects.filter(is_superuser=True)
    if not user.exists():
        UserProfile.objects.create(username=SUPERUSER_NAME, password=make_password(SUPERUSER_PASSWORD),
                                   email='admin@admin.com', is_superuser=True, is_staff=True)
    else:
        print("super user already exists")


if __name__ == '__main__':
    register_application()
    create_superuser()
