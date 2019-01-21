import os
import aws_xray_sdk.core


class InvalidParameterTypeException(Exception):
    """
    Exception thrown when an invalid parameter is passed into SDKConfig.set_sdk_enabled.
    """
    pass


class SDKConfig(object):
    """
    Global Configuration Class that defines SDK-level configuration properties.
    It is recommended to only use the recorder to set this configuration's enabled
    flag to maintain thread safety.
    """
    XRAY_ENABLED_KEY = 'AWS_XRAY_SDK_ENABLED'
    __SDK_ENABLED = str(os.getenv(XRAY_ENABLED_KEY, 'true')).lower() != 'false'

    @classmethod
    def sdk_enabled(cls):
        """
        Returns whether the SDK is enabled or not.
        """
        return cls.__SDK_ENABLED

    @classmethod
    def set_sdk_enabled(cls, value):
        """
        Modifies the enabled flag if the "AWS_XRAY_ENABLED" environment variable is not set,
        otherwise, set the enabled flag to be equal to the environment variable. If the
        env variable is an invalid string boolean, it will default to true.

        :param bool value: Flag to set whether the SDK is enabled or disabled.

        Environment variables AWS_XRAY_ENABLED overrides argument value.
        """
        # Environment Variables take precedence over hardcoded configurations.
        if cls.XRAY_ENABLED_KEY in os.environ:
            cls.__SDK_ENABLED = str(os.getenv(cls.XRAY_ENABLED_KEY, 'true')).lower() != 'false'
        else:
            if type(value) == bool:
                cls.__SDK_ENABLED = value
            else:
                cls.__SDK_ENABLED = True
                raise InvalidParameterTypeException(
                    "Invalid parameter type passed into set_sdk_enabled(). Defaulting to True..."
                )

        # Modify all key paths.
        aws_xray_sdk.core.xray_recorder.configure(enabled=cls.__SDK_ENABLED)
