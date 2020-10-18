from uuid import uuid4
from django.db import models
from django_celery_beat.models import (PeriodicTask as Periodic, CrontabSchedule as Cron)

# Create your models here.


class Projects(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name="项目名称")
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    description = models.TextField(null=True, blank=True, verbose_name="描述信息")

    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ['-updateTime']
        default_permissions = []
        permissions = [
            ('create_projects', '创建'),
            ('update_projects', '更新'),
            ('delete_projects', '删除'),
            ('view_projects', '查看')
        ]

    def __str__(self):
        return self.name


class Tasks(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name="任务名称")
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    description = models.TextField(null=True, blank=True, verbose_name="描述信息")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    category = models.CharField(max_length=10, choices=(('api', 'api'), ('ui', 'ui')), default='api', verbose_name="类别")

    class Meta:
        verbose_name = "测试任务"
        verbose_name_plural = "测试任务"
        ordering = ['-updateTime']
        unique_together = ['project', 'name', 'category']
        default_permissions = []
        permissions = [
            ('create_tasks', '创建'),
            ('update_tasks', '更新'),
            ('delete_tasks', '删除'),
            ('view_tasks', '查看'),
            ('execute_tasks', '执行任务'),
            ('associate_set', '关联测试集'),
            ('remove_set', '移除测试集'),
            ('associate_counter', '关联计数器')
        ]

    def __str__(self):
        return self.name


class Sets(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name="测试集名称")
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    tags = models.JSONField(null=True, blank=True, verbose_name="标签")
    description = models.TextField(null=True, blank=True, verbose_name="描述信息")
    category = models.CharField(max_length=10, choices=(('api', 'api'), ('ui', 'ui')), default='api', verbose_name="类别")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')
    tasks = models.ManyToManyField(
        Tasks,
        through='SetsRelationShip'
    )

    class Meta:
        verbose_name = "测试集"
        verbose_name_plural = "测试集"
        ordering = ['-updateTime']
        unique_together = ['project', 'name', 'category']
        default_permissions = []
        permissions = [
            ('create_sets', '创建'),
            ('update_sets', '更新'),
            ('delete_sets', '删除'),
            ('view_sets', '查看'),
            ('execute_set', '执行测试集'),
            ('remove_case', '移除用例'),
            ('copy_case', '复制用例'),
            ('associate_config', '配置引用'),
            ('associate_cases', '关联用例')
        ]

    def __str__(self):
        return self.name


class Counter(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name="引用名")
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    initial = models.IntegerField(verbose_name="初始值")
    step = models.IntegerField(verbose_name="增量")
    final = models.IntegerField(verbose_name="最大值")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')
    tasks = models.ManyToManyField(Tasks, related_name='counters')

    class Meta:
        verbose_name = '计数器'
        verbose_name_plural = '计数器'
        ordering = ['-updateTime']
        unique_together = ['project', 'name']
        default_permissions = []
        permissions = [
            ('create_counter', '创建'),
            ('update_counter', '更新'),
            ('delete_counter', '删除'),
            ('view_counter', '查看')
        ]

    def __str__(self):
        return self.name


class Config(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name="配置名称")
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    baseurl = models.URLField(verbose_name="BaseURL")
    headers = models.JSONField(null=True, blank=True, verbose_name="头部信息")
    variables = models.JSONField(null=True, blank=True, verbose_name="变量")
    proxy = models.JSONField(null=True, blank=True, verbose_name="代理")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    globalConfig = models.BooleanField(default=False, verbose_name="是否是全局变量")
    category = models.CharField(max_length=10, choices=(('api', 'api'), ('ui', 'ui')), default='api', verbose_name="类别")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')
    sets = models.ManyToManyField(Sets, related_name='config')

    class Meta:
        verbose_name = '配置'
        verbose_name_plural = '配置'
        ordering = ['-updateTime']
        unique_together = ['project', 'name']
        default_permissions = []
        permissions = [
            ('create_config', '创建'),
            ('update_config', '更新'),
            ('delete_config', '删除'),
            ('view_config', '查看')
        ]

    def __str__(self):
        return self.name


class Cases(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name="用例名称")
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    url = models.CharField(max_length=255, null=True, blank=True, verbose_name="请求地址")
    method = models.CharField(max_length=6, null=True, blank=True, verbose_name="请求方法")
    variables = models.JSONField(null=True, blank=True, verbose_name="变量")
    headers = models.JSONField(null=True, blank=True, verbose_name="头部信息")
    body = models.JSONField(null=True, blank=True, verbose_name="请求内容")
    asserts = models.JSONField(null=True, blank=True, verbose_name="结果断言")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updateTime = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    extracts = models.JSONField(null=True, blank=True, verbose_name="提取参数")
    waitingTime = models.IntegerField(default=10, verbose_name="超时时间")
    continues = models.BooleanField(default=False, verbose_name="失败后是否继续")
    cycle = models.IntegerField(default=1, verbose_name="重试次数")
    category = models.CharField(max_length=10, choices=(('api', 'api'), ('ui', 'ui')), default='api', verbose_name="类别")
    procedures = models.JSONField(null=True, blank=True, verbose_name="步骤")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')
    sets = models.ManyToManyField(
        Sets,
        through='CasesRelationShip'
    )
    tasks = models.ManyToManyField(Tasks, through='CasesRelationShip')

    class Meta:
        verbose_name = "接口用例"
        verbose_name_plural = "接口用例"
        ordering = ['-updateTime']
        unique_together = ['project', 'name', 'category']
        default_permissions = []
        permissions = [
            ('create_cases', '创建'),
            ('update_cases', '更新'),
            ('delete_cases', '删除'),
            ('view_cases', '查看'),
            ('execute_cases', '执行')
        ]

    def __str__(self):
        return self.name


class SetsRelationShip(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    tasks = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name='relationship')
    sets = models.ForeignKey(Sets, on_delete=models.CASCADE, related_name='relationship')

    class Meta:
        default_permissions = []


class CasesRelationShip(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    order = models.IntegerField(null=True, blank=True, verbose_name="序列号")
    cases = models.ForeignKey(Cases, null=True, blank=True, on_delete=models.CASCADE, related_name='relations')
    sets = models.ForeignKey(Sets, null=True, blank=True, on_delete=models.CASCADE, related_name='relations')
    level = models.CharField(max_length=20, null=True, blank=True, verbose_name="级别")
    tasks = models.ForeignKey(Tasks, null=True, blank=True, on_delete=models.CASCADE, related_name='relations')
    handler = models.CharField(max_length=20, blank=True, null=True, verbose_name="处理器")

    class Meta:
        default_permissions = []


class Histories(models.Model):
    id = models.UUIDField(primary_key=True, auto_created=True, default=uuid4, editable=False)
    status = models.CharField(max_length=20, null=True, blank=True, verbose_name="状态")
    result = models.CharField(max_length=20, null=True, blank=True, verbose_name="执行结果")
    error_message = models.TextField(null=True, blank=True, verbose_name="错误信息")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    response = models.JSONField(null=True, blank=True, verbose_name="请求结果")
    image = models.ImageField(null=True, blank=True, verbose_name="图片", upload_to='ui/')
    batch = models.UUIDField(null=True, blank=True)
    cases = models.ForeignKey(Cases, on_delete=models.CASCADE, null=True, blank=True, db_column='cases', related_name='history')
    sets = models.ForeignKey(Sets, on_delete=models.CASCADE, null=True, blank=True, db_column='sets', related_name='history')
    tasks = models.ForeignKey(Tasks, on_delete=models.CASCADE, null=True, blank=True, db_column='tasks', related_name='history')
    set_cases = models.ForeignKey(CasesRelationShip, on_delete=models.CASCADE, null=True, blank=True, db_column='set_cases', related_name='history')
    task_sets = models.ForeignKey(SetsRelationShip, on_delete=models.CASCADE, null=True, blank=True, db_column='task_sets', related_name='history')

    class Meta:
        default_permissions = []
        ordering = ['-start_time']


class PeriodicTask(Periodic):
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')
    tasks = models.ForeignKey(Tasks, on_delete=models.DO_NOTHING, verbose_name="任务")
    tags = models.CharField(max_length=50, null=True, blank=True, verbose_name="标签")
    category = models.CharField(max_length=10, choices=(('api', 'api'), ('ui', 'ui')), default='api', verbose_name="类别")

    class Meta:
        verbose_name_plural = '定时任务'
        verbose_name = '定时任务'
        default_permissions = []
        permissions = [
            ('create_periodictask', '创建'),
            ('update_periodictask', '更新'),
            ('delete_periodictask', '删除'),
            ('view_periodictask', '查看')
        ]

    def __str__(self):
        return self.name


class CrontabSchedule(Cron):
    display = models.CharField(max_length=100, null=True, blank=True, verbose_name="显示名称")
    name = models.CharField(max_length=50, verbose_name="名称")
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, db_column='project')

    class Meta:
        verbose_name_plural = '定时规则'
        verbose_name = '定时规则'
        unique_together = ['project', 'name']
        default_permissions = []
        permissions = [
            ('create_crontabschedule', '创建'),
            ('update_crontabschedule', '更新'),
            ('delete_crontabschedule', '删除'),
            ('view_crontabschedule', '查看')
        ]

    def __str__(self):
        return self.name
