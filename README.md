# kafka-rest-service


```bash
docker build -t kafka/rest-service .
```


```bash
docker run --rm -d \
    -v $(pwd)/src:/app \
    -v $(pwd)/appcfg:/appcfg \
    -p 8080:8080 \
    kafka/rest-service
```