=========
CHANGELOG
=========

2.4.2
==========
* bugfix: Fix exception processing in Django running in Lambda. `PR145 <https://github.com/aws/aws-xray-sdk-python/pull/145>`_.
* bugfix: Poller threads block main thread from exiting bug. `PR144 <https://github.com/aws/aws-xray-sdk-python/pull/144>`_.

2.4.1
==========
* bugfix: Middlewares should create subsegments only when in the Lambda context running under a Lambda environment. `PR139 <https://github.com/aws/aws-xray-sdk-python/pull/139>`_.

2.4.0
==========
* feature: Add ability to enable/disable the SDK. `PR119 <https://github.com/aws/aws-xray-sdk-python/pull/119>`_.
* feature: Add Serverless Framework Support `PR127 <https://github.com/aws/aws-xray-sdk-python/pull/127>`_.
* feature: Bring aiobotocore support back. `PR125 <https://github.com/aws/aws-xray-sdk-python/pull/125>`_.
* bugfix: Fix httplib invalid scheme detection for HTTPS. `PR122 <https://github.com/aws/aws-xray-sdk-python/pull/122>`_.
* bugfix: Max_trace_back = 0 returns full exception stack trace bug fix. `PR123 <https://github.com/aws/aws-xray-sdk-python/pull/123>`_.
* bugfix: Rename incorrect config module name to the correct global name. `PR130 <https://github.com/aws/aws-xray-sdk-python/pull/130>`_.
* bugfix: Correctly remove password component from SQLAlchemy URLs, preventing... `PR132 <https://github.com/aws/aws-xray-sdk-python/pull/132>`_.

2.3.0
==========
* feature: Stream Django ORM SQL queries and add flag to toggle their streaming. `PR111 <https://github.com/aws/aws-xray-sdk-python/pull/111>`_.
* feature: Recursively patch any given module functions with capture. `PR113 <https://github.com/aws/aws-xray-sdk-python/pull/113>`_.
* feature: Add patch support for pg8000 (Pure Python Driver). `PR115 <https://github.com/aws/aws-xray-sdk-python/pull/115>`_.
* improvement: Remove the dependency on Requests. `PR112 <https://github.com/aws/aws-xray-sdk-python/pull/112>`_.
* bugfix: Fix psycop2 register type. `PR95 <https://github.com/aws/aws-xray-sdk-python/pull/95>`_.

2.2.0
=====
* feature: Added context managers on segment/subsegment capture. `PR97 <https://github.com/aws/aws-xray-sdk-python/pull/97>`_.
* feature: Added AWS SNS topic ARN to the default whitelist file. `PR93 <https://github.com/aws/aws-xray-sdk-python/pull/93>`_.
* bugfix: Fixed an issue on `psycopg2` to support all keywords. `PR91 <https://github.com/aws/aws-xray-sdk-python/pull/91>`_.
* bugfix: Fixed an issue on `endSegment` when there is context missing. `ISSUE98 <https://github.com/aws/aws-xray-sdk-python/issues/98>`_.
* bugfix: Fixed the package description rendered on PyPI. `PR101 <https://github.com/aws/aws-xray-sdk-python/pull/101>`_.
* bugfix: Fixed an issue where `patch_all` could patch the same module multiple times. `ISSUE99 <https://github.com/aws/aws-xray-sdk-python/issues/99>`_.
* bugfix: Fixed the `datetime` to `epoch` conversion on Windows OS. `ISSUE103 <https://github.com/aws/aws-xray-sdk-python/issues/103>`_.
* bugfix: Fixed a wrong segment json key where it should be `sampling_rule_name` rather than `rule_name`.

2.1.0
=====
* feature: Added support for `psycopg2`. `PR83 <https://github.com/aws/aws-xray-sdk-python/pull/83>`_.
* feature: Added support for `pynamodb` >= 3.3.1. `PR88 <https://github.com/aws/aws-xray-sdk-python/pull/88>`_.
* improvement: Improved stack trace recording when exception is thrown in decorators. `PR70 <https://github.com/aws/aws-xray-sdk-python/pull/70>`_.
* bugfix: Argument `sampling_req` in LocalSampler `should_trace` method now becomes optional. `PR89 <https://github.com/aws/aws-xray-sdk-python/pull/89>`_.
* bugfix: Fixed a wrong test setup and leftover poller threads in recorder unit test.

