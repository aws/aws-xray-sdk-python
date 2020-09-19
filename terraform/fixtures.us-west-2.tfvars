region = "us-west-2"

bucket_name = "${{ github.run_id }}" + "eb.flask.applicationversion"

bucket_key = "beanstalk/deploy.zip"

source_path = "deploy.zip"

eb_app_name = "${{ github.run_id }}" + "EB-Flask-App"

eb_app_version_label = "${{ github.run_id }}" + "EB-Flask-App-1"

eb_env_name = "${{ github.run_id }}" + "EB-Flask-App-Env"

eb_env_cname_prefix = "${{ github.run_id }}" + "Eb-flask-app-env"
