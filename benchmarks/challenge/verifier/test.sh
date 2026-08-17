#!/bin/bash
# Verify the scorer discriminates. Nonzero exit means the scorer is broken --
# it accepted something it must reject, or its arithmetic stopped matching the
# study's published numbers. Not a comment on any submission.
set -u
python3 "$(dirname "$0")/test_scorer.py"
