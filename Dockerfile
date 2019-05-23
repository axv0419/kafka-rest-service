FROM python:3.6


RUN mkdir -p /tmp && mkdir -p /app
COPY ./requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
WORKDIR /app

CMD ["gunicorn", "-b", "0.0.0.0:80", "app.main"]
