# Demo — under 3 minutes spoken

**Read the bold. The rest is stage direction.** `[pause]` = stop, let the screen carry it.
**The repeated number is THREE OF FOUR.** Say it in the first sentence and the last.

---

## OPEN

> ### **"We ran four evaluations on this project. Three of them came back negative. We're reporting all four, and the three negatives are the reason the fourth is worth anything."**

`[pause — 2 beats]`

---

## 1 · What it is — one sentence

> **"It takes a biological program — a named list of genes that do one job — and asks which of nine thousand eight hundred genetic knockouts pushes that whole program the other way. We ran all fifty programs in a standard public collection, so we couldn't cherry-pick."**

*Screen: **FIG 1**, the matrix.*

---

## 2 · NEGATIVE ONE — most of what looks like biology is measurement

> **"Between fifty-six and seventy-five percent of the variance in which programs look reversible is explained by measurement quality alone, not biology."**
>
> **"The range is wide because one of our own features is partly circular — computed from the same matrix as the outcome. Fifty-six is the number that survives that objection. We report both ends."**
>
> **"The mechanism is size. Bigger programs with more co-moving members return more hits regardless of what they do. Program size alone explains forty-six and a half percent."**
>
> **"We pre-registered this. Before the sweep we wrote down that if measurability cleared sixty percent, that becomes the finding, not the failure. It cleared."**

*Screen: **FIG 3**.*
`[pause]`

---

## 3 · NEGATIVE TWO — the filter anyone would build is wrong

> **"We built the obvious quality filter: enough members measured, expressed above background, variable above background. Across fifty programs it's wrong twenty times. Twenty fail the filter and produce hits anyway."**
>
> **"And this is why the seal matters. The program we locked in git before the scoring code existed fails our own filter. Expression ratio zero-point-nine-two, just under the line. It ranks eleventh of fifty with seven hundred and seventy-three hits."**
>
> **"We built a filter that would have thrown away our best result. We could only find that out because we sealed the program before we could know."**

*Screen: **FIG 2**.*
`[pause]`

---

## 4 · NEGATIVE THREE — the held-out test failed

> **"Ten programs from a different collection, chosen by a public rule, sealed before the sweep, scored only after we hashed the model."**
>
> **"One of the ten was even measurable. By our own pre-registered rule — written before any number was visible — that makes the whole evaluation underpowered and inconclusive. Binary accuracy came back below chance. Zero true positives."**
>
> **"And the clearest illustration is a single row. Scavenging of heme from plasma drew the highest prediction of all ten. It has one measured gene. It returned zero hits."**
>
> **"That's the measurability finding reappearing in held-out data we hadn't touched. The failure and the finding are the same fact."**

`[pause — strongest beat in the talk]`

---

## 5 · THE POSITIVE — the machinery works

> **"So here's the one that worked, and it's a control, not a headline."**
>
> **"We sealed one row of this matrix before the matrix existed. Cholesterol, commit 9ad74a7, twenty-one minutes before the scoring code was written."**
>
> **"SREBF2 comes back rank two of eleven thousand two hundred and fifty-eight scored perturbations — more than the nine thousand eight hundred genes, because some get targeted twice. It's the textbook answer — we're not claiming we found it. Eleven of seventeen canonical pathway members land in the extreme ten percent, p equals seven times ten to the minus eight, and the signs are right at both ends."**
>
> **"That tells you the ranking works. It does not tell you the ranking is discovering anything, and we don't say that it does."**

---

## 6 · THE LOOP — same agent, three results, three proposals

*Screen: all three side by side. Point at it; don't read it aloud.*

| Result | Proposal it generates | Read from |
|---|---|---|
| **Null**, 0 hits | *"Members expressed and variable, nothing significant → power limit, not biology. Raise depth."* **Falsified if** doubling depth still yields nothing. | `expr_ratio`, `sd_ratio` |
| **Hit**, 5,707 | *"Validate pathway-level, both tails, second cell type."* **Not gene-level, because concordance is −0.019.** | hits, residual |
| **Unscored** | *"Predicted R_p 3.48, SD 0.58. The informative part is the residual."* | 6 features, no scoring |

> **"Same code, three results, three different proposals. No branch in it tests a program name."**

`[pause]`

---

## CLOSE

