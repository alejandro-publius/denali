# Vendored fonts

Both families are used under the SIL Open Font License 1.1, which permits
embedding. They are committed rather than fetched from a CDN because
`tests/test_frozen_invariants.py` asserts that `index.html` makes no network
call — the page has to render identically on an expo machine with no wifi.

Each file is the **latin subset** published by Google Fonts, taken verbatim
from `fonts.gstatic.com` on 2026-08-15. They are inlined into the page as
base64 `@font-face` sources by `src/build_page.py`.

| File | Family | Weight | Upstream |
|---|---|---|---|
| `poppins-400.woff2` | Poppins | 400 | https://fonts.google.com/specimen/Poppins |
| `poppins-500.woff2` | Poppins | 500 | https://fonts.google.com/specimen/Poppins |
| `poppins-600.woff2` | Poppins | 600 | https://fonts.google.com/specimen/Poppins |
| `jetbrainsmono-400.woff2` | JetBrains Mono | 400 | https://fonts.google.com/specimen/JetBrains+Mono |

Poppins © 2020 Indian Type Foundry, Jonny Pinhorn.
JetBrains Mono © 2020 JetBrains s.r.o.

Full licence text: https://openfontlicense.org/open-font-license-official-text/

## Scope

These are presentation assets. Nothing here touches `results/frozen/`, and no
number on the page depends on them.
