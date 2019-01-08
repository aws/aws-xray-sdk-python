from aws_xray_sdk.core import xray_recorder


def mock_subfunc():
    pass


@xray_recorder.capture()
def mock_no_doublepatch():
    pass


class MockClass(object):
    def __init__(self):
        pass

    def mock_method(self):
        pass

    @classmethod
    def mock_classmethod(cls):
        # Should not be automatically patched
        pass

    @staticmethod
    def mock_staticmethod():
        pass


class MockSubclass(MockClass):
    def __init__(self):
        super(MockSubclass, self).__init__()

    def mock_submethod(self):
        pass
