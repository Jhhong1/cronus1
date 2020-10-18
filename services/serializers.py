import re
import json
import six
import logging
import timezone_field
from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from django_celery_beat.models import PeriodicTasks

from services.utils import generate_uuid
from services.tasks import bound_set_to_task, bound_cases_to_set, Start, run
from services.models import Projects, Config, Counter, Cases, Tasks, Sets, Histories, CasesRelationShip, \
    SetsRelationShip, CrontabSchedule, PeriodicTask


logger = logging.getLogger()


def _validate_name(name):
    if len(name) < 1 or len(name) > 50:
        raise serializers.ValidationError(
            "the name must be not less than 6 digits greater than 50 digits"
        )
    if not re.match(r'^([a-z]+[a-z0-9_-]{1,49})$', name):
        raise serializers.ValidationError(
            "the name format is '[a-z]+[a-z0-9_-]{1,49}'")
    return name


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    createTime = serializers.DateTimeField(read_only=True)
    updateTime = serializers.DateTimeField(read_only=True)
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        label='项目名称',
        validators=[
            UniqueValidator(
                queryset=Projects.objects.all(),
                message="the project name already exists")
        ])
    description = serializers.CharField(required=False, label='描述信息')

    class Meta:
        model = Projects
        fields = '__all__'

    def validate_name(self, name):
        return _validate_name(name)


class ConfigSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    createTime = serializers.DateTimeField(read_only=True)
    updateTime = serializers.DateTimeField(read_only=True)
    name = serializers.CharField(required=True, allow_blank=False)
    baseurl = serializers.URLField(required=False, allow_blank=True)
    headers = serializers.DictField(required=False, allow_null=True)
    proxy = serializers.ListField(required=False, allow_null=True)
    variables = serializers.DictField(required=False, allow_null=True)

    class Meta:
        model = Config
        exclude = ['sets']
        validators = [
            UniqueTogetherValidator(
                queryset=Config.objects.all(),
                fields=['project', 'name'],
                message='config already exist'
            )
        ]

    def validate_name(self, name):
        return _validate_name(name)

    def validate(self, attrs):
        global_config = attrs.get('globalConfig')
        project_id = attrs.get('project')
        category = attrs.get('category')

        if global_config:
            ret = Config.objects.filter(globalConfig=global_config, project=project_id, category=category)
            try:
                config_instance = Config.objects.get(name=attrs.get('name'), project=project_id)
            except ObjectDoesNotExist:
                if ret.exists():
                    raise serializers.ValidationError(
                        'the global config already exists')
            else:
                if ret.exists() and ret[0].id != config_instance.id:
                    raise serializers.ValidationError(
                        'the global config already exists')

        return attrs


class CounterSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    createTime = serializers.DateTimeField(read_only=True)
    updateTime = serializers.DateTimeField(read_only=True)
    name = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Counter
        exclude = ['tasks']
        validators = [
            UniqueTogetherValidator(
                queryset=Counter.objects.all(),
                fields=['project', 'name'],
                message='counter already exist'
            )
        ]

    def validate_name(self, name):
        return _validate_name(name)


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Histories
        fields = '__all__'
        ordering = ['-start_time']


class CasesSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    createTime = serializers.DateTimeField(read_only=True)
    updateTime = serializers.DateTimeField(read_only=True)
    variables = serializers.DictField(required=False, allow_null=True)
    asserts = serializers.ListField(required=False, allow_null=True)
    body = serializers.DictField(required=False, allow_null=True)
    extracts = serializers.ListField(required=False, allow_null=True)
    headers = serializers.DictField(required=False, allow_null=True)
    procedures = serializers.ListField(required=False, allow_null=True)
    history = HistorySerializer(many=True, read_only=True)

    class Meta:
        model = Cases
        exclude = ['sets']
        validators = [
            UniqueTogetherValidator(
                queryset=Cases.objects.all(),
                message='case already exist',
                fields=['project', 'name', 'category']
            )
        ]

    def validate_name(self, name):
        return _validate_name(name)


class SetsSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    createTime = serializers.DateTimeField(read_only=True)
    updateTime = serializers.DateTimeField(read_only=True)
    tags = serializers.ListField(required=True, allow_null=True)
    history = HistorySerializer(many=True, read_only=True)

    class Meta:
        model = Sets
        exclude = ['tasks']
        validators = [
            UniqueTogetherValidator(
                queryset=Sets.objects.all(),
                fields=['project', 'name', 'category'],
                message='test set already exist'
            )
        ]

    def validate_name(self, name):
        return _validate_name(name)


class TasksSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    createTime = serializers.DateTimeField(read_only=True)
    updateTime = serializers.DateTimeField(read_only=True)
    history = HistorySerializer(many=True, read_only=True)

    class Meta:
        model = Tasks
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Tasks.objects.all(),
                fields=['project', 'name', 'category'],
                message='task already exist'
            )
        ]

    def validate_name(self, name):
        return _validate_name(name)


class CaseBindingSerializer(serializers.Serializer):
    set_id = serializers.CharField()
    cases = serializers.ListField(required=False, allow_null=True)
    handler = serializers.CharField(required=False)

    def create(self, validated_data):
        set_id = validated_data.get('set_id')
        handler = validated_data.get('handler', None)
        set_instance = Sets.objects.get(id=set_id)
        cases = validated_data.get('cases')
        max_order = ''
        for case in cases:
            if not handler:
                max_order = set_instance.relations.filter(handler=None) \
                    .aggregate(Max('order')).get('order__max')
            elif handler == 'setup':
                max_order = set_instance.relations.filter(handler="setup"). \
                    aggregate(Max('order')).get('order__max')
            elif handler == 'teardown':
                max_order = set_instance.relations.filter(handler="teardown"). \
                    aggregate(Max('order')).get('order__max')
            case_id = case.get('id')
            case_instance = Cases.objects.get(pk=case_id)
            max_order = max_order or 0
            case_instance.relations.create(sets=set_instance, order=max_order + 1, level='sets', handler=handler)
        bound_cases_to_set.apply_async((set_id, handler, cases))

        return validated_data