> **"Three of four evaluations negative. Every one pre-registered, every one reported. Scope is pathway-level only — concordance is minus nought-one-nine, so we name no novel gene anywhere in this project. Everything's frozen with a data dictionary and two hashes that predate the work they validate. Take it apart."**

---

# PREPARED RESPONSES

## ⚠ Partial visibility of the held-out set — lead with point 1

*If asked: "Three rows printed before you patched the crash. You saw part of the held-out set."*

> **1. "The result was a FAILURE. Contamination biases toward looking good. It came back worse than chance with zero true positives — you can't peek your way to that."**
>
> **2. "The frozen predictor, hash 610f2a75, was never touched. Only feature extraction changed, and the hash is verified at load time."**
>
> **3. "The guards are neutral by construction — undefined features fall back to the training mean, so they contribute zero."**
>
> **4. "And the inconclusive verdict fired on a pre-registered rule — one of ten, below the eight-of-ten threshold — before any number was visible."**
>
> **"It's in LIMITATIONS section seven because we wrote it down, not because you found it."**


## ⚠ The question we cannot answer well — say it straight

*If asked: "Three of your six 'measurability' features are properties of the gene set, not of your measurement. Strip them and what's left?"*

> **"You're right that three of the six are set-construction properties, and size is the dominant one. We didn't run the stripped model, so I can't tell you what survives — that's the first thing I'd run next. What I can say is that the pre-registration fixed those six before the sweep, so we're stuck reporting what we committed to rather than the version that flatters us. If the finding collapses to 'bigger sets give more hits,' that's still worth knowing, but it's a smaller claim than the one on our slide."**

**Do not soften this.** The honest version is stronger than a hedge, and the
alternative is being walked into it.

## Six adversarial questions, ranked by how badly they land

| # | Question | Verdict and answer |
|---|---|---|
| **1** | **"The held-out failed. Why should I believe the predictor?"** | **Fatal to the predictor, survivable for the work.** *"Don't believe it. It failed, we report it as failure, we didn't refit. What survives is descriptive: across the fifty we did score, measurability explains most of the variance. The predictor was the test of whether that generalises, and at n=10 it didn't."* |
| **2** | **"You saw part of the held-out set before patching."** | **Survivable — pre-empt it.** See above; lead with "the result was a failure." |
| **3** | **"Is 0.751 inflated by circular features?"** | **Already answered.** *"Yes, partly, and it's in our first sentence. That's why it's a range. 0.561 excludes the circular feature. We never quote the top alone."* |
| **4** | **"−0.019 — doesn't that kill the pathway claims too?"** | **Survivable.** *"Ranking noise moves individual positions; it doesn't move seventeen genes to both tails at p = 7e-8. Gene-level is dead, pathway-level survives, and that's exactly where we drew the line."* |
| **5** | **"SREBF2 at rank 2 is just the obvious answer."** | **Already answered.** *"Completely — and it is labelled a recovered known answer everywhere. What a guess does not produce is the shape: eleven of seventeen canonical pathway members landing in the extreme ten percent with the correct sign at both ends. That is a pathway-level pattern, and it is the only part we claim."* |
| **6** | **"One review covers 50.4% — is the evidence layer real?"** | **Fatal to calling it an evidence chain; we don't.** *"It's a pointer layer and we labelled it one. Our top source for ATF3 was a paper on integrating single-cell data across species. Nineteen of twenty probe genes returned the same zebrafish methods paper."* Screen: **FIG 4**. |

> ### Pre-empt **#1** in the opening.
> "Three of four came back negative" defuses it before it is asked. If a judge raises the held-out failure first, everything after reads as damage control.

## Cut — answer live if asked, do not narrate

RPE1 24.2% coverage collision · tier detail · Sanger KY and scbench (not done, claim nothing) · myeloma anchor (never reached) · essentiality null (+0.021, p=0.90 — only if asked).

## Timing

| Beat | Target |
|---|---:|
| Open | 0:12 |
| 1 What it is | 0:15 |
| 2 Negative one | 0:35 |
| 3 Negative two | 0:35 |
| 4 Negative three | 0:35 |
| 5 The positive | 0:30 |
| 6 The loop | 0:20 |
| Close | 0:15 |
| **Total** | **2:57** |

**If long, cut beat 1.** Never cut beat 4 or the close.
