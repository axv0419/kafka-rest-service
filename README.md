# kafka-rest-service


```bash
docker build -t kafka/rest-service .
```


```bash
docker run --rm -d -V ./src:/app -p 5000:5000 -e REST_SERVICE_HOST_PORT=172.26.0.6:8082 kafka/rest-service

```