# Domain 5 substrate extraction — curatedMetagenomicData CRC cohorts.
#
# Pre-registered in docs/DOMAINS_PREREG.md (6d40a079..., a2776f7) with
# CORRECTION 1 (commit 8d2296a) fixing the set definition BEFORE any value was
# computed: sets = MetaCyc pathways, members = the species carrying them, read
# from the stratified HUMAnN pathway-abundance table cMD already ships.
#
# This script only WRITES THE SUBSTRATE. It computes no audit statistic; all
# inference happens in src/domain_microbiome.py so the audit code stays in one
# language and one place.
#
#   Rscript src/microbiome_extract.R
#
# Writes data/raw/microbiome/<cohort>_pathways.tsv (features x samples) and
# data/raw/microbiome/<cohort>_meta.tsv.

suppressMessages({
  library(curatedMetagenomicData)
  library(SummarizedExperiment)
})

outdir <- "data/raw/microbiome"
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

s <- sampleMetadata
crc <- s[!is.na(s$study_condition) &
         s$study_condition %in% c("CRC", "control") &
         s$body_site == "stool", ]
tb <- table(crc$study_name, crc$study_condition)
tb <- tb[tb[, "CRC"] >= 20 & tb[, "control"] >= 20, , drop = FALSE]
cohorts <- rownames(tb)
cat("cohorts meeting n>=20 per group:", length(cohorts), "\n")

for (co in cohorts) {
  f <- file.path(outdir, paste0(co, "_pathways.tsv"))
  if (file.exists(f)) { cat("  have", co, "\n"); next }
  cat("  fetching", co, "\n")
  ok <- tryCatch({
    se <- curatedMetagenomicData(
      paste0(co, ".pathway_abundance"), dryrun = FALSE, rownames = "long",
      counts = FALSE)[[1]]
    keep <- colData(se)$study_condition %in% c("CRC", "control")
    se <- se[, keep]
    m <- assay(se)
    write.table(m, f, sep = "\t", quote = FALSE, col.names = NA)
    md <- data.frame(sample = colnames(se),
                     condition = colData(se)$study_condition)
    write.table(md, file.path(outdir, paste0(co, "_meta.tsv")),
                sep = "\t", quote = FALSE, row.names = FALSE)
    cat("    ", nrow(m), "features x", ncol(m), "samples\n")
    TRUE
  }, error = function(e) { cat("    FAILED:", conditionMessage(e), "\n"); FALSE })
}
cat("done\n")
