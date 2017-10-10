from aws_xray_sdk.core.plugins.utils import get_plugin_modules

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
