import re
import json
import logging

from services.exceptions import ParseResponseErr


logger = logging.getLogger()


class Extractor:
    @classmethod
    def extractor(cls, contents, **kwargs):
        assert isinstance(contents, str), "ValueError: The type of content is not string"

        match_type = kwargs.get('match_type')
        if match_type == 'regular':
            return cls.regular_extractor(contents, **kwargs)
        elif match_type == 'json':
            contents = json.loads(contents)
            return cls.json_path_extractor(contents, **kwargs)
        else:
            raise TypeError("The value of match_type should be 'regular' or 'json', but '{}'".format(match_type))

    @classmethod
    def regular_extractor(cls, str_content, **kwargs):
        list_item = kwargs.get('group', '')
        tuple_item = kwargs.get('match_no', '')

        pattern = re.compile(kwargs.get('expression'))
        result = pattern.findall(str_content)
        logger.info("regular match result: {}".format(result))

        if list_item.isdigit() and tuple_item.isdigit():
            return result[int(list_item)][int(tuple_item)]
        elif list_item.isdigit() and not tuple_item:
            return result[int(list_item)]
        else:
            return result

    @classmethod
    def json_path_extractor(cls, json_content, **kwargs):
        """
        Do an xpath-like query with json_content.
        @param (json_content) json_content
            json_content = {
                "ids": [1, 2, 3, 4],
                "person": {
                    "name": {
                        "first_name": "Leo",
                        "last_name": "Lee",
                    },
                    "age": 29,
                    "cities": ["Guangzhou", "Nanjing"]
                }
            }
        @param (str) query
            "person.name.first_name"  =>  "Leo"
            "person.cities.0"         =>  "Guangzhou"
        @return queried result
        """
        assert isinstance(json_content, (list, dict)), "TypeError: The type of content is not a list or dict"
        keys = cls.parser_extractor(kwargs.get('expression'))
        try:
            for key in keys:
                if isinstance(json_content, list):
                    json_content = json_content[int(key)]
                elif isinstance(json_content, dict):
                    json_content = json_content[key]
                else:
                    raise ParseResponseErr("response content is in text format! failed to query key {}!".format(key))
        except (KeyError, ValueError, IndexError):
            raise ParseResponseErr("failed to query json when extracting response! response: {}".format(json_content))
        logger.info("json match result: {}".format(json_content))
        return json_content

    @classmethod
    def parser_extractor(cls, expression):
        """
        Extract expected values from expressions
        :param expression:
        :return: list of value
        """
        full_pattern = re.compile(r'^\$\.(\[[\w.\-/]+\])+')
        pattern = re.compile(r'[\w.\-/]+')
        msg = "expression format error, the format is '$.(\[[\w.\-/]+\])+'"
        assert re.match(full_pattern, expression), msg
        con = expression.split('$.')[1]
        assert re.match(r'([[\w.\-/]+])+', con), msg
        return pattern.findall(con)
