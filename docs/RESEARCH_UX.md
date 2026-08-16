# UX research — how the tools this audience already trusts handle first contact

Written 2026-08-16, before touching any code. Method: each site below was
actually opened in a headless Chromium (Playwright 1.62, 1280×900) and
screenshotted; where a flow mattered (example → run → results) it was driven,
not read about. Claims below marked **observed** come from those sessions.
Claims marked *inferred* are reasoning from what was observed, and say so.

The question asked of every site: what is the FIRST action offered? How does it
handle "I don't have data yet"? Where does the example live? How does it explain
a statistic to someone who won't read a methods section? What does it do that is
obviously bad?

---

## Enrichr — https://maayanlab.cloud/Enrichr/

**Observed.** The landing page IS the input form. The page heading is "Input
data"; the primary affordance is a paste/drop textarea, above the fold, with a
live "0 gene(s) entered" count beneath it. No login is required to run anything
(Login/Register exist, top-right, ignorable). The "I don't have data" answer is
a plain link inside the instruction sentence — "You can try a gene set
*example*" — one click fills the form; Submit then lands on a results grid with
zero further questions. Credibility is carried by counters in the header:
"134,467,383 sets analyzed · 473,746 terms · 229 libraries".

**Observed, results view** (drove example → Submit): an immediate grid of
per-library bar-chart cards under category tabs (Transcription / Pathways /
Ontologies / …). Statistics are not explained on the surface at all — each card
has a small ⓘ icon; p-value, odds ratio and combined score appear only in the
table view. The Overlap column there is the "5/200" string our Enrichr adapter
parses.

