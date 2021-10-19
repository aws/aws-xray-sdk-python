### Set up the AWS X-Ray + Python Demo

1.  Build the image

    ```bash
    ./build.sh
    ```

1.  Validate your AWS Credentials

    Make sure your aws credentials are correct

    ```bash
    aws sts get-caller-identity
    ```

1.  Start the image

    ```bash
    ./start.sh
    ```

1.  Confirm the Application is Running

    ```bash
    docker ps | grep demo-xpy
    ```

### Run X-Ray Trace Demo

With the application running locally, you can run this command to fire off demo API calls. These API calls will show up in AWS X-Ray.

```bash
./run-xray-demo.sh
```

### View AWS X-Ray Data

Note: the links are set with **us-east-2** as the default AWS Region

- [Insights](https://us-east-2.console.aws.amazon.com/xray/home?region=us-east-2#/insights)
- [Service Map](https://us-east-2.console.aws.amazon.com/xray/home?region=us-east-2#/service-map)
- [Traces](https://us-east-2.console.aws.amazon.com/xray/home?region=us-east-2#/traces?timeRange=PT15M)
- [Analytics](https://us-east-2.console.aws.amazon.com/xray/home?region=us-east-2#/analytics?timeRange=PT5M)

#### Debugging

1.  Confirm AWS Identity

    ```bash
    docker exec -it demo-xpy aws sts get-caller-identity
    ```

1.  Review X-Ray Daemon logs

    **Tail**

    ```bash
    docker exec -it demo-xpy tail -f /tmp/xray.log
    ```

    **View**

    ```bash
    docker exec -it demo-xpy cat /tmp/xray.log
    ```
