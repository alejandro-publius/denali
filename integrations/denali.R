## denali.R — run the size audit AT the enrichment step, not after it.
##
## WHY THIS EXISTS. The audit is useful in the ten seconds after an enrichment
## finishes and nearly useless a week later, once the top of the list is already
## in a slide. Every other surface this project ships (a CLI, an MCP server, a
## web page) requires the analyst to stop, export, and go somewhere else. An
## R user running clusterProfiler will not do that, so for them the check does
## not exist.
##
## WHY IT SHELLS OUT rather than reimplementing. core.py's docstring says the
## maths must not drift, and a second implementation in R is exactly the drift
## it warns about. This is a thin adapter over the packaged CLI: same bytes,
## same numbers, no second copy. `tests/test_r_integration.py` runs this file
## against the Python package on identical input and fails the build if any
## value differs.
##
## USE
##   source("integrations/denali.R")
##   ego <- clusterProfiler::enrichGO(genes, OrgDb = org.Hs.eg.db, ont = "BP")
##   denali_audit(ego)          # verdict, R^2, percentile against 1,272 screens
##   denali_rerank(ego)         # which of your top entries size was carrying
##
## It accepts an enrichResult directly, or any data.frame with clusterProfiler's
## columns. `as.data.frame()` on an enrichResult gives BgRatio and Count, which
## is what the audit reads -- so nothing has to be renamed.
##
## REQUIRES the CLI on PATH: pip install -e packages/denali-audit
## The `denali` argument overrides the path if it is installed somewhere else.

.denali_run <- function(x, subcmd, extra = character(0), denali = "denali") {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("denali.R needs the jsonlite package: install.packages('jsonlite')",
         call. = FALSE)
  }
  df <- as.data.frame(x)
  if (nrow(df) == 0L) {
    stop("that enrichment result has no rows to audit.", call. = FALSE)
  }

  ## Resolve the CLI before writing anything, so a missing install fails with a
  ## sentence about installing it rather than with an empty parse further down.
  if (nchar(Sys.which(denali)) == 0L && !file.exists(denali)) {
    stop(sprintf(paste0("could not find the `%s` command on PATH. Install it ",
                        "with: pip install -e packages/denali-audit\n",
                        "  (or pass denali = '/path/to/denali')"), denali),
         call. = FALSE)
  }

  tmp <- tempfile(fileext = ".csv")
  on.exit(unlink(tmp), add = TRUE)
  utils::write.csv(df, tmp, row.names = FALSE)

  ## stderr is captured too. The CLI writes its refusals there -- a table it
  ## cannot recognise, or one too small to say anything about -- and dropping
  ## them would turn an explained refusal into a silent empty result.
  out <- suppressWarnings(
    system2(denali, c(subcmd, shQuote(tmp), extra, "--json"),
            stdout = TRUE, stderr = TRUE))
  status <- attr(out, "status")
  txt <- paste(out, collapse = "\n")

  if (!is.null(status) && status != 0L) {
    stop(sprintf("denali %s refused this table:\n%s", subcmd, txt), call. = FALSE)
  }
  jsonlite::fromJSON(txt)
}

#' How much of this enrichment ranking is explained by gene-set size?
#'
#' @param x an enrichResult from clusterProfiler, or a data.frame of one
#' @param denali path to the denali CLI if it is not on PATH
#' @return a list: verdict, r2_size_alone, the plain-language reading, and
#'   where this ranking sits against 1,272 published CRISPR screens.
#'   It reports a property of the RANKING and nominates nothing.
denali_audit <- function(x, denali = "denali") {
  .denali_run(x, "audit", denali = denali)
}

#' Apply the size correction and report which entries do not survive it.
#'
#' @param top how many of your top entries to check
#' @return a list whose `left_the_top` names the entries your ranking is least
#'   able to justify. This is the inverse of a candidate list: it says what was
#'   carried by size, never what to chase.
denali_rerank <- function(x, top = 10, denali = "denali") {
  .denali_run(x, "rerank", c("--top", as.character(top)), denali = denali)
}

#' What does a predictor that sees only set size score on your evaluation?
#'
#' @param predicted name of the column holding your model's score per set
#' @param metric how you evaluate: spearman, pearson, r2, mae, rmse,
#'   top_k_overlap. Named, never inferred -- a baseline scored with a different
#'   metric than yours is not a comparison.
denali_baseline <- function(x, predicted, metric, denali = "denali") {
  if (missing(predicted) || missing(metric)) {
    stop(paste0("denali_baseline needs both `predicted` (the column holding ",
                "your model's score) and `metric` (how you evaluate). Neither ",
                "is guessed."), call. = FALSE)
  }
  .denali_run(x, "baseline",
              c("--predicted", shQuote(predicted), "--metric", shQuote(metric)),
              denali = denali)
}

#' Print the audit the way a reader should meet it: verdict first.
denali_report <- function(x, top = 10, denali = "denali") {
  a <- denali_audit(x, denali = denali)
  r <- denali_rerank(x, top = top, denali = denali)
  cat("\n", a$verdict, "\n", sep = "")
  cat(strwrap(a$reading, 78), sep = "\n")
  if (!is.null(a$corpus_reading)) cat(strwrap(a$corpus_reading, 78), sep = "\n")
  cat("\n")
  cat(strwrap(r$reading, 78), sep = "\n")
  cat("\n", strwrap(r$what_this_is_not, 78), "\n", sep = "\n")
  invisible(list(audit = a, rerank = r))
}
