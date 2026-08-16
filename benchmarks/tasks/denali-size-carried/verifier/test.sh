#!/bin/bash
# Grade the agent's answer. Exit 0 once a reward is written; nonzero exit means
# verifier infrastructure failure, not a failing agent.
set -u
mkdir -p /logs/verifier
python3 "$(dirname "$0")/test_outputs.py"
