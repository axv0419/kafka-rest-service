# kafka-rest-service


```bash
docker build -t kafka/rest-service .
```


```bash
docker run --rm -d \
    -v $(pwd)/src:/app \
    -v $(pwd)/config:/config \
    -p 5000:5000 \
    kafka/rest-service
```