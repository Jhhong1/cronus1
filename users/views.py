import json
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import ContentType
from django.db.models import Q
from oauth2_provider.views.mixins import OAuthLibMixin
from oauth2_provider.settings import oauth2_settings
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from rest_framework.permissions import AllowAny
from oauth2_provider.models import Application
from users.serializers import UserRegisterSerializer, UserSerializer, ChangePasswordSerializer, ResetEmailSerializer, \
    ResetPasswordSerializer, LoginSerializer, RegisterApplicationSerializer, SuperUserSerializer, \
    GroupSerializer, BoundPermissionSerializer, ContentTypeSerializer
from users.models import ResetCode, GroupExtend
from users.permissions import Permission
from users.authorization import LoginAuthorization

# Create your views here.


class RegistryViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSerializer
    permission_classes = [Permission]

    def get_queryset(self):
        user = get_user_model()
        return user.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        groups = instance.groups.values()
        serializer = self.get_serializer(instance)
        results = serializer.data
        results['groups'] = groups
        return Response(results)


class ChangePasswordViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = ChangePasswordSerializer
    lookup_field = 'username'

    def get_queryset(self):
        user = get_user_model()
        return user.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.password = make_password(request.data['password'])
        instance.save()
        msg = {"result": "reset password success"}
        return Response(msg, status=HTTP_200_OK)


# 发送重置密码邮件
class ResetPasswordEmailViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ResetEmailSerializer
    permission_classes = [AllowAny]


class ResetPasswordView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        reset_code = self.request.query_params.get('code', None)
        user = ResetCode.objects.get(code=reset_code).user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.password = make_password(request.data['password'])
        user.save()
        msg = {"result": "reset password success"}
        return Response(msg, status=HTTP_201_CREATED)


class ApplicationViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterApplicationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Application.objects.all()

    def create(self, request, *args, **kwargs):
        params = request.data
        serializer = self.get_serializer(data=params)
        serializer.is_valid(raise_exception=True)
        Application.objects.create(**params)
        msg = {"result": "Registered application successfully"}
        return Response(msg, status=HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ret = list(queryset.values())
        return Response(ret, status=HTTP_200_OK)


class SuperuserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = SuperUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_model()
        return user.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ret = list(queryset.filter(is_superuser=True).values())
        return Response(ret, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = get_user_model()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user.objects.create_superuser(username=data['username'], email=data['email'], password=data['password'])
        msg = {"result": "create super user success"}
        return Response(msg, status=HTTP_201_CREATED)


translation = {
            'cases': '测试用例',
            'projects': '项目',
            'set': '测试集',
            'tasks': '测试任务',
            'config': '配置',
            'counter': '计数器',
            'crontabschedule': '定时规则',
            'periodictask': '定时任务',
            'groupextend': '用户组',
            'userprofile': '用户'
        }


class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ContentTypeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ContentType.objects.filter(Q(app_label='services') | Q(app_label='users'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        permissions = []
        contents = serializer.data
        print(contents)
        for content in contents:
            mod = content['model']
            if mod in translation and content['permission_set']:
                content['name'] = translation[mod]
                permissions.append(content)
        return Response(permissions)


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [Permission]

    def get_queryset(self):
        return GroupExtend.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data

        permissions = self._extract_permissions(data.pop('permissions'))

        g = GroupExtend.objects.create(**data)
        for permission in permissions:
            g.permissions.add(permission)
        data = list(GroupExtend.objects.filter(pk=g.id).values())
        return Response(data, status=HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        contents = self._translation_data(serializer.data)
        return Response(contents)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        groups = serializer.data
        for group in groups:
            for permission in group['permissions']:
                mod = permission['content_type']['model']
                if mod in translation:
                    permission['content_type']['name'] = translation[mod]
        return Response(groups)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        permissions = self._extract_permissions(data['permissions'])
        data['permissions'] = permissions
        instance.description = data['description']
        instance.permissions.clear()
        for permission in permissions:
            instance.permissions.add(permission)
        return Response(request.data)

    def _extract_permissions(self, contents):
        """
        :param contents: dict of permissions codenames
        :return:
        """
        permissions = []

        for _, value in contents.items():
            if isinstance(value, list) and value:
                permissions.extend(value)
        return permissions

    def _translation_data(self, contents):
        result = {}
        for content in contents.pop('permissions'):
            content_type = content.pop('content_type')
            mod = content_type['model']
            if mod not in result:
                result[mod] = {}
                result[mod]['permissions'] = []
                result[mod]['permissions'].append(content)
            else:
                result[mod]['permissions'].append(content)
        contents['permissions'] = []
        for key, value in result.items():
            if key in translation:
                value['name'] = translation[key]
                value['model'] = key
                contents['permissions'].append(value)
        return contents


class SecretViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        app = Application.objects.first()
        data = {
            "client_id": app.client_id,
            "client_secret": app.client_secret,
            "grant_type": app.authorization_grant_type
        }
        return Response(data=data, status=HTTP_200_OK)


class LoginViewSet(mixins.CreateModelMixin, OAuthLibMixin, viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS

    def create(self, request, *args, **kwargs):
        username = request.data['username']
        password = request.data['password']
        user = LoginAuthorization().authenticate(request, username=username, password=password)
        if not user:
            msg = {"AuthenticationError": "username or password invalid"}
            return Response(msg, status=HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            msg = {"AuthenticationError": "current user is inactive"}
            return Response(msg, status=HTTP_403_FORBIDDEN)

        data = {}
        url, headers, body, status = self.create_token_response(request)

        body = json.loads(body)

        data['access_token'] = body['access_token']
        data['refresh_token'] = body['refresh_token']
        data['token_type'] = body['token_type']
        data['project'] = list(user.projects.values())
        data['permissions'] = user.get_group_permissions()
        data['is_superuser'] = False
        if user.is_superuser:
            data['is_superuser'] = True

        return Response(data=data, status=HTTP_200_OK)


class BoundPermissionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = BoundPermissionSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = get_user_model()
        user_instance = user.objects.get(id=data['user'])
        group = data.get('group', '')
        projects = data.get('projects')
        if group:
            user_instance.groups.clear()
            user_instance.groups.add(group)
        else:
            user_instance.groups.clear()

        if projects:
            user_instance.projects.clear()
            for project in data['projects']:
                user_instance.projects.add(project)
        else:
            user_instance.projects.clear()

        user_data = list(user.objects.filter(id=data['user']).values())
        return Response(user_data)
