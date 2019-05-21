# kafka-rest-service


```bash
docker build -t kafka/rest-service .
```


```bash
docker run --rm -d -p 5000:5000 -e REST_SERVICE_HOST_PORT=172.0.0.1:8082 kafka/rest-service

```