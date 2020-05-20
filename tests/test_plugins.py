from aws_xray_sdk.core.plugins.utils import get_plugin_modules
from unittest.mock import patch

supported_plugins = (
    'ec2_plugin',
    'ecs_plugin',
    'elasticbeanstalk_plugin',
)


def test_runtime_context_available():
    plugins = get_plugin_modules(supported_plugins)

    for plugin in plugins:
        plugin.initialize()
        assert hasattr(plugin, 'runtime_context')


@patch('urllib.request.urlopen')
def test_ec2_plugin(mock_urlopen):
    # set up mock response
    mock_urlopen.return_value.read.return_value.decode.side_effect = ['token', 'i-0a1d026d92d4709cd', 'us-west-2b',
                                                                      Exception("Boom!"), 'i-0a1d026d92d4709ab',
                                                                      'us-west-2a',
                                                                      Exception("Boom v2!"), Exception("Boom v1!")]

    ec2_plugin = get_plugin_modules(('ec2_plugin',))
    for plugin in ec2_plugin:
        # for IMDSv2 success
        plugin.initialize()
        assert hasattr(plugin, 'runtime_context')
        r_c = getattr(plugin, 'runtime_context')
        assert r_c['instance_id'] == 'i-0a1d026d92d4709cd'
        assert r_c['availability_zone'] == 'us-west-2b'

        # for IMDSv2 fail and IMDSv1 success
        plugin.initialize()
        assert hasattr(plugin, 'runtime_context')
        r_c = getattr(plugin, 'runtime_context')
        assert r_c['instance_id'] == 'i-0a1d026d92d4709ab'
        assert r_c['availability_zone'] == 'us-west-2a'

        # for both failure
        plugin.initialize()
        assert hasattr(plugin, 'runtime_context')
        r_c = getattr(plugin, 'runtime_context')
        assert r_c is None
