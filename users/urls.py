from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import RegistryViewSet, UserViewSet, ChangePasswordViewSet, ResetPasswordEmailViewSet, \
    ResetPasswordView, LoginViewSet, ApplicationViewSet, SuperuserViewSet, PermissionViewSet, GroupViewSet, \
    BoundPermissionViewSet, SecretViewSet


router = DefaultRouter()
router.register('register', RegistryViewSet, basename='register')
router.register('user', UserViewSet, basename='user')
router.register('change', ChangePasswordViewSet, basename='change')
router.register('email', ResetPasswordEmailViewSet, basename="email")
router.register('reset/password', ResetPasswordView, basename='reset_password')
router.register('secret', SecretViewSet, basename='secret')
router.register('login', LoginViewSet, basename='login')
router.register('application', ApplicationViewSet, basename='application')
router.register('superuser', SuperuserViewSet, basename='superuser')
router.register('permissions', PermissionViewSet, basename='permission')
router.register('groups', GroupViewSet, basename='groups')
router.register('binding/permission', BoundPermissionViewSet, basename='binding_permission')

urlpatterns = [
    path('', include(router.urls)),
]
