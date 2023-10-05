.. _thirdparty:

Third Party Library Support
===========================

Patching Supported Libraries
----------------------------

The X-Ray Python SDK supports patching aioboto3, aiobotocore, boto3, botocore, pynamodb, requests, 
sqlite3, mysql, httplib, pymongo, pymysql, psycopg2, pg8000, sqlalchemy_core, httpx, and mysql-connector.

To patch, use code like the following in the main app::

    from aws_xray_sdk.core import patch_all

    patch_all()

``patch_all`` ignores any libraries that are not installed.

To patch specific modules::

    from aws_xray_sdk.core import patch

    i_want_to_patch = ('botocore') # a tuple that contains the libs you want to patch
    patch(i_want_to_patch)

The following modules are availble to patch::

    SUPPORTED_MODULES = (
        'aioboto3',
        'aiobotocore',
        'boto3',
        'botocore',
        'pynamodb',
        'requests',
        'sqlite3',
        'mysql',
        'httplib',
        'pymongo',
        'pymysql',
        'psycopg2',
        'pg8000',
        'sqlalchemy_core',
        'httpx',
    )

Patching boto3 and botocore are equivalent since boto3 depends on botocore.

Patching pynamodb applies the botocore patch as well, as it uses the logic from the botocore
patch to apply the trace header.

Patching mysql
----------------------------

For mysql, only the mysql-connector module is supported and you have to use
code like the following to generate a subsegment for an SQL query::

    def call_mysql():
        conn = mysql.connector.connect(
            host='host',
            port='some_port',
            user='some_user',
            password='your_password',
            database='your_db_name'
        )

        conn.cursor().execute('SHOW TABLES')

Patching aioboto3 and aiobotocore
---------------------------------

On top of patching aioboto3 or aiobotocore, the xray_recorder also needs to be
configured to use the ``AsyncContext``. The following snippet shows how to set
up the X-Ray SDK with an Async Context, bear in mind this requires Python 3.5+::

    from aws_xray_sdk.core.async_context import AsyncContext
    from aws_xray_sdk.core import xray_recorder
    # Configure X-Ray to use AsyncContext
    xray_recorder.configure(service='service_name', context=AsyncContext())

See :ref:`Configure Global Recorder <configurations>` for more information about
configuring the ``xray_recorder``.

Patching httplib
----------------

httplib is a low-level python module which is used by several third party modules, so
by enabling patching to this module you can gain patching of many modules "for free."
Some examples of modules that depend on httplib: requests and httplib2
