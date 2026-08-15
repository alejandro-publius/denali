FROM python:3.12-slim

RUN pip install --no-cache-dir pandas==3.0.5 numpy==2.5.2

WORKDIR /app
# Measurability features only. The screen's results are not in this image --
# they live with the verifier, so the answer cannot be read out of the task.
COPY data/ /app/data/

RUN mkdir -p /logs/verifier /logs/agent /logs/artifacts
