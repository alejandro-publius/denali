# Entries

Drop one CSV here and open a pull request. That is the whole submission mechanism —
no server, no account, no hosting.

The file needs two columns, `set` and `score`, one row per gene set in
[`../data/k562_input.csv`](../data/k562_input.csv), where a higher score means
ranked higher. Any other columns are ignored, so you can submit your tool's own
output table with a single column appended.

Every file in this directory is rescored by
[`../scorer/score.py`](../scorer/score.py) on every run and written into
[`../board.md`](../board.md). A row that cannot be reproduced from its own file does
not survive, which is why the board is generated rather than edited.

Say in the pull request what the method was. A score with no method behind it is a
number, not a result.
