FROM python:3.13.7-alpine3.22

WORKDIR /app

RUN addgroup -S pipeline && adduser -S -G pipeline pipeline

COPY --chown=pipeline:pipeline scripts/ /app/scripts/

USER pipeline

ENTRYPOINT ["python", "/app/scripts/generator.py"]

