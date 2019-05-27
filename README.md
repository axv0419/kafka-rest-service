# kafka-rest-service


```bash
docker build -t kafka/rest-service .
```


```bash
docker run --rm  \
    --name k-rst-svc \
    -e CCLOUD_BROKER_URL=$CCLOUD_BROKER_URL \
    -e CCLOUD_API_KEY=$CCLOUD_API_KEY \
    -e CCLOUD_API_SECRET=$CCLOUD_API_SECRET \
    -v $(pwd)/app:/app \
    -v $(pwd)/static:/static \
    -v $(pwd)/appcfg:/appcfg \
    --entrypoint gunicorn \
    -p 7080:80 \
    kafka/rest-service -b 0.0.0.0:80 --workers=3 app.main
```