**Obviously bad, observed:** three citation paragraphs occupy the middle of the
input page; a row of eight sibling-tool badges ("You can also try submitting
the gene set to: ChEA-KG, Rummagene, …") distracts from the one action that
matters; nothing on the input page says what you will get after Submit.

**Lesson for denali:** the example must be one click and must land on a full
result, and the input surface must be the page, not a page you reach.

## g:Profiler — https://biit.cs.ut.ee/gprofiler/gost

**Observed.** First action: a large query textarea with an orange **Run query**
button — the only saturated colour on the page (the restraint is familiar).
Directly beside the primary button, in quieter type: "random example" and
"mixed query example". That placement is the whole answer to "no data yet":
the example is physically adjacent to the primary action, styled one step
quieter, so an empty-handed visitor's eye lands on it without a search.
Input modes are tabs of one control: Query / Upload query / Upload bed file.
Options sit to the right with ⓘ tooltips; everything advanced is collapsed.

**Observed, results** (drove random example → Run query): results render on the
SAME page, below the form, under tabs (Overview / Detailed Results / GO Context
/ Query Info) — the input that produced them stays visible above. Export to
PNG / query URL / short link are immediate. The Detailed Results table carries
`term_size` and `intersection_size` — the exact columns `denali-audit` reads
as-is.

**Observed, privacy:** the footer states "g:Profiler respects our users'
privacy and therefore we do not store user gene lists", with the one exception
(short-link sharing) named in the same sentence. A privacy property stated
plainly, at the surface, with its caveat inline — the same register denali's
copy already uses.

**Obviously bad, observed:** the top nav is thirteen items of project
administration (News, Archives, Beta, Contact, …); the statistical method
(g:SCS multiple-testing correction) is nowhere near the results that use it —
you must find the Docs page. *Inferred:* a first-time biologist reads the
Manhattan plot's y-axis as "bigger is better" and never learns what was
corrected or why.

**Lesson for denali:** same-page results with the input still visible; example
adjacent to the primary action; privacy stated where the data enters, caveat
inline.

## Morpheus — https://software.broadinstitute.org/morpheus/

**Observed.** The most relevant precedent found, and the strongest. The landing
page is a file-open dialog. The heading is "Open". The first line under it:
**"All data is processed on your computer and never sent to any server."** —
the exact property denali's page has, stated in one sentence at the exact point
a user would worry about it. Input sources are tabs of one picker: My Computer
/ URL / Dropbox / **Preloaded Datasets** — the example data is not a separate
feature, it is one more place a file can come from. The drop zone reads
"Select File — or Copy and Paste Clipboard Data, Drag and Drop": three input
modalities in one affordance. The right rail explains what the tool is in two
sentences, then usage stats (30,000+ users, 100,000+ matrices), then the
citation. Nothing else on the page.

**Lesson for denali:** this is the shape to steal. Client-side compute stated
as one plain sentence at the point of upload; example data as a peer of "your
file", not a demo elsewhere; the whole surface is the action.

## cBioPortal — https://www.cbioportal.org/

**Observed.** The landing page is the query builder itself: a study list with
checkboxes, quick-select buttons ("TCGA PanCancer Atlas Studies", "Curated set
of non-redundant studies"), and two big actions at the bottom — "Query By Gene"
/ "Explore Selected Studies". Login optional. The "no data yet" answer is a
right-rail list of **Example Queries** ("RAS/RAF alterations in colorectal
cancer", …) that deep-link straight into a finished result view — not into a
tutorial. Every study row carries an ⓘ.

**Obviously bad, observed:** density — a first-timer faces 539 studies, a
what's-new feed, social icons, a deployment map, and a chat beta before
understanding what a "study" is here.

**Lesson for denali:** examples that land on a finished result teach faster
than examples that land on a filled-in form.

## DepMap portal — https://depmap.org/portal/

**Observed.** The first thing a visitor meets is a full-screen Terms and
Conditions modal — ~800 words of legal text covering the entire page, with the
accept control below the modal's own fold. Behind it: a welcome hero, a search
bar ("Type in a gene, cell line, compound…") as the true primary action, and
"Explore the data" cards.

**Obviously bad, observed:** the modal IS the onboarding. Whatever the legal
need, the portal's first interaction is scrolling a contract.
**Lesson for denali:** never put anything — even one sentence — between the
visitor and the surface. denali has no terms to accept; its equivalent sin
would be an explainer the user must scroll before the button appears.

## UCSC Genome Browser — https://genome.ucsc.edu/

**Observed.** Dense, dated front door: a mid-page search bar is the primary
action; a Tools list gives each tool one clause of description ("Genome Browser
— Interactively visualize genomic data"); a "DID YOU KNOW?" tip box rotates
power-user features. News, meetings, and workshops fill the rest. No example
prominence — the page assumes you arrive knowing what you want.

**Lesson for denali:** one honest clause per tool name works; assuming intent
does not. A first-time visitor to UCSC who does not already know what a
"track" is has no path. (*Inferred* from the page structure; UCSC's actual
audience mostly does know.)

## Galaxy — https://usegalaxy.org/

**Observed.** A three-panel workbench (tool list · center · history). The
empty state is handled well in one place: the History panel's empty state
reads "This history is empty. **You can load your own data or get data from an
external source**" — the empty state itself contains its two exits as links.
The center panel, though, spends the prime slot on a sponsor-sticker carousel
and a Bluesky feed; "start here" is a link inside a paragraph. Registration is
needed to actually keep work (*inferred from the Login/Register emphasis; not
driven to the wall*).

**Lesson for denali:** an empty state must name its exits. Galaxy's history
panel does; its center panel is the anti-lesson.

## MAGeCKFlute — Bioconductor

**Observed, and a finding in itself:** the release landing page
(`bioconductor.org/packages/release/bioc/html/MAGeCKFlute.html`) returns **HTTP
404**, and `bioconductor.org/packages/MAGeCKFlute/` redirects to Bioconductor's
"Removed Packages" page, where MAGeCKFlute is listed. The canonical
post-MAGeCK enrichment pipeline this audience was taught is being removed from
the release; its documentation links are rotting now.

**Lesson for denali:** the MAGeCK screener denali most wants to reach is
losing their default downstream tool. Meeting them at the file they already
have (`gene_summary.txt`, which the adapter reads as-is) is not a convenience
feature — for that user it may be the only thing on offer that still resolves.
Also: never make a doc URL the only path to a capability.

## Benchling — https://www.benchling.com/

**Observed.** Pure enterprise SaaS front door: "AI for every scientist" hero,
"Request a demo" as the primary action (twice), Sign up, cookie-consent modal.
There is no path to touching the product without a sales interaction.

**Lesson for denali:** this is the inverse pole. A results page with no action
(denali today) and a demo-gate with no product (Benchling's public site) fail
the same user the same way: convinced, then stranded.

---

## What this research changes about the plan

1. **The primary action goes above the fold and the example sits beside it,
   one step quieter** (g:Profiler's exact geometry). Not a "demo" section
   further down.
2. **The example runs to a finished result in one click** (Enrichr,
   cBioPortal), on the same page, with the input still identifiable
   (g:Profiler).
3. **The no-upload property is stated in one sentence at the drop zone**
   (Morpheus, g:Profiler's footer note — ours moves to the point of entry).
   The page already makes zero network calls; saying so where the file lands
   converts an invariant into trust.
4. **Example data is a peer of "your file", not a separate feature**
   (Morpheus's Preloaded Datasets tab).
5. **Empty states name their exits** (Galaxy's history panel). Every state of
   the new path — empty, reading, unrecognised, too-few-rows, result — must
   say what to do next in the state itself.
6. **Nothing stands between the visitor and the surface** (DepMap's modal as
   the anti-pattern). No explainer gate, no scroll-to-reveal.
7. **Statistics get one plain clause at the point of use** (every site defers
   the stat to a ⓘ or a docs page; nobody explains inline — this is the gap
   denali's writing rules already fill: "state the number, then the
   objection", in the sentence, not a tooltip).
8. **MAGeCK users are the underserved audience** — their downstream tool has
   left Bioconductor. The upload path must recognise `gene_summary.txt` with
   the same zero-configuration the CSV formats get (the adapter already does;
   the page must say so).
