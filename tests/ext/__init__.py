from aws_xray_sdk.core import xray_recorder
from ..util import StubbedEmitter


xray_recorder.configure(sampling=False)
xray_recorder.emitter = StubbedEmitter()
