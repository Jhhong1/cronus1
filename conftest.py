import pytest
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from oauth2_provider.models import Application
from users.models import UserProfile
from register_app_create_superuser import client_secret, client_id


@pytest.fixture
def access_token():
    Application.objects.create(name='admin', client_id=client_id, client_secret=client_secret,
                               client_type='confidential', authorization_grant_type='password')
    UserProfile.objects.create(username="auth", password=make_password('123456'), is_superuser=True)
    url = reverse('login-list')
    client = APIClient()
    client.post(url, data={'username': 'auth', 'password': '123456', 'grant_type': 'password',
                           'client_id': client_id, 'client_secret': client_secret})
