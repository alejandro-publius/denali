FROM python:3.12-slim

# numpy and pandas only. The scorer does not import scipy: the rank correlation
# is `denali_audit.core._spearman`, the shipped scipy-free implementation, which is
# the same function that produced the study's published 0.6633. Adding scipy here
# would let a second definition of Spearman into the scoring path.
RUN pip install --no-cache-dir pandas==3.0.5 numpy==2.5.2

WORKDIR /app

# The published input half, the scorer, and the two frozen files it derives truth
# from. No network, no key, no account, and nothing here is fetched at run time.
COPY benchmarks/challenge/ /app/benchmarks/challenge/
COPY packages/denali-audit/ /app/packages/denali-audit/
COPY results/concordance/paired_programs.csv /app/results/concordance/paired_programs.csv

RUN mkdir -p /logs/artifacts

# Score the worked example; swap in your own CSV.
CMD ["python", "benchmarks/challenge/scorer/score.py", \
     "benchmarks/challenge/data/example_submission.csv"]
