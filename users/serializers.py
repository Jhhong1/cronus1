import re
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission, ContentType
from rest_framework import serializers

from users.models import GroupExtend
from users.email import send_email


def _validate_password(password):
    if len(password) < 8 or len(password) > 16:
        raise serializers.ValidationError("密码的长度不得少于8位，大于16位")
    if not re.match(r'([a-z]+[a-z0-9_-]{7,15})$', password):
        raise serializers.ValidationError('密码必须已小写字母开头，包含小写字母、数字、下划线、中横线')
    return password


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label='用户名')
    password = serializers.CharField(write_only=True, label="密码", style={'input_type': 'password'})
    email = serializers.EmailField(label='邮箱')

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')

    def validate_username(self, username):
        user = get_user_model()
        if user.objects.filter(username=username).exists():
            raise serializers.ValidationError("该用户名已存在")
        if len(username) < 5 or len(username) > 10:
            raise serializers.ValidationError("用户名的字符串长度不得少于5位，大于10位")
        if not re.match(r'^([a-z]+[a-z0-9_-]{4,9})$', username):
            raise serializers.ValidationError("用户名必须已小写字母开头，包含小写字母、数字、下划线、中横线")
        return username

    def validate_password(self, password):
        return _validate_password(password)

    def validate_email(self, email):
        user = get_user_model()
        if user.objects.filter(email=email).exists():
            raise serializers.ValidationError("该邮箱已存在")
        return email

    def create(self, validated_data):
        user = get_user_model()
        pwd = validated_data['password']
        validated_data['password'] = make_password(pwd)
        return user.objects.create(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = '__all__'


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(label="密码", write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('password', )

    def validate_password(self, password):
        return _validate_password(password)


# 发送重置密码邮件的serializer
class ResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(label="邮箱")

    def validate_email(self, email):
        user = get_user_model()
        if not user.objects.filter(email=email):
            raise serializers.ValidationError("该邮箱不存在")
        return email

    def create(self, validated_data):
        send_email(validated_data['email'])
        return validated_data


# 重置密码
class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(label="密码", write_only=True)

    def validate_password(self, password):
        return _validate_password(password)


class RegisterApplicationSerializer(serializers.Serializer):
    name = serializers.CharField()
    client_id = serializers.CharField()
    client_secret = serializers.CharField()
    client_type = serializers.CharField()
    authorization_grant_type = serializers.CharField()


class SuperUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class ContentTypeSerializer(serializers.ModelSerializer):
    permission_set = PermissionSerializer(read_only=True, many=True)

    class Meta:
        model = ContentType
        fields = '__all__'


class ContentType2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = '__all__'


class Permission2Serializer(serializers.ModelSerializer):
    content_type = ContentType2Serializer(read_only=True)

    class Meta:
        model = Permission
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    permissions = Permission2Serializer(read_only=True, many=True)

    class Meta:
        model = GroupExtend
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label='用户名')
    password = serializers.CharField(label='密码')
    client_id = serializers.CharField()
    client_secret = serializers.CharField()
    grant_type = serializers.CharField()


class BoundPermissionSerializer(serializers.Serializer):
    user = serializers.CharField(required=False)
    projects = serializers.ListField(required=False)
    group = serializers.CharField(required=False)