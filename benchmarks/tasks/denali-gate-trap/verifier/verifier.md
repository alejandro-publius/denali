---
document_version: "0.3"
verifier:
  name: denali-gate-trap
  default_strategy: deterministic
  strategies:
    deterministic:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_mean
    dimensions:
      task_success: {weight: 1.0, source: deterministic}
  outputs:
    reward_json: /logs/verifier/reward.json
    details_json: /logs/verifier/reward-details.json
    aggregate_policy:
      method: weighted_mean
      metrics:
        task_success: 1.0
---

## verifier intent

Deterministic script verifier. ./test.sh runs verifier/test_outputs.py, which compares the agent's /logs/artifacts/answer.json against the frozen screen outcome (answer_key.json, never present in the agent environment) and writes balanced-accuracy-derived reward to /logs/verifier/reward.txt. No model judgment is involved.
