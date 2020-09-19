resource_prefix = "${{ github.run_id }}"

region = "us-west-2"

bucket_name = resource_prefix + "eb.flask.applicationversion"

bucket_key = "beanstalk/deploy.zip"

source_path = "deploy.zip"

eb_app_name = resource_prefix +"EB-Flask-App"

eb_app_version_label = resource_prefix + "EB-Flask-App-1"

eb_env_name = resource_prefix + "EB-Flask-App-Env"

eb_env_cname_prefix = resource_prefix + "Eb-flask-app-env"
