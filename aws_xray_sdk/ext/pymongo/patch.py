from pymongo import monitoring
from aws_xray_sdk.core import xray_recorder


class XrayCommandListener(monitoring.CommandListener):
    """
    A listener that traces all pymongo db commands to AWS Xray.
    Creates a subsegment for each mongo db conmmand.

    name: 'pymongo-127.0.0.1:27017'
    annotations: command_name:str, database_name: str, succeed: bool
    """

    def started(self, event):
        host, port = event.connection_id
        subsegment = xray_recorder.begin_subsegment(
            f'MongoDB-{host}:{port}', 'remote')
        subsegment.put_annotation('command_name', event.command_name)
        subsegment.put_annotation('database_name', event.database_name)

    def succeeded(self, event):
        xray_recorder.end_subsegment()

    def failed(self, event):
        subsegment = xray_recorder.current_subsegment()
        subsegment.add_fault_flag()
        subsegment.put_metadata('failure', event.failure)
        xray_recorder.end_subsegment()


def patch():
    # ensure `patch()` is idempotent
    if hasattr(monitoring, '_xray_enabled'):
        return
    setattr(monitoring, '_xray_enabled', True)
    monitoring.register(XrayCommandListener())
