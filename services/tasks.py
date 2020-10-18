from __future__ import absolute_import, unicode_literals

import os
from itertools import cycle
from rest_framework import serializers
from django.utils import timezone
from celery import shared_task, chord
from celery.utils.log import get_task_logger
from cronus.settings import MEDIA_ROOT
from services.utils import remove_file, generate_uuid
from services.models import Tasks, Cases, Sets, Histories
from services.runner import CasesRunner, SetsRunner

logger = get_task_logger(__name__)


@shared_task
def bound_set_to_task(task_id):
    task_instance = Tasks.objects.get(pk=task_id)
    sets = task_instance.sets_set.iterator()
    for test_set in sets:
        qs = test_set.relations.filter(level='sets')
        for queryset in qs:
            task_instance.relations.create(order=queryset.order, level='tasks', handler=queryset.handler,
                                           cases=queryset.cases, sets=queryset.sets)


@shared_task
def bound_cases_to_set(set_id, handler, cases):
    set_instance = Sets.objects.get(id=set_id)
    tasks = set_instance.tasks.iterator()
    relations = [set_instance.relations.filter(level='sets', handler=handler, cases_id=case.get('id'))
                 for case in cases]
    for task in tasks:
        for test_cases in relations:
            for test_case in test_cases:
                if not task.relations.filter(sets=set_instance, cases=test_case.cases, order=test_case.order,
                                             level='tasks', handler=test_case.handler).exists():
                    task.relations.create(sets=set_instance, cases=test_case.cases, order=test_case.order,
                                          level='tasks', handler=test_case.handler)


class Start(object):

    def __init__(self, obj_id, level, batch):
        self.id = obj_id
        self.batch = batch
        self.level = level
        self.start_time = timezone.now()

    @staticmethod
    def _remove_file(instance):
        image = instance.image
        if image:
            file_path = os.path.join(MEDIA_ROOT, str(image))
            remove_file(file_path)

    def _set_status(self, instance, start_time=None, status=None, batch=None):
        ret = instance.history
        if ret.count() > 9:
            obj = ret.earliest('start_time')
            self._remove_file(obj)
            obj.delete()
        instance.history.create(start_time=start_time, status=status, batch=batch)

    def run(self):
        if self.level == 'cases':
            instance = Cases.objects.get(id=self.id)
            ret = instance.history.filter(status='Starting').exists()
        elif self.level == 'sets':
            instance = Sets.objects.get(id=self.id)
            ret = instance.history.filter(status='Starting').exists()
        else:
            instance = Tasks.objects.get(id=self.id)
            ret = instance.history.filter(status='Starting').exists()

        if ret:
            raise serializers.ValidationError('task: %s already running' % self.id)

        self._set_status(instance, start_time=self.start_time, status='Starting', batch=self.batch)


@shared_task
def run_case(case_id, batch, category):
    instance = Cases.objects.get(pk=case_id)
    CasesRunner(instance, batch, category=category).run()


@shared_task
def run_set(set_id, batch, category=None, level='sets', task_id=None, counter=None):
    logger.info("run test set, test set: {}, batch: {}, level: {}, task id: {}, counter: {}".format(set_id, batch,
                                                                                                    level, task_id,
                                                                                                    counter))
    return SetsRunner(set_id, batch, level=level, task_id=task_id, counter=counter, category=category).run()


@shared_task
def save_task_result(info, task_id, batch):
    result = 'Succeed'
    status = 'Done'

    error_msg = ''

    logger.info("test set results: {}".format(info))

    for errors in info:
        if errors:
            error_msg = '{}; {}'.format(errors, error_msg)
    if error_msg:
        result = 'Failed'

    end_time = timezone.now()
    Histories.objects.filter(tasks_id=task_id, batch=batch).update(status=status, result=result,
                                                                   error_message=error_msg, end_time=end_time)


@shared_task
def run_task(task_id, batch, tags, category):
    queryset = Sets.objects.filter(tasks__id=task_id)
    if not tags:
        test_sets = queryset.filter(tags__contains=[])
    elif tags == 'all':
        test_sets = queryset
    else:
        test_sets = queryset.filter(tags__contains=tags)

    instance = Tasks.objects.get(id=task_id)
    ret = instance.counters
    if ret.exists():
        counter = ret.first()
        num_generator = (i for i in range(counter.initial, counter.final, counter.step))
        num = cycle(num_generator)

        chord((run_set.s(testSet.id, batch, category, 'tasks', task_id,
                         {counter.name: str(next(num))})
               for testSet in test_sets),
              save_task_result.s(task_id, batch).set(retry_policy={
                  'interval_step': 1,
                  'interval_max': 2
              }))()
    else:
        chord((run_set.s(testSet.id, batch, category, 'tasks', task_id)
               for testSet in test_sets),
              save_task_result.s(task_id, batch).set(retry_policy={
                  'interval_step': 1,
                  'interval_max': 2
              }))()


def run(level, obj_id, batch, tags=None, category=None):
    if level == 'cases':
        run_case.apply_async((obj_id, batch, category))
    elif level == 'sets':
        run_set.apply_async((obj_id, batch, category))
    elif level == 'tasks':
        run_task.apply_async((obj_id, batch, tags, category))


@shared_task
def periodic_task(task_id, tags=None, category=None):
    logger.info("periodic task, args: {} {}".format(task_id, tags))
    batch = generate_uuid()
    Start(task_id, 'tasks', batch).run()
    run('tasks', task_id, batch, tags, category)
