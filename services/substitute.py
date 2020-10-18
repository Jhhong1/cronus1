import string
import json


class Parser(object):
    def __init__(self, target, variable=None):
        """
        :param target: json format
        :param variable: dict
        """
        self.target = target
        self.variable = variable

    def parser(self):
        """
        Replace variables in strings
        :return string
        """
        if isinstance(self.target, (list, dict)):
            self.target = json.dumps(self.target)
        template = string.Template(self.target)
        return template.safe_substitute(self.variable)
