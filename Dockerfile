FROM python:3.10.6-slim-buster
WORKDIR /website
COPY . .

RUN sed -i s@/deb.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN sed -i s@/security.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN apt-get update
RUN apt-get install poppler-utils -y
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

CMD ["bash", "-c", "\
    mkdir -p /website/upload/sign && \
    mkdir -p /website/upload/jpg && \
    mkdir -p /website/upload/pdf && \
    gunicorn start:app -c ./gunicorn.conf.py \
"]