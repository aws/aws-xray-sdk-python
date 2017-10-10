.. _thirdparty:

Third Party Library Support
===========================

The SDK supports boto3, botocore, requests, sqlite3 and mysql-connector.

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
        'boto3',
        'botocore',
        'requests',
        'sqlite3',
        'mysql',
    )

Patching boto3 and botocore are equivalent since boto3 depends on botocore

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
