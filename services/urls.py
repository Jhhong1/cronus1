from django.urls import path, include
from rest_framework.routers import DefaultRouter

from services.views import ProjectViewSet, ConfigViewSet, CounterViewSet, CasesViewSet, SetsViewSet, TasksViewSet, \
    CaseBindingViewSet, OrderViewSet, UnboundCaseViewSet, ConfigBindingViewSet, CounterBindingViewSet, \
    SetBindingViewSet, UnboundSetsViewSet, RunnerViewSet, HistoryViewSet, ReportViewSet, CronScheduleViewSet, \
    PeriodicTaskViewSet


router = DefaultRouter()
router.register('project', ProjectViewSet, basename='project')
router.register('config', ConfigViewSet, basename='config')
router.register('counter', CounterViewSet, basename='counter')
router.register('cases', CasesViewSet, basename='cases')
router.register('sets', SetsViewSet, basename='sets')
router.register('tasks', TasksViewSet, basename='tasks')
router.register('binding/cases', CaseBindingViewSet, basename='binding_cases')
router.register('ordering', OrderViewSet, basename='ordering')
router.register('unbound/cases', UnboundCaseViewSet, basename='unbound_cases')
router.register('binding/config', ConfigBindingViewSet, basename='binding_config')
router.register('binding/counter', CounterBindingViewSet, basename='binding_counter')
router.register('binding/sets', SetBindingViewSet, basename='binding_sets')
router.register('unbound/sets', UnboundSetsViewSet, basename='unbound_sets')
router.register('execute', RunnerViewSet, basename='execute')
router.register('history', HistoryViewSet, basename='history')
router.register('report', ReportViewSet, basename='report')
router.register('cron', CronScheduleViewSet, basename='cron')
router.register('periodic', PeriodicTaskViewSet, basename='periodic')


urlpatterns = [
    path('', include(router.urls)),
]