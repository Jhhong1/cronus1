import os
import json
import logging
import time
import uuid
from uuid import uuid5
from json.decoder import JSONDecodeError
from requests import Session
from django.utils import timezone
from cronus.settings import MEDIA_ROOT
from services.models import Config, Sets
from services.substitute import Parser
from services.assertion import Asserts
from services.extract import Extractor
from services.procedures import Procedures
from services.utils import remove_file, generate_uuid


logger = logging.getLogger()


class CasesRunner(object):
    class_variables = {}

    def __init__(self, instance, batch, level='cases', set_instance=None, order=None, config_instance=None,
                 handler=None, key=None, counter=None, task_id=None, category='api'):
        """
        :param instance: instance of test case, type(object)
        :param batch: run tasks or sets will generate id, which used to record the result of cases, type(string)
        :param level: level of cases, must be cases、sets or tasks, type(string)
        :param set_instance: instance of test sets, type(object)
        :param order: cases order in test sets, type(int)
        :param config_instance: instance of config, type(object)
        :param handler:  case's label in test sets, must be ''、setup or teardown, type(string)
        :param key: type(string)
        :param counter: type(dict)
        :param task_id: id of tasks , type(string)
        :param category: must be ui、api, type(string)
        """
        self.instance = instance
        self.batch = batch
        self.setInstance = set_instance
        self.orderNum = order
        self.config_instance = config_instance
        self.level = level
        self.handler = handler
        self.error = None
        self.status = None
        self.result = None
        self.key = key
        self.counter = counter
        self.task_id = task_id
        self.category = category
        self.start_time = timezone.now()
        self.ret = None
        self.image_name = None

        self._init_variables()
        self._get_relation_ship()

        if self.category == 'api':
            self._init_data()

    def _init_variables_api(self):
        self.proxy = []
        if not self.key:
            self.key = 'case'
            self.class_variables.setdefault(self.key, {})
            self.class_variables[self.key].setdefault('variables', {})
        if self.config_instance:
            self.class_variables[self.key]['base_url'] = self.config_instance.baseurl
            self.class_variables[self.key]['headers'] = self.config_instance.headers
            self.class_variables[self.key]['variables'].update(self.config_instance.variables)
            self.proxy = self.config_instance.proxy
        else:
            ret = Config.objects.filter(globalConfig=1, project=self.instance.project, category=self.category)
            if ret.exists():
                config = ret.first()
                self.class_variables[self.key]['base_url'] = config.baseurl
                self.class_variables[self.key]['headers'] = config.headers
                self.class_variables[self.key]['variables'].update(config.variables)
                self.proxy = config.proxy
        if self.counter:
            self.class_variables[self.key]['variables'].update(self.counter)

    def _init_variables_ui(self):
        if not self.key:
            self.key = 'case'
            Procedures.class_variables.setdefault(self.key, {})
            Procedures.class_variables[self.key].setdefault('variables', {})
        if self.config_instance:
            Procedures.class_variables[self.key]['variables'].update(self.config_instance.variables)
            self.proxy = self.config_instance.proxy
        else:
            ret = Config.objects.filter(globalConfig=1, project=self.instance.project, category=self.category)
            if ret.exists():
                config = ret.first()
                Procedures.class_variables[self.key]['variables'].update(config.variables)
                self.proxy = config.proxy

        self.proxies = {}
        for proxy in self.proxy:
            self.proxies[proxy.get('protocol')] = '{}:{}'.format(
                proxy.get('ip'), proxy.get('port'))

    def _init_variables(self):
        assert self.category in ('api', 'ui'), "category not in ('api', 'ui')"
        category = {
            'api': self._init_variables_api,
            'ui': self._init_variables_ui
        }
        category.get(self.category)()

    def _init_data(self):
        self.method = self.instance.method
        if self.instance.url.startswith(('http://', 'https://', '$')):
            self.url = self.instance.url
        else:
            self.url = self.class_variables.get(self.key).get('base_url') and '{}/{}'.format(
                self.class_variables.get(self.key).get('base_url').rstrip('/'), self.instance.url.lstrip('/')) \
                       or self.instance.url

        instance_variables = self.instance.variables
        if instance_variables:
            self.class_variables[self.key]['variables'].update(instance_variables)

        instance_headers = self.instance.headers
        if instance_headers:
            self.class_variables[self.key]['headers'].update(instance_headers)

        self.headers = self.class_variables.get(self.key).get('headers')
        self.variables = self.class_variables.get(self.key).get('variables')
        self.cycle = self.instance.cycle
        self.body = self.instance.body
        self.asserts = self.instance.asserts
        self.extracts = self.instance.extracts
        self.time_out = self.instance.waitingTime

    def _replace_variables_ui(self):
        variables = Procedures.class_variables[self.key]['variables']
        self.procedures = json.loads(Parser(self.instance.procedures, variables).parser())

    def _replace_variables_api(self):
        variable = self.class_variables[self.key]['variables']
        self.url = Parser(self.url, variable=variable).parser()
        self.headers = json.loads(Parser(self.headers, variable=variable).parser())
        self.body = Parser(self.body, variable=variable).parser()

    @staticmethod
    def _create_dir(file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)

    def _asserts(self, contents):
        error = ''
        for index, obj in enumerate(self.asserts):
            try:
                Asserts.asserts(contents, **obj)
            except Exception as e:
                self.error = "Failed reason: {}, response message: {}  {}".format(e, contents.status_code,
                                                                                  contents.text)
                error = "{};  {}".format(self.error, error)
                break

        if error:
            self.error = error
            self.result = "Failed"
        else:
            self.result = "Succeed"

    def _request(self):
        self._replace_variables_api()
        contents = {}

        if self.headers:
            contents['headers'] = self.headers

        if self.body:
            contents['data'] = self.body

        if self.time_out:
            contents['timeout'] = self.time_out

        if self.proxy:
            proxies = {}
            for proxy in self.proxy:
                scheme = proxy.get('scheme', '')
                protocol = proxy.get('protocol', '')
                username = proxy.get('username', '')
                port = proxy.get('port', '')
                ip = proxy.get('ip', '')
                password = proxy.get('password', '')
                proxies[protocol] = "{}://{}:{}@{}:{}".format(scheme, username, password, ip, port)
            contents['proxies'] = proxies

        contents['verify'] = False

        s = Session()

        logger.info('request url: {}, method: {}, {}'.format(self.url, self.method, contents))
        return s.request(method=self.method, url=self.url, **contents)

    def _extract_variable(self, contents):
        if self.result == "Succeed":
            for index, con in enumerate(self.extracts):
                content = ''
                if con.get('select') == 'text':
                    content = contents.text
                elif con.get('select') == 'response_header':
                    content = json.dumps(dict(contents.headers))
                elif con.get('select') == 'request_history':
                    ind = con.get('index')
                    content = contents.history[ind].text
                elif con.get('select') == 'request_url':
                    content = contents.url
                self.class_variables[self.key]['variables'][con.get('name')] = Extractor.extractor(content, **con)

    def _get_relation_ship(self):
        if self.level != 'cases':
            self.relation = self.instance.relations.get(sets_id=self.setInstance.id, tasks_id=self.task_id,
                                                        level=self.level, order=self.orderNum, handler=self.handler)

    def _record_result(self):
        ret = self.relation.history
        if ret.count() > 9:
            instance = ret.earliest('start_time')
            if instance.image:
                full_path = os.path.join(MEDIA_ROOT, str(instance.image))
                remove_file(full_path)
            instance.delete()
        self.relation.history.create(start_time=self.start_time, status='Starting', batch=self.batch)

    def _update_result(self, end_time, response=None, image=None):
        self.relation.history.filter(batch=self.batch).update(status=self.status, result=self.result,
                                                              error_message=self.error, end_time=end_time,
                                                              response=response, image=image)
        if self.error:
            raise Exception(self.error)

    def _save_screen_shot(self):
        driver = Procedures.class_variables[self.key]['driver']
        self.image_name = "{}{}{}".format('ui/', generate_uuid(), '.png')
        file_path = '{}/{}'.format(MEDIA_ROOT, self.image_name)
        logger.info("image path: {}".format(file_path))
        self._create_dir(os.path.dirname(file_path))
        driver.get_screenshot_as_file(file_path)
        driver.quit()

    def _response(self, response):
        ret = {}
        if response is not None:
            ret['status_code'] = response.status_code
            ret['headers'] = dict(response.headers)
            try:
                ret['text'] = response.json()
            except (JSONDecodeError, TypeError):
                ret['text'] = response.text
        if self.error:
            ret['error'] = self.error
        return ret

    def _run(self):
        if not self.cycle:
            self.cycle = 1

        while self.cycle:
            self.cycle -= 1
            try:
                self.ret = self._request()
                logger.info("response code: {}, response: {}".format(self.ret.status_code, self.ret.text))
            except Exception as e:
                logger.error("request failed: {}".format(e))
                self.error = repr(e)
                self.result = "Failed"
            else:
                # assert request result
                self._asserts(self.ret)
                if self.result == "Succeed":
                    self.error = None
                    break

    def run_api(self):
        if self.level != 'cases':
            self._record_result()

        self._run()

        if not self.error:
            try:
                self._extract_variable(self.ret)
            except Exception as e:
                self.error = "{}:  {}".format('extract variable failed', repr(e))
                self.result = "Failed"

        self.status = "Done"
        end_time = timezone.now()
        response = self._response(self.ret)

        if self.level == 'cases':
            self.instance.history.filter(batch=self.batch).update(status=self.status, result=self.result,
                                                                  error_message=self.error, end_time=end_time,
                                                                  response=response)
        else:
            self._update_result(end_time, response)

    def run_ui(self):
        self._replace_variables_ui()

        if self.level != 'cases':
            self._record_result()

        try:
            Procedures(self.procedures, self.key, self.proxies).parse()
        except Exception as e:
            logger.error(repr(e))
            self.error = repr(e)
            self.result = 'Failed'
            self._save_screen_shot()

        end_time = timezone.now()
        self.status = "Done"
        if not self.result:
            self.result = 'Succeed'

        if self.level == 'cases':
            self.instance.history.filter(batch=self.batch).update(status=self.status, result=self.result,
                                                                  error_message=self.error, end_time=end_time,
                                                                  image=self.image_name)

            driver = Procedures.class_variables[self.key]['driver']
            driver.quit()
        else:
            self._update_result(end_time, response=None, image=self.image_name)

    def run(self):
        assert self.category in ('api', 'ui'), "category not in ('api', 'ui')"
        category = {
            'api': self.run_api,
            'ui': self.run_ui
        }
        category.get(self.category)()


class SetsRunner(object):
    def __init__(self, set_id, batch, level='sets', task_id=None, counter=None, category='api'):
        """
        :param set_id: test set id, type(string)
        :param level: the level of test cases, type(string)
        :param task_id: test task id, type(string)
        :param counter: counter, type(dict)
        :param category: must be ui、api, type(string)
        """
        self.batch = batch
        self.set_id = set_id
        self.level = level
        self.task_id = task_id
        self.result = 'Succeed'
        self.error = None
        self.v_key = None
        self.counter = counter
        self.category = category
        self.start_time = timezone.now()
        self.setInstance = Sets.objects.get(pk=set_id)

        self._get_config()
        self._get_cases()
        self._get_relationship()

    def _get_config(self):
        result = self.setInstance.config
        if result.exists():
            self.config = result.first()
        else:
            self.config = Config.objects.filter(globalConfig=1, project=self.setInstance.project,
                                                category=self.category).first()

    def _get_cases(self):
        self.cases = self.setInstance.relations.filter(tasks_id=self.task_id, level=self.level,
                                                       handler=None).order_by('order')
        self.setup_cases = self.setInstance.relations.filter(tasks_id=self.task_id, level=self.level,
                                                             handler='setup').order_by('order')
        self.teardown_cases = self.setInstance.relations.filter(tasks_id=self.task_id, level=self.level,
                                                                handler='teardown').order_by('order')

    def _get_relationship(self):
        if self.level == 'tasks':
            self.relation = self.setInstance.relationship.get(tasks_id=self.task_id)

    def _generate_key(self):
        task_uuid = self.task_id or ''
        name = ''.join([self.set_id, self.level, task_uuid, str(time.time())])
        return str(uuid5(uuid.NAMESPACE_OID, name))

    def _setup(self):
        case_instance = None
        try:
            for setup in self.setup_cases:
                case_instance = setup.cases
                CasesRunner(case_instance, self.batch, level=self.level, set_instance=self.setInstance,
                            order=setup.order, config_instance=self.config, handler='setup', key=self.v_key,
                            counter=self.counter, task_id=self.task_id, category=self.category).run()
        except Exception as e:
            self.result = "Failed"
            self.error = 'setup: {} failed:{}; {}'.format(case_instance.name, e, self.error)
            logger.error('tasks: {}, sets: {}, setup: {}, failed: {}'.format(self.task_id, self.set_id,
                                                                             case_instance.name, e))
            raise Exception(self.error)

    def _teardown(self):
        for teardown in self.teardown_cases:
            case_instance = teardown.cases
            try:
                CasesRunner(case_instance, self.batch, level=self.level, set_instance=self.setInstance,
                            order=teardown.order, config_instance=self.config, handler='teardown', key=self.v_key,
                            counter=self.counter, task_id=self.task_id, category=self.category).run()
            except Exception as e:
                logger.error('tasks: {}, sets: {}, teardown: {}, failed: {}'.format(self.task_id, self.set_id,
                                                                                    case_instance.name, e))
                pass

    def _main(self):
        for case in self.cases:
            case_instance = case.cases
            try:
                CasesRunner(case_instance, self.batch, level=self.level, set_instance=self.setInstance,
                            order=case.order, config_instance=self.config, key=self.v_key, counter=self.counter,
                            task_id=self.task_id, category=self.category).run()
            except Exception as e:
                self.result = "Failed"
                self.error = '{} failed:{}; {}'.format(case_instance.name, e, self.error)
                logger.error('tasks: {}, sets: {}, case: {}, failed: {}'.format(self.task_id, self.set_id,
                                                                                case_instance.name, e))
        if self.error:
            raise Exception(self.error)

    def _record_result(self):
        ret = self.relation.history
        if ret.count() > 9:
            ret.earliest('start_time').delete()
        self.relation.history.create(start_time=self.start_time, status='Starting', batch=self.batch)

    def _update_result(self, status, end_time):
        self.relation.history.filter(batch=self.batch).update(status=status, result=self.result,
                                                              error_message=self.error, end_time=end_time)

    def run(self):
        self.v_key = self._generate_key()
        if self.category == 'api':
            CasesRunner.class_variables.setdefault(self.v_key, {})
            CasesRunner.class_variables[self.v_key].setdefault('variables', {})
        elif self.category == 'ui':
            Procedures.class_variables.setdefault(self.v_key, {})
            Procedures.class_variables[self.v_key].setdefault('variables', {})

        if self.level == 'tasks':
            self._record_result()

        try:
            self._setup()
        except Exception as e:
            # self.error = e
            self.error = repr(e)
        else:
            try:
                self._main()
            except Exception as e:
                self.error = repr(e)
        finally:
            self._teardown()
            if self.category == 'api':
                logger.info("global variables: {}".format(CasesRunner.class_variables))
                del CasesRunner.class_variables[self.v_key]
            elif self.category == 'ui':
                logger.info("global variables: {}".format(Procedures.class_variables))

                # Make sure WebDriver exits
                driver = Procedures.class_variables[self.v_key]['driver']
                driver.quit()

                del Procedures.class_variables[self.v_key]

            status = "Done"
            end_time = timezone.now()
            if self.level == 'sets':
                self.setInstance.history.filter(batch=self.batch).update(status=status, result=self.result,
                                                                         error_message=self.error, end_time=end_time)
            elif self.level == 'tasks':
                self._update_result(status, end_time)
                return self.error