class OrderSerializer(serializers.Serializer):
    set_id = serializers.CharField()
    cases = serializers.ListField(required=False, allow_null=True)
    handler = serializers.CharField(required=False)

    def create(self, validated_data):
        set_id = validated_data.get('set_id')
        cases = validated_data.get('cases')
        handler = validated_data.get('handler', None)

        for index, case in enumerate(cases, 1):
            order = int(case.get('relations__order'))
            if index != order:
                CasesRelationShip.objects.filter(
                    cases_id=case.get('id'),
                    sets_id=set_id,
                    order=case.get('relations__order'),
                    handler=handler).update(order=index)

        return validated_data


class UnboundCaseSerializer(serializers.Serializer):
    case_id = serializers.CharField()
    set_id = serializers.CharField()
    order = serializers.CharField()
    handler = serializers.CharField(required=False)


class ConfigBindingSerializer(serializers.Serializer):
    config_id = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    set_id = serializers.CharField()

    def create(self, validated_data):
        config_id = validated_data.get('config_id')
        set_id = validated_data.get('set_id')
        set_instance = Sets.objects.get(pk=set_id)
        if config_id:
            set_instance.config.clear()
            set_instance.config.add(config_id)
        else:
            set_instance.config.clear()
        return validated_data


class CounterBindingSerializer(serializers.Serializer):
    task = serializers.CharField()
    counter = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        task = validated_data.get('task')
        counter = validated_data.get('counter')
        instance = Tasks.objects.get(id=task)
        if counter:
            instance.counters.clear()
            instance.counters.add(counter)
        else:
            instance.counters.clear()
        return validated_data


class SetBindingSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    sets = serializers.ListField(required=False, allow_null=True)

    def create(self, validated_data):
        task_id = validated_data.get('task_id')
        task_instance = Tasks.objects.get(pk=task_id)
        sets = validated_data.get('sets')

        for testSet in sets:
            set_id = testSet.get('id')
            if not task_instance.relationship.filter(sets_id=set_id).exists():
                task_instance.relationship.create(sets_id=set_id)
        bound_set_to_task.apply_async((task_id, ))
        return validated_data


class UnboundSetsSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    set_id = serializers.CharField()


class RunnerSerializer(serializers.Serializer):
    id = serializers.CharField()
    level = serializers.CharField()
    category = serializers.CharField()
    tags = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        logger.info("Request data for executing tasks: {}".format(validated_data))
        obj_id = validated_data.get('id')
        level = validated_data.get('level')
        tags = validated_data.get('tags', None)
        category = validated_data.get('category', None)

        assert level in ('cases', 'sets', 'tasks'), "level not in ('cases', 'sets', 'tasks')"
        batch = generate_uuid()
        Start(obj_id, level, batch).run()

        run(level, obj_id, batch, tags, category)

        return validated_data


class CaseRelationShipSerializer(serializers.ModelSerializer):
    cases = CasesSerializer(read_only=True)
    history = HistorySerializer(read_only=True, many=True)

    class Meta:
        model = CasesRelationShip
        fields = '__all__'


class SetRelationShipSerializer(serializers.ModelSerializer):
    sets = SetsSerializer(read_only=True)
    history = HistorySerializer(read_only=True, many=True)

    class Meta:
        model = SetsRelationShip
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    history = HistorySerializer(read_only=True, many=True)

    class Meta:
        model = Tasks
        fields = '__all__'


class TimeZoneField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        kwargs.setdefault('choices', [(six.text_type(v), t) for v, t in timezone_field.TimeZoneField.CHOICES])
        super(TimeZoneField, self).__init__(**kwargs)


class CronScheduleSerializer(serializers.ModelSerializer):
    # fix: TypeError: Object of type 'Africa/Abidjan' is not JSON serializable
    timezone = TimeZoneField()

    class Meta:
        model = CrontabSchedule
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=CrontabSchedule.objects.all(),
                fields=['project', 'name'],
                message='cron already exist'
            )
        ]

    def validate_name(self, name):
        return _validate_name(name)

    def update(self, instance, validated_data):
        super(CronScheduleSerializer, self).update(instance, validated_data)
        periodic_tasks = instance.periodictask_set.all()
        for task in periodic_tasks:
            PeriodicTasks.changed(task)
        return instance


class PeriodicTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'

    def create(self, validated_data):
        return PeriodicTask.objects.create(
            crontab=validated_data.get('crontab'),
            name=validated_data.get('name'),
            task=validated_data.get('task'),
            args=json.dumps([str(validated_data.get('tasks').id)]),
            kwargs=json.dumps({'tags': validated_data.get('tags'), 'category': validated_data.get('category')}),
            tags=validated_data.get('tags'),
            category=validated_data.get('category'),
            tasks=validated_data.get('tasks'),
            display=validated_data.get('display'),
            project=validated_data.get('project')
        )

    def update(self, instance, validated_data):
        super(PeriodicTaskSerializer, self).update(instance, validated_data)
        PeriodicTasks.changed(instance)
        return instance
