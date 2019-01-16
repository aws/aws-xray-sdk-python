import os


class SDKConfig(object):
    """
    Global Configuration Class that defines SDK-level configuration properties.
    It is recommended to only use the recorder to set this configuration's enabled
    flag to maintain thread safety.
    """
    XRAY_ENABLED_KEY = 'AWS_XRAY_ENABLED'
    __SDK_ENABLED = str(os.getenv(XRAY_ENABLED_KEY, 'true')).lower() != 'false'

    @staticmethod
    def sdk_enabled():
        """
        Returns whether the SDK is enabled or not.
        """
        return SDKConfig.__SDK_ENABLED

    @staticmethod
    def set_sdk_enabled(value):
        """
        Modifies the enabled flag if the "AWS_XRAY_ENABLED" environment variable is not set,
        otherwise, set the enabled flag to be equal to the environment variable. If the
        env variable is an invalid string boolean, it will default to true.

        :param bool value: Flag to set whether the SDK is enabled or disabled.

        Environment variables AWS_XRAY_ENABLED overrides argument value.
        """
        # Environment Variables take precedence over hardcoded configurations.
        if SDKConfig.XRAY_ENABLED_KEY in os.environ:
            SDKConfig.__SDK_ENABLED = str(os.getenv(SDKConfig.XRAY_ENABLED_KEY, 'true')).lower() != 'false'
        else:
            SDKConfig.__SDK_ENABLED = value
