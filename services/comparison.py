class Comparison:
    @classmethod
    def execute(cls, comparison, source, target):
        assert comparison in ('equal', 'gt', 'lt', 'contains'), \
            "ValueError: the value of content must in ('equal', 'gt', 'lt', 'contains')"
        data = {
            'equal': cls.equal,
            'gt': cls.great_than,
            'lt': cls.less_than,
            'contains': cls.contains
        }
        data[comparison](source, target)

    @classmethod
    def equal(cls, source, target):
        assert source == target, "AssertionError {} != {}".format(source, target)

    @classmethod
    def less_than(cls, source, target):
        assert source < target, "AssertionError {} is not less than {}".format(source, target)

    @classmethod
    def great_than(cls, source, target):
        assert source > target, "AssertionError {} is not greater than {}".format(source, target)

    @classmethod
    def contains(cls, source, target):
        assert target in source, "AssertionError {} not in {}".format(target, source)
