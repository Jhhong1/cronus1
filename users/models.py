from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from services.models import Projects


# Create your models here.


class UserProfile(AbstractUser):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    username = models.CharField(max_length=10, unique=True, verbose_name="用户名")
    email = models.EmailField(max_length=50, unique=True, verbose_name="邮箱")
    password = models.CharField(max_length=256, verbose_name="密码")
    projects = models.ManyToManyField(Projects)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        default_permissions = []
        permissions = [
            ('create_user', '创建'),
            ('update_user', '更新'),
            ('delete_user', '删除'),
            ('view_user', '查看')
        ]

    def __str__(self):
        return self.username


class ResetCode(models.Model):
    code = models.CharField(max_length=8, null=True, blank=True)
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)

    class Meta:
        default_permissions = []


class GroupExtend(Group):
    description = models.CharField(max_length=200, verbose_name="描述", blank=True, editable=False)

    class Meta:
        verbose_name_plural = '权限组'
        verbose_name = '权限组'
        default_permissions = []
        permissions = [
            ('create_group', '创建'),
            ('update_group', '更新'),
            ('delete_group', '删除'),
            ('view_group', '查看')
        ]

    def __str__(self):
        return self.name
