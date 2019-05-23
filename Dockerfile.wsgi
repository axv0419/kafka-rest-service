FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN mkdir -p /tmp && mkdir -p /app
COPY ./requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

USER 1012