2.0.1
=====
* bugfix: Fixed a issue where manually `begin_segment` might break when making sampling decisions. `PR82 <https://github.com/aws/aws-xray-sdk-python/pull/82>`_.

2.0.0
=====
* **Breaking**: The default sampler now launches background tasks to poll sampling rules from X-Ray backend. See the new default sampling strategy in more details here: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-python-configuration.html#xray-sdk-python-configuration-sampling.
* **Breaking**: The `should_trace` function in the sampler now takes a dictionary for sampling rule matching.
* **Breaking**: The original sampling modules for local defined rules are moved from `models.sampling` to `models.sampling.local`.
* **Breaking**: The default behavior of `patch_all` changed to selectively patches libraries to avoid double patching. You can use `patch_all(double_patch=True)` to force it to patch ALL supported libraries. See more details on `ISSUE63 <https://github.com/aws/aws-xray-sdk-python/issues/63>`_
* **Breaking**: The latest `botocore` that has new X-Ray service API `GetSamplingRules` and `GetSamplingTargets` are required.
* **Breaking**: Version 2.x doesn't support pynamodb and aiobotocore as it requires botocore >= 1.11.3 which isn’t currently supported by the pynamodb and aiobotocore libraries. Please continue to use version 1.x if you’re using pynamodb or aiobotocore until those haven been updated to use botocore > = 1.11.3.
* feature: Environment variable `AWS_XRAY_DAEMON_ADDRESS` now takes an additional notation in `tcp:127.0.0.1:2000 udp:127.0.0.2:2001` to set TCP and UDP destination separately. By default it assumes a X-Ray daemon listening to both UDP and TCP traffic on `127.0.0.1:2000`.
* feature: Added MongoDB python client support. `PR65 <https://github.com/aws/aws-xray-sdk-python/pull/65>`_.
* bugfix: Support binding connection in sqlalchemy as well as engine. `PR78 <https://github.com/aws/aws-xray-sdk-python/pull/78>`_.
* bugfix: Flask middleware safe request teardown. `ISSUE75 <https://github.com/aws/aws-xray-sdk-python/issues/75>`_.


1.1.2
=====
* bugfix: Fixed an issue on PynamoDB patcher where the capture didn't handle client timeout.

1.1.1
=====
* bugfix: Handle Aiohttp Exceptions as valid responses `PR59 <https://github.com/aws/aws-xray-sdk-python/pull/59>`_.

1.1
===
* feature: Added Sqlalchemy parameterized query capture. `PR34 <https://github.com/aws/aws-xray-sdk-python/pull/34>`_
* bugfix: Allow standalone sqlalchemy integrations without flask_sqlalchemy. `PR53 <https://github.com/aws/aws-xray-sdk-python/pull/53>`_
* bugfix: Give up aiohttp client tracing when there is no open segment and LOG_ERROR is configured. `PR58 <https://github.com/aws/aws-xray-sdk-python/pull/58>`_
* bugfix: Handle missing subsegment when rendering a Django template. `PR54 <https://github.com/aws/aws-xray-sdk-python/pull/54>`_
* Typo fixes on comments and docs.

1.0
===
* Changed development status to `5 - Production/Stable` and removed beta tag.
* feature: Added S3 API parameters to the default whitelist.
* feature: Added new recorder APIs to add annotations/metadata.
* feature: The recorder now adds more runtime and version information to sampled segments.
* feature: Django, Flask and Aiohttp middleware now inject trace header to response headers.
* feature: Added a new API to configure maximum captured stack trace.
* feature: Modularized subsegments streaming logic and now it can be overriden with custom implementation.
* bugfix(**Breaking**): Subsegment `set_user` API is removed since this attribute is not supported by X-Ray back-end.
* bugfix: Fixed an issue where arbitrary fields in trace header being dropped when calling downstream.
* bugfix: Fixed a compatibility issue between botocore and httplib patcher. `ISSUE48 <https://github.com/aws/aws-xray-sdk-python/issues/48>`_.
* bugfix: Fixed a typo in sqlalchemy decorators. `PR50 <https://github.com/aws/aws-xray-sdk-python/pull/50>`_.
* Updated `README` with more usage examples.

0.97
====
* feature: Support aiohttp client tracing for aiohttp 3.x. `PR42 <https://github.com/aws/aws-xray-sdk-python/pull/42>`_.
* feature: Use the official middleware pattern for Aiohttp ext. `PR29 <https://github.com/aws/aws-xray-sdk-python/pull/29>`_.
* bugfix: Aiohttp middleware serialized URL values incorrectly. `PR37 <https://github.com/aws/aws-xray-sdk-python/pull/37>`_
* bugfix: Don't overwrite plugins list on each `.configure` call. `PR38 <https://github.com/aws/aws-xray-sdk-python/pull/38>`_
* bugfix: Do not swallow `return_value` when context is missing and `LOG_ERROR` is set. `PR44 <https://github.com/aws/aws-xray-sdk-python/pull/44>`_
* bugfix: Loose entity name validation. `ISSUE36 <https://github.com/aws/aws-xray-sdk-python/issues/36>`_
* bugfix: Fix PyPI project page being rendered incorrectly. `ISSUE30 <https://github.com/aws/aws-xray-sdk-python/issues/30>`_

0.96
====
* feature: Add support for SQLAlchemy and Flask-SQLAlcemy. `PR14 <https://github.com/aws/aws-xray-sdk-python/pull/14>`_.
* feature: Add support for PynamoDB calls to DynamoDB. `PR13 <https://github.com/aws/aws-xray-sdk-python/pull/13>`_.
* feature: Add support for httplib calls. `PR19 <https://github.com/aws/aws-xray-sdk-python/pull/19>`_.
* feature: Make streaming threshold configurable through public interface. `ISSUE21 <https://github.com/aws/aws-xray-sdk-python/issues/21>`_.
* bugfix:  Drop invalid annotation keys and log a warning. `PR22 <https://github.com/aws/aws-xray-sdk-python/pull/22>`_.
* bugfix:  Respect `with` statement on cursor objects in dbapi2 patcher. `PR17 <https://github.com/aws/aws-xray-sdk-python/pull/17>`_.
* bugfix:  Don't throw error from built in subsegment capture when `LOG_ERROR` is set. `ISSUE4 <https://github.com/aws/aws-xray-sdk-python/issues/4>`_.

0.95
====
* **Breaking**: AWS API parameter whitelist json file is moved to path `aws_xray_sdk/ext/resources/aws_para_whitelist.json` in `PR6 <https://github.com/aws/aws-xray-sdk-python/pull/6>`_.
* Added aiobotocore/aioboto3 support and async function capture. `PR6 <https://github.com/aws/aws-xray-sdk-python/pull/6>`_
* Added logic to removing segment/subsegment name invalid characters. `PR9 <https://github.com/aws/aws-xray-sdk-python/pull/9>`_
* Temporarily disabled tests run on Django2.0. `PR10 <https://github.com/aws/aws-xray-sdk-python/pull/10>`_
* Code cleanup. `PR11 <https://github.com/aws/aws-xray-sdk-python/pull/11>`_

0.94
====
* Added aiohttp support. `PR3 <https://github.com/aws/aws-xray-sdk-python/pull/3>`_

0.93
====
* The X-Ray SDK for Python is now an open source project. You can follow the project and submit issues and pull requests on GitHub: https://github.com/aws/aws-xray-sdk-python

0.92.2
======
* bugfix: Fixed an issue that caused the X-Ray recorder to omit the origin when recording segments with a service plugin. This caused the service's type to not appear on the service map in the X-Ray console.

0.92.1
======
* bugfix: Fixed an issue that caused all calls to Amazon DynamoDB tables to be grouped under a single node in the service map. With this update, each table gets a separate node.

0.92
====

* feature: Add Flask support
* feature: Add dynamic naming on segment name

0.91.1
======

* bugfix: The SDK has been released as a universal wheel
