# How to cite a floor

If you report a no-biology floor, a percentile, or a size-corrected re-ranking
from this tool, cite **both the software and the data underneath it**. The
citation string is generated rather than typed, so it always names the exact
table the number came from:

```bash
denali floor 100          # prints the number, the method, and the CITE line
python -c "from denali_audit.atlas import citation; print(citation())"
```

The string pins a **sha256 of the corpus table**, not a version number or a
commit. A version can be bumped without the numbers moving and a commit moves
when an unrelated file changes; the content hash changes when and only when the
floors do, which is the property a citation needs.

[`CITATION.cff`](../CITATION.cff) and [`.zenodo.json`](../.zenodo.json) carry the same
information in the two formats other people's tooling reads. **No release has
been cut and no tag pushed** — those files are prepared so that minting a DOI is
a decision someone makes, not a side effect of this work.

Cite BioGRID ORCS alongside anything from the atlas: Oughtred R et al., *Protein
Science* 2021;30(1):187–200,
[doi:10.1002/pro.3978](https://doi.org/10.1002/pro.3978). The floors are derived
statistics we computed; the screens are theirs.

