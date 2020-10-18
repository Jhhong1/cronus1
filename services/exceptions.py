class ResponseError(BaseException):
    pass


class ExtractorFormatErr(BaseException):
    pass


class ParseResponseErr(BaseException):
    pass


class RunTestSetError(BaseException):
    pass


class FindElementFailedException(Exception):
    pass
