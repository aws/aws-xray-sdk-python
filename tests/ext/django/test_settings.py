try:
    from unittest import mock
except ImportError:
    import mock  # Python 2

import django
from aws_xray_sdk import global_sdk_config
from django.test import TestCase, override_settings
from django.conf import settings
from django.apps import apps

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.sampling.sampler import LocalSampler


class XRayConfigurationTestCase(TestCase):
    def test_sampler_can_be_configured(self):
        assert isinstance(settings.XRAY_RECORDER['SAMPLER'], LocalSampler)
        assert isinstance(xray_recorder.sampler, LocalSampler)
