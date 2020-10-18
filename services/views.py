import os
import json
import logging
from django.db.models.query import QuerySet
from rest_framework import viewsets, mixins
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_200_OK
from rest_framework.response import Response

from cronus.settings import MEDIA_ROOT
from services.utils import remove_file
from services.pagination import CustomPagination
from services.models import Projects, Config, Counter, Cases, Tasks, Sets, CasesRelationShip, SetsRelationShip, \
    CrontabSchedule, PeriodicTask
from services.permissions import CRUDPermission, AssociateCasePermission, RemoveCasePermission, \
    AssociateConfigPermission, AssociateCounterPermission, AssociateSetPermission, RemoveSetsPermission, \
    RunnerPermission

from services.serializers import ProjectSerializer, ConfigSerializer, CounterSerializer, CasesSerializer, \
    SetsSerializer, TasksSerializer, CaseBindingSerializer, OrderSerializer, UnboundCaseSerializer, \
    ConfigBindingSerializer, CounterBindingSerializer, SetBindingSerializer, UnboundSetsSerializer, RunnerSerializer, \
    CaseRelationShipSerializer, SetRelationShipSerializer, ReportSerializer, CronScheduleSerializer, \
    PeriodicTaskSerializer


logger = logging.getLogger()


def remove_relation_image(relation):
    records = relation.history.values('image')
    for record in records:
        image = record['image']
        if image:
            full_path = os.path.join(MEDIA_ROOT, image)
            remove_file(full_path)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [CRUDPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Projects.objects.all()
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(userprofile=user)

        return queryset

    def create(self, request, *args, **kwargs):
        super(ProjectViewSet, self).create(request, *args, **kwargs)
        user = self.request.user
        name = request.data.get('name')
        queryset = Projects.objects.filter(name=name).values()[0]
        if not user.is_superuser:
            user.projects.add(queryset['id'])
        return Response(queryset, status=HTTP_201_CREATED)


class ConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ConfigSerializer
    permission_classes = [CRUDPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Config.objects.all()
        project_name = self.request.query_params.get('project', None)
        category = self.request.query_params.get('category', None)
        if project_name:
            queryset = queryset.filter(project__name=project_name)
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_id = Projects.objects.get(name=data.get('project')).id
        data['project'] = project_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)


class CounterViewSet(viewsets.ModelViewSet):
    serializer_class = CounterSerializer
    permission_classes = [CRUDPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Counter.objects.all()
        project_name = self.request.query_params.get('project', None)
        if project_name:
            queryset = queryset.filter(project__name=project_name)

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_id = Projects.objects.get(name=data.get('project')).id
        data['project'] = project_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)


class CasesViewSet(viewsets.ModelViewSet):
    serializer_class = CasesSerializer
    permission_classes = [CRUDPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Cases.objects.all()
        project_name = self.request.query_params.get('project', None)
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        if project_name:
            queryset = queryset.filter(project__name=project_name)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_id = Projects.objects.get(name=data.get('project')).id
        data['project'] = project_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)

    @staticmethod
    def _remove_cases_image(instance):
        records = instance.history.values('image')
        for record in records:
            image = record['image']
            if image:
                full_path = os.path.join(MEDIA_ROOT, image)
                remove_file(full_path)

    @staticmethod
    def _remove_cases_relations(instance):
        relations = instance.relations.iterator()
        for relation in relations:
            remove_relation_image(relation)

    def perform_destroy(self, instance):
        self._remove_cases_relations(instance)
        self._remove_cases_image(instance)
        instance.delete()


class SetsViewSet(viewsets.ModelViewSet):
    serializer_class = SetsSerializer
    permission_classes = [CRUDPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Sets.objects.all()
        project_name = self.request.query_params.get('project', None)
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        if project_name:
            queryset = queryset.filter(project__name=project_name)
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_name = data.get('project')
        project_id = Projects.objects.get(name=project_name).id
        data['project'] = project_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)

    @staticmethod
    def _remove_relation(instance):
        relations = instance.relations.iterator()
        for relation in relations:
            remove_relation_image(relation.id)

    def perform_destroy(self, instance):
        self._remove_relation(instance)
        instance.delete()


class TasksViewSet(viewsets.ModelViewSet):
    serializer_class = TasksSerializer
    permission_classes = [CRUDPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Tasks.objects.all()
        project_name = self.request.query_params.get('project', None)
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        if project_name:
            queryset = queryset.filter(project__name=project_name)

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_id = Projects.objects.get(name=data.get('project')).id
        data['project'] = project_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)

    @staticmethod
    def _remove_relation(instance):
        relations = instance.relations.iterator()
        for relation in relations:
            remove_relation_image(relation)

    def perform_destroy(self, instance):
        self._remove_relation(instance)
        instance.delete()


class CaseBindingViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CaseBindingSerializer
    permission_classes = [AssociateCasePermission]

    def get_queryset(self):
        return Sets.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        handler = self.request.query_params.get('handler', None)
        instance = self.get_object()
        cases = instance.cases_set.filter(relations__handler=handler, relations__level='sets')\
            .order_by('relations__order').values('id', 'name', 'display', 'method', 'url', 'relations__order')
        return Response(cases)


class OrderViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [AssociateCasePermission]

    def get_queryset(self):
        return Sets.objects.all()


class UnboundCaseViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UnboundCaseSerializer
    permission_classes = [RemoveCasePermission]

    def get_queryset(self):
        return Sets.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Remove case from test set
        """
        payload = request.data
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        case_id = data.get('case_id')
        set_id = data.get('set_id')
        handler = data.get('handler', None)
        order = int(data.get('order'))
        logger.info(
            "delete set_id {}、case_id {}、order {}、handler {} from relationship"
            .format(set_id, case_id, order, handler))
        relations = CasesRelationShip.objects.filter(sets_id=set_id, cases_id=case_id, order=order, handler=handler)
        for relation in relations:
            remove_relation_image(relation)

        relations.delete()

        m2 = CasesRelationShip.objects.filter(sets_id=set_id, handler=handler)
        for m in m2:
            if m.order > order:
                m.order -= 1
                m.save()

        return Response(status=HTTP_204_NO_CONTENT)


class ConfigBindingViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ConfigBindingSerializer
    permission_classes = [AssociateConfigPermission]

    def get_queryset(self):
        return Sets.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        config = instance.config.values()
        if config:
            config = config[0]
        else:
            config = {}
        return Response(config)


class CounterBindingViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CounterBindingSerializer
    permission_classes = [AssociateCounterPermission]

    def get_queryset(self):
        return Tasks.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        counter = instance.counters.values()
        if counter:
            counter = counter[0]
        else:
            counter = {}
        return Response(counter)


class SetBindingViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SetBindingSerializer
    permission_classes = [AssociateSetPermission]

    def get_queryset(self):
        return Tasks.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        sets = instance.sets_set.values()
        return Response(sets)


class UnboundSetsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UnboundSetsSerializer
    permission_classes = [RemoveSetsPermission]

    def get_queryset(self):
        return Tasks.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Remove set from task
        """
        payload = request.data
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        task_id = data.get('task_id')
        set_id = data.get('set_id')

        task_instance = Tasks.objects.get(id=task_id)
        relations = task_instance.relations.filter(sets_id=set_id)
        for relation in relations:
            remove_relation_image(relation)

        task_instance.relationship.filter(sets_id=set_id).delete()
        relations.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class RunnerViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    run cases
    """
    serializer_class = RunnerSerializer
    permission_classes = [RunnerPermission]

    def get_queryset(self):
        data = self.request.data
        level = data.get('level')
        if level == 'cases':
            return Cases.objects.all()
        elif level == 'sets':
            return Sets.objects.all()
        elif level == 'tasks':
            return Tasks.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        level = serializer.validated_data.get('level')
        obj_id = serializer.validated_data.get('id')
        ret = []
        if level == 'cases':
            ret = CasesSerializer(Cases.objects.get(pk=obj_id)).data
        elif level == 'sets':
            ret = SetsSerializer(Sets.objects.get(pk=obj_id)).data
        elif level == 'task':
            ret = TasksSerializer(Tasks.objects.get(pk=obj_id)).data

        return Response(ret, status=HTTP_201_CREATED)


class HistoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    def get_serializer_class(self):
        types = self.request.query_params.get('types')
        if types == 'cases':
            self.serializer_class = CasesSerializer
        elif types == 'sets':
            self.serializer_class = SetsSerializer
        elif types == 'tasks':
            self.serializer_class = TasksSerializer
        elif types == 'set_cases' or types == 'task_cases':
            self.serializer_class = CaseRelationShipSerializer
        elif types == 'task_sets':
            self.serializer_class = SetRelationShipSerializer
        else:
            pass
        return self.serializer_class

    def get_queryset(self):
        pass

    def _filter_data(self, contents, batch=None):
        ret = []
        if contents:
            if not isinstance(contents, QuerySet):
                raise TypeError('input value is not QuerySet')

            for query in contents:
                serializer = self.get_serializer(query).data
                if batch:
                    records = serializer.get('history')
                    for record in records:
                        if record['batch'] == batch:
                            serializer['history'] = record
                            break
                ret.append(serializer)
        return ret

    def list(self, request, *args, **kwargs):
        types = self.request.query_params.get('types')
        obj_id = self.request.query_params.get('id')
        batch = self.request.query_params.get('batch', None)
        handler = self.request.query_params.get('handler', None)
        task_id = self.request.query_params.get('task_id', None)
        if not handler:
            handler = None

        if not task_id:
            task_id = None

        query_set = None

        if types == 'cases':
            query_set = Cases.objects.filter(id=obj_id)

        elif types == 'sets':
            query_set = Sets.objects.filter(id=obj_id)

        elif types == 'tasks':
            query_set = Tasks.objects.filter(id=obj_id)

        elif types == 'set_cases' or types == 'task_cases':
            query_set = CasesRelationShip.objects.filter(sets_id=obj_id, handler=handler, tasks_id=task_id)

        elif types == 'task_sets':
            query_set = SetsRelationShip.objects.filter(tasks_id=obj_id)

        ret = self._filter_data(query_set, batch)

        if not batch and ret:
            ret = ret[0].get('history')

        return Response(ret)


class ReportViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ReportSerializer

    def get_queryset(self):
        queryset = Tasks.objects.all()
        project_name = self.request.query_params.get('project', None)
        if project_name:
            queryset = queryset.filter(project__name=project_name)
        return queryset

    @staticmethod
    def _get_result(types, contents):
        s_count = 0
        f_count = 0
        r_count = 0
        sets = []

        if not isinstance(contents, list):
            raise TypeError('input value is not list')

        for index, content in enumerate(contents):
            if types == 'all':
                if content.get('result', None) == 'Succeed':
                    s_count += 1
                elif content.get('result', None) == 'Failed':
                    f_count += 1
                elif content.get('result', None) is None:
                    r_count += 1
                else:
                    pass
                sets.append(content)
            elif types == 'succeed':
                if content.get('result', None) == 'Succeed':
                    s_count += 1
                    sets.append(content)
            elif types == 'failed':
                if content.get('result', None) == 'Failed':
                    f_count += 1
                    sets.append(content)
            elif types == 'running':
                if content.get('result', None) is None:
                    r_count += 1
                    sets.append(content)
        return s_count, f_count, r_count, sets

    def retrieve(self, request, *args, **kwargs):
        l_type = self.request.query_params.get('type')
        instance = self.get_object()
        serializer = self.get_serializer(instance).data
        records = serializer.get('history')
        s_count, f_count, r_count, sets = self._get_result(l_type, records)
        ret = {
                'success': s_count,
                'failed': f_count,
                'running': r_count,
                'sets': sets
        }
        return Response(ret, status=HTTP_200_OK)


class CronScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = CronScheduleSerializer
    pagination_class = CustomPagination
    permission_classes = [CRUDPermission]

    def get_queryset(self):
        queryset = CrontabSchedule.objects.all()
        project_name = self.request.query_params.get('project', None)
        if project_name:
            queryset = queryset.filter(project__name=project_name)

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_id = Projects.objects.get(name=data.get('project')).id
        data['project'] = project_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        data = request.data
        data['project'] = Projects.objects.get(name=data['project']).id
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PeriodicTaskViewSet(viewsets.ModelViewSet):
    serializer_class = PeriodicTaskSerializer
    pagination_class = CustomPagination
    permission_classes = [CRUDPermission]

    def get_queryset(self):
        queryset = PeriodicTask.objects.all()
        project_name = self.request.query_params.get('project', None)
        if project_name:
            queryset = queryset.filter(project__name=project_name)

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data
        project_id = Projects.objects.get(name=data.get('project')).id
        data['project'] = project_id
        data['task'] = 'services.tasks.periodic_task'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        data = request.data
        data['project'] = Projects.objects.get(name=data['project']).id
        data['task'] = 'services.tasks.periodic_task'
        data['args'] = json.dumps([data.get('tasks')])
        data['kwargs'] = json.dumps({'tags': data.get('tags'), 'category': data.get('category')})
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
