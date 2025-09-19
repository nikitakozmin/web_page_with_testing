FROM python:3.10-slim-bookworm

ENV TZ=Europe/Moscow

RUN apt-get update && apt-get install -y tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY tests/ /app/tests/
COPY requirements.txt /app/requirements.txt 

# Установка Python и библиотек
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt && \
    useradd -m -s /bin/bash tester && \
    chown -R tester:tester /app

USER tester
CMD ["pytest", "-v", "tests/", "--html=/app/reports/report.html", "--self-contained-html"]
