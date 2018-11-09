from aws_xray_sdk.core import xray_recorder


def mock_subfunc():
    pass


@xray_recorder.capture()
def mock_no_doublepatch():
    pass
