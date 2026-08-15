# Demo spine — under 3 minutes, spoken

**Read the bold. The rest is stage direction.**
`[pause]` = stop talking, let the screen carry it.

---

## Open with this sentence

> ### **"Our headline number is minus zero point zero one nine — that's our own reproducibility check failing, and it's why you can trust everything else I'm about to show you."**

`[pause — 2 beats. Let them look confused.]`

---

## 1 · The graveyard — 10 seconds, brisk, no apology

> **"Four projects died to get here. A cross-paper conflict engine that turned out to be a parsing artifact. A figure-certification thesis our own measurements falsified. A lung fibrosis program that returned zero genes across seven cell populations. And three of the four cell programs we gated last night."**
>
> **"All of it is in the repo with the kill criteria that fired."**

*Screen: commit graph, or the four names struck through.*
`[pause]`

---

## 2 · What we built — one sentence

> **"We built something that takes a biological program — a named list of genes that do one job — and asks which of nine thousand eight hundred genetic knockouts pushes that whole program the other way."**

*Screen: program in → ranked knockouts out.*

---

## 3 · Program A returns nothing, and we can name the mechanism

> **"We chose the unfolded protein response — how cells handle badly-folded protein. It returns nothing. PERK, IRE1, XBP1 — the three textbook sensors — all sit at q of about 0.8. Dead."**
>
> **"And here's the mechanism, not an excuse: the cells were never stressed. Unstimulated K562 has no ER stress, so the program was switched off. Knocking out the sensors of an alarm that isn't ringing moves nothing."**
>
> **"Our gate tested whether the program was measurable. It should have tested whether it was engaged. That's on us, and it's written down."**

*Screen: PERK / IRE1 / XBP1 with their q-values. Big.*
`[pause — this is the honesty beat. Do not rush it.]`

---

## 4 · Program B — sealed, and it works

> **"Before we scored anything, we sealed a second program in git. Cholesterol. Commit 9ad74a7, 8:24 in the morning."**
>
> **"The scoring code didn't exist yet. We wrote it twenty-one minutes later. There was nothing to tune."**

`[pause]`

> **"SREBF2 comes back rank one of nine thousand eight hundred and thirty-seven. It's the master regulator of cholesterol synthesis — the textbook answer. We are not claiming we discovered it. It's the positive control that says the ranking works."**
>
> **"The real result is the shape. Seventeen canonical pathway members were in the screen. Eleven land in the extreme ten percent. Expected by chance: one point seven. p equals seven times ten to the minus eight."**
>
> **"And the signs are right at both ends. Knock out the activators, the program goes down. Knock out INSIG1 — the brake — and it goes up, rank nine thousand eight hundred and fifteen. Seventy-nine percent sign-correct across both tails. A fitness artifact does not do that."**

*Screen: the 17-gene rank distribution, both tails highlighted.*
`[pause]`

---

## 4b · We audited our own literature tool, and it failed

`[This is a named result, not a caveat. Say it as a finding.]`

> **"We used Paperclip to build the evidence layer — one citation per gene, a hundred and thirteen genes. Then we audited it instead of trusting it."**
>
> **"Thirty-four distinct sources cover a hundred and thirteen genes. One review is the cited evidence for fifty-seven of them — half the program. Only fourteen of a hundred and thirteen top hits even name their own gene in the title."**

`[pause]`

> **"So we ran a blind probe on twenty more genes to check whether that was our query or the tool. Nineteen of the twenty came back with the same zebrafish methods paper. For one gene it returned a paper about a different gene entirely."**
>
> **"That's not an evidence chain. It's a pointer layer, and we labelled it as one in the repo before anyone asked. If you build on retrieval, measure your retrieval."**

*Screen: 34 / 113, the 50.4% bar, the 19-of-20 probe.*

---

## 5 · The scope statement — as a choice, not a confession

> **"So back to minus zero one nine. Two independent guides aimed at the same gene give uncorrelated scores. Gene-level calls are not reproducible in this data."**
>
> **"So we made a choice. We make pathway-level claims only, and we name no novel gene anywhere in this project. Not one. We could have put a novel gene on this slide and most of you would not have caught it tonight."**
>
> **"We also report that one review paper is the entire cited evidence for fifty-seven of our hundred and thirteen genes. That's a real weakness. You didn't have to find it."**

`[pause]`

> **"Everything is frozen in results/frozen with a data dictionary. The kill criteria are hashed. The seal timestamp is in the commit log. Take it apart."**

---

## Cut list — did not survive compression

| Cut | Why |
|---|---|
| RPE1 24.2% / 94.1%-vs-11.3% collision | Real and quantified, but needs 40s to land. **Answer live if asked.** |
| The divergence table (90/12/11) | Great artifact, competes with §4 for attention. **Put on screen, don't narrate.** |
| scbench, Sanger KY | Not done. Don't raise; answer honestly if asked. |
| Tier system detail | `tier_label` on screen does the work. |
| Paperclip / Europe PMC mechanics | Only the 57-of-113 number survives. |
| Multiple myeloma anchor | Never reached. Don't imply we did. |

## If asked — one line each

- **"Does −0.019 kill the pathway claim too?"** → *"No. Ranking noise moves individual positions; it doesn't move seventeen genes to both tails at p equals seven-e-minus-eight. Gene-level is dead, pathway-level survives, and that's exactly where we drew the line."*
- **"Isn't SREBF2 obvious?"** → *"Completely. Guessing SREBF2 is easy. Guessing INSIG1 at rank 9,815 is not."*
- **"Could the null be a bug?"** → *"Same code, same session, produced a clean positive on program B. A bug that nulls one gene set and recovers a seventeen-member pathway in another doesn't exist."*
- **"Did you replicate?"** → *"No. RPE1 covers 24% of our genes and none of the headline ones. We call it a generalization check, never replication."*
- **"Your essentiality filter uses an average across a thousand cell lines. Isn't that the wrong number?"** → *"It was, for two genes, and we found that by checking rather than inheriting it. We pulled the K562-specific value — the line we actually ran in — and MBTPS2 and LDLR both cross the essentiality line there when the average said they didn't. Those two rows carry a note that overrides the tier. SREBF2 goes the other way: minus zero-two-four on the average, plus zero-two-nine in K562 — not essential by either measure, with more margin in the cell line that matters."*

## Timing

| Section | Target |
|---|---:|
| Opening line | 0:10 |
| 1 Graveyard | 0:20 |
| 2 What we built | 0:15 |
| 3 Program A null | 0:40 |
| 4 Program B sealed | 0:55 |
| 5 Scope statement | 0:35 |
| **Total** | **2:55** |

**If you run long, cut the graveyard to one sentence.** Never cut §5.
