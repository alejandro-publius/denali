# denali-gate-trap Verifier Rubric

- `task_success`: Deterministic script verifier. ./test.sh runs verifier/test_outputs.py, which compares the agent's /logs/artifacts/answer.json against the frozen screen outcome (answer_key.json, never present in the agent environment) and writes balanced-accuracy-derived reward to /logs/verifier/reward.txt. No model judgment is involved.
