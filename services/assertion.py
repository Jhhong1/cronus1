from services.extract import Extractor
from services.comparison import Comparison


class Asserts:
    @classmethod
    def asserts(cls, contents, **kwargs):
        """
        :param contents: object of request response
        :param kwargs:
        :return:
        """
        select = kwargs.get('select', None)
        if select == 'code':
            cls.assert_code(str(contents.status_code), **kwargs)
        elif select == 'text':
            cls.assert_text(contents.text, **kwargs)
        elif select == 'response_header':
            cls.assert_text(contents.headers, **kwargs)
        else:
            raise ValueError("The value of 'select' should be 'code'、'text' or 'response_header'")

    @classmethod
    def assert_code(cls, contents, **kwargs):
        Comparison.execute(comparison=kwargs.get('comparator'), source=contents, target=kwargs.get('expected_value'))

    @classmethod
    def assert_text(cls, contents, **kwargs):
        comparator = kwargs.get('comparator')
        if comparator == 'contains':
            Comparison.execute(comparison=comparator, source=contents, target=kwargs.get('expected_value'))
        elif comparator == 'equal':
            contents = Extractor.extractor(contents, **kwargs)
            Comparison.execute(comparison=comparator, source=contents, target=kwargs.get('expected_value'))
