# What the reproduction check found

Three defects, all in the reproduction wiring, **none touching a reported number**:

1. **`src.divergence_repair` was in `make all` and cannot run twice.** A one-shot migration that consumes and deletes its own input. Removed from the target, kept as documented history.
2. **`src.freeze` and `src.freeze_matrix` both wrote `provenance.json`.** An interrupted run left the file half-migrated and looking like numeric drift. `freeze_matrix` is now the sole writer.
3. **`src/sweep.py` did not compile.** A blanket text replacement had rewritten the identifier `SEALED_B` as `HELD OUT_B`. The repo shipped that way, and the tests passed the whole time because nothing imported it.

Each was found only by running from a clean clone, and the third only after the first two were fixed.
