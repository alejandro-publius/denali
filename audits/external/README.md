# External audit gallery — the same command, other people's screens

**Every row is `src/audit_screen.py`, unmodified, run on the published supplementary
table of someone else's study.** Standardized inputs are committed beside this file;
each result was produced by an adversarial pipeline that (1) fetched the real
supplement, (2) confirmed against the source document that the hit column is a true
per-set count of significant members at a stated threshold — not a score, NES, or
p-value, and (3) independently re-ran the audit. Every number below was then
**re-verified a second time against this branch's exact `src/audit_screen.py`** and
matched to four decimals.

| Study (assay) | Venue | Sets | Ranking variance explained by set construction (size alone) | Verdict |
|---|---|---:|---:|---|
| Single-cell CRISPRa screen, mouse embryonic stem cells | Cell Systems 2020 | 17 | **88%** | CONFOUNDED |
| Bulk RNA-seq KEGG enrichment, hypoxia vs normoxia | PeerJ 2022 | 675 | **72%** | CONFOUNDED |
| Primary human gastric organoid CRISPR-KO screen | Nat Commun 2025 | 147 | **63%** | CONFOUNDED |
| Protein-uptake CRISPR-KO screen, human iPSC neurons (g:Profiler) | EMBO J 2025 | 67 | **63%** | CONFOUNDED |
| TCGA bulk RNA-seq, GO/KEGG over-representation | PeerJ 2023 | 1985 | **52%** | CONFOUNDED |
| Primary human CD8+ T cell CRISPRi/CRISPRa screens | Nat Genet 2023 | 2809 | **42%** | CONFOUNDED |
| Cancer-dependency CRISPR-KO screen (DepMap-based), MSigDB overlaps | Nat Commun 2023 | 85 | **36%** | PARTIALLY CONFOUNDED |
| **This repository's own screen** (`--self-test`) | — | 50 | **46%** (73% with the correlation term) | CONFOUNDED |

## How to read this honestly

- **These are floors.** External figures are *size-alone* R² — the conservative
  lower bound — because published exports do not carry the per-set inter-gene
  correlation needed for the full variance-inflation factor. Where we *can* compute
  it (our own screen), the share rises from 46% to 73%. The real confound in the
  external screens is at least as large as shown, never smaller.
- **The tool discriminates — it does not cry wolf.** One study returns
  *PARTIALLY CONFOUNDED* at 36%, not everything is flagged, and one candidate table
  was **rejected during verification for the right reason**: it was an fgsea/GSEA
  output with no true per-set hit count, and inventing one is the exact error this
  auditor exists to catch (see below).
- **Scope, as everywhere in denali:** each audit measures a property of that study's
  *ranking*, not of any gene, pathway, or conclusion in it. No claim is made about
  any study's biology; several may have entirely size-robust findings. The audit
  says only how much of each ranking a size-aware reader should discount before
  committing validation budget. Small-*n* caveat: the 17-set entry carries the least
  stable estimate, and *n* is printed so you can weigh it.

---

