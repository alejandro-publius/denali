FROM python:3.12-slim

RUN pip install --no-cache-dir pandas==3.0.5 numpy==2.5.2 scipy==1.18.0

WORKDIR /app
# Seven real published enrichment tables plus the pinned top-10 ranking for each.
# The size-aware residual that defines the answer lives with the verifier,
# outside this image, so which entries are size-carried cannot be read out of
# the task.
COPY data/ /app/data/

RUN mkdir -p /logs/verifier /logs/agent /logs/artifacts
