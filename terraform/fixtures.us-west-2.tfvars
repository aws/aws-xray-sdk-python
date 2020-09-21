region = "us-west-2"

bucket_name = "${var.resource_prefix}.eb.flask.applicationversion"

bucket_key = "beanstalk/deploy.zip"

source_path = "deploy.zip"

eb_app_name = "${var.resource_prefix}-EB-Flask-App"

eb_app_version_label = "${var.resource_prefix}-EB-Flask-App-1"

eb_env_name = "${var.resource_prefix}-EB-Flask-App-Env"

eb_env_cname_prefix = "${var.resource_prefix}-Eb-flask-app-env"