### Single-cell CRISPRa screen, mouse embryonic stem cells — Cell Systems 2020
- **DOI:** [10.1016/j.cels.2020.06.004](https://doi.org/10.1016/j.cels.2020.06.004) · Supplementary Table S3 (file mmc4.xlsx), sheets "Gene ontology enrichment PC1" and "Gene ontology enrichment PC2"; GOrilla output, Related to Figure 1.
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **17**, size range [6, 92], size-alone R² **0.8826** → **CONFOUNDED**
- **What the hit column is (quoted from the source):** hits = b, the last element of the column header "Enrichment (N, B, n, b) " (sheet header row, cols: 'GO term','Description','P-value','FDR q-value','Enrichment (N, B, n, b)','Genes'). Per GOrilla's convention (Eden et al. 2009, BMC Bioinformatics 10:48) and confirmed by reproducing the reported enrichment as E=(b/n)/(B/N) exactly (e.g. 11.47=(7/50)/(11/901)), the tuple is N=total background genes, B=genes associated 
- **What the size column is:** MEASURED (not declared). size = B from the "Enrichment (N, B, n, b)" tuple = the number of background genes associated with the GO term, i.e. the term's gene count restricted to the N=901 background (of the "965 highly variable genes" background stated in the 
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/zga_crispra/std.csv --set set --size size --hits hits`

### Bulk RNA-seq KEGG enrichment, hypoxia vs normoxia — PeerJ 2022
- **DOI:** [10.7717/peerj.14369](https://doi.org/10.7717/peerj.14369) · Supplemental Information 7 (file peerj-10-14369-s007.xlsx inside the PMC9703989 supplementaryFiles zip), sheets 'Pathway' (288 sets), 'GO-BP' (172), 'GO-CC' (120), 'GO-MF' (95); companion *_detail sheets list overlapping genes one per row (Pathway_detail gene rows = 9,843 = sum of 'Genes in Overlap' in the Pathway sheet, exact match)
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **675**, size range [15, 490], size-alone R² **0.7211** → **CONFOUNDED**
- **What the hit column is (quoted from the source):** Hit count column = 'Genes in Overlap' (integer per set). Supplemental Information 7 legend (full-text XML, verbatim): "Supplemental Information 7 GO&KEGG enrichment analysis for genes with the same expression trends in the proteome and transcriptome enrichment results were used in the same genes part of Fig. 7". The counted members are trend-consistent DEGs whose significance threshold is stated in the paper: "the th
- **What the size column is:** Set size column = 'Genes in Gene Set' (declared, not measured): it is the annotated size of each KEGG/GO gene set as reported by the overlap tool (e.g. bta05022 'Pathways of neurodegeneration - multiple diseases' = 490), quoted verbatim from the sheet header '
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/yak-pasmc-s007/std.csv --set set --size size --hits hits`

### Primary human gastric organoid CRISPR-KO screen — Nat Commun 2025
- **DOI:** [10.1038/s41467-025-62818-3](https://doi.org/10.1038/s41467-025-62818-3) · Supplementary Data 3, sheet "Sup Data 3" (DAVID functional-annotation enrichment block, spreadsheet columns J-W, i.e. Category through FDR). PMC mirror: PMC12354852.
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **147**, size range [4, 1721], size-alone R² **0.6349** → **CONFOUNDED**
- **What the hit column is (quoted from the source):** HIT COUNT = the DAVID column headed verbatim "Count" (spreadsheet column L). The embedded legend is the DAVID header row (Excel row 4): "Category | Term | Count | % | PValue | Genes | List Total | Pop Hits | Pop Total | Fold Enrichment | Bonferroni | Benjamini | FDR". DAVID standard definition: Count = the number of genes from the user's input list that are involved in / annotated to the term; here the input list is 
- **What the size column is:** SIZE = the DAVID column headed verbatim "Pop Hits" (spreadsheet column Q). DAVID definition: the number of genes in the background/population annotated to that term. This is a DECLARED size taken from the annotation-database background, NOT measured from the s
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/gastric/std.csv --set set --size size --hits hits`

### Protein-uptake CRISPR-KO screen, human iPSC neurons (g:Profiler) — EMBO J 2025
- **DOI:** [10.1038/s44318-025-00514-0](https://doi.org/10.1038/s44318-025-00514-0) · Dataset EV2 (Supplementary/Expanded-View file MOESM4, 44318_2025_514_MOESM4_ESM.xlsx), data sheet "monomeric OR fibrillar p<0.01" (67 gene sets). Other sheets: "monomeric p<0.01" (38 sets), "fibrillar p<0.01" (71 sets).
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **67**, size range [3, 14808], size-alone R² **0.6345** → **CONFOUNDED**
- **What the hit column is (quoted from the source):** hits = g:Profiler column `intersection_size` = the number of query genes (the CRISPR-screen significant hits) that are annotated to the term. LEGEND sheet, verbatim: "gProfiler2 output showing significantly enriched pathways in the sets of significant hits (pval <0.01) found in the CRISPR screens for monomeric tau, fibrillar tau, or either form of tau protein." Threshold: (1) the query gene set = screen hits selected
- **What the size column is:** DECLARED, not measured. size = g:Profiler column `term_size` = the total number of genes annotated to that term within the effective domain (e.g. COG complex term_size=8, endosome term_size=993). It is the annotation-declared set size, independent of the scree
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/tau_lrp1/std.csv --set set --size size --hits hits`

### TCGA bulk RNA-seq, GO/KEGG over-representation — PeerJ 2023
- **DOI:** [10.7717/peerj.16237](https://doi.org/10.7717/peerj.16237) · Supplemental Information 2 'Raw data: GO KEGG GSEA' (10.7717/peerj.16237/supp-2; peerj-11-16237-s002.zip) -> 'Raw data GO KEGG GSEA/Raw data-GOKEGG(logFC).xlsx', sheet 'Sheet 1' (1985 rows); in-paper excerpt is Table 2
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **1985**, size range [10, 500], size-alone R² **0.5183** → **CONFOUNDED**
- **What the hit column is (quoted from the source):** hits = 'Count' column = GeneRatio numerator (e.g. '38/198' in Table 2, captioned 'HtrA-related gene enrichment, pathway analysis, and functional profiles') = number of the 198 HtrA-related query genes annotated to each set; validated Count == GeneRatio numerator and Count <= size for all 1985 rows. Threshold quote from Methods: "The GO, KEGG, and GSEA of HtrA-related genes were performed using the 'clusterProfiler' p
- **What the size column is:** Measured, not merely declared: size = BgRatio numerator K from clusterProfiler, the number of genes in each set intersected with the analysis background universe (Table 2 shows e.g. 'BgRatio 221/18800' for GO-BP; background denominators vary by ontology: 18800
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/htra3-hnscc-gokegg/std.csv --set set --size size --hits hits`

### Primary human CD8+ T cell CRISPRi/CRISPRa screens — Nat Genet 2023
- **DOI:** [10.1038/s41588-023-01554-0](https://doi.org/10.1038/s41588-023-01554-0) · Supplementary Data (file 41588_2023_1554_MOESM3_ESM.xlsx), sheet "T4D BATF3 Enriched GO Pathways" (2,809 rows). Sister sheet "T4E BATF3 Depelted GO Pathways" was NOT used: its Overlap column is Excel date-corrupted (2,757/3,114 rows became datetimes, e.g. "1965-12-01"), destroying the set-size denominator; per honesty rules it was not reconstructed.
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **2809**, size range [5, 2244], size-alone R² **0.4221** → **CONFOUNDED**
- **What the hit column is (quoted from the source):** HIT COUNT = k, the numerator of the Enrichr "Overlap" column (formatted k/K). k = number of the input significant genes that fall in the GO term; verified k == length of the semicolon-delimited "Genes" list in every one of the 2,809 rows. Input gene list = BATF3-upregulated DEGs at the stated threshold padj < 0.01 (sheet title "T4B BATF3 upreg (padj < 0.01)"). Set-level enrichment significance is the "Adjusted P-valu
- **What the size column is:** DECLARED (annotated), not measured. SIZE = K, the denominator of the Enrichr "Overlap" k/K column = number of genes annotated to that GO term in Enrichr's background GO_Biological_Process library (a library annotation count, not a per-experiment measured count
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/batf3/std.csv --set set --size size --hits hits`

### Cancer-dependency CRISPR-KO screen (DepMap-based), MSigDB overlaps — Nat Commun 2023
- **DOI:** [10.1038/s41467-023-38594-3](https://doi.org/10.1038/s41467-023-38594-3) · Supplementary Data 4 = "Supplemental Table S2" (sheet "Supplemental Table S2")
- **Audited (rerun against this repo's `src/audit_screen.py`):** n_sets **85**, size range [5, 1771], size-alone R² **0.36** → **PARTIALLY CONFOUNDED**
- **What the hit column is (quoted from the source):** Column 4 header verbatim: "# Genes in Overlap (k)". In this MSigDB Compute-Overlaps over-representation analysis, k = the number of genes from the query list (the top-200 genes selectively essential for SMARCA4/2-deficient cancer cells) that are members of each gene set. It is a genuine per-set significant-member COUNT (integers 2-52), not an enrichment score/NES/p-value. The significance threshold governing which se
- **What the size column is:** DECLARED. Column 2 header verbatim: "# Genes in Gene Set (K)". This is the declared MSigDB gene-set size K (e.g. 94, 58, 518, range 5-1771), i.e. the total number of genes in each GO/MSigDB set as catalogued -- NOT the number of genes measured/expressed in the
- **Independently verified:** rerun matched True · column semantics confirmed against source True · provenance resolves True
- **Reproduce:** `python -m src.audit_screen audits/external/smarca4_ala/std.csv --set set --size size --hits hits`

## Rejected during verification (a feature, not a gap)

- **Novel insights from a multiomics dissection of the Hayflick limit — Figure 1—source data 3: Hallmark fgsea results for RS, RIS and CD RNA-seq time courses** — This is a standard fgsea (GSEA) result table, not an over-representation/hit-count table, so it lacks a true per-set significant-member COUNT and I am not permitted to improvise one. Columns in all three result sheets (gsea_timecourse_RS/RIS/CD) are exactly: pathway, pval, padj, log2err, ES, NES, size, leadingEdge. (1) NAME = pathway (present, e.g. HALLMARK_ADIPOGENESIS). (2) SIZE = 'size' = MEASURED genes-in-set retained within the ranked stats list (confirmed measured, not declared: HALLMARK_ADIPOGENESIS is 192 in RS, 193 in RIS, 192 in CD, versus the declared MSigDB Hallmark ADIPOGENESIS size of 200). (3) NO qualifying HIT COUNT. The only per-set FDR column, 'padj', is the per-PATHWAY BH-adjusted enrichment p-value (significance of the whole set's enrichment), i.e. exactly the 'NES/enrichment-score/p-value alone' case the task says to skip. The only enumerable per-set membership is the 'leadingEdge' gene list, but the leading edge is the GSEA core-enrichment subset (genes contributing to the running-sum peak), NOT the count of genes passing a stated per-gene FDR/q/adj-p threshold; leading-edge count is mechanically defined by the GSEA statistic and set size, and no per-gene significance threshold is applied or documented. The candidate itself concedes 'leading-edge membership is defined by GSEA rather than a per-gene FDR cutoff.' Per the task's explicit rule ('A column of NES/enrichment score/p-value alone is NOT a hit count -- skip those tables' and 'If the table does not truly have a per-set significant-member COUNT, return ok:false with fail_reason -- do NOT improvise one'), I stopped at step 2 and did NOT build std.csv or run the auditor. The xlsx downloaded and parsed successfully (44,656 bytes; sheets: readme, gsea_timecourse_RS, gsea_timecourse_RIS, gsea_timecourse_CD; 50 Hallmark sets each); the failure is semantic (no valid hits column), not a download/parse failure.
