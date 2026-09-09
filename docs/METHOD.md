# Method

For a program *p* with measured members *M* and background *B*, each perturbation *i* gets a signed rank statistic from the Mann–Whitney U of member effects against background:

```
u_z(i, p) = −(U(X[i, M], X[i, B]) − μ) / σ        μ = n₁n₂/2,  σ = √(n₁n₂(n₁+n₂+1)/12)
```

Positive `u_z` means the knockdown pushed the program **down**. Per-perturbation p-values are Benjamini–Hochberg corrected **within** each program, and the program's reversibility is:

```
R_p = log₁₀(1 + |{ i : q(i, p) < 0.05 }|)
```

The pre-registered decision regressed `R_p` on six measurability features — `frac_present`, `expr_ratio`, `sd_ratio`, `n_present`, `essentiality_density`, `coherence` — with thresholds fixed before the sweep: **adj R² ≥ 0.60 → measurability dominates; ≤ 0.30 → program-intrinsic; between → report both and claim neither.** It returned 0.751.

The **measurability gate** requires ≥50% of members present, ≥25 present in absolute terms, and both expression and variance ratios ≥ 1.0 against background.

**The rule that fired before any number was seen:** the pre-registration states that if fewer than 8 of the 10 held-out programs pass that gate, the evaluation is reported as **underpowered and inconclusive** rather than as success or failure. One passed. The rule fired against us.
