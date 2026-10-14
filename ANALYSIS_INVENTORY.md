# Executed analysis inventory - v2

This is an inventory of released computations, not a preregistration or a complete contemporaneous record of every draft choice. All results use the frozen 8 October 2026 outcome vintage. Secondary comparisons are exploratory, dependent, pointwise and not multiplicity-adjusted.

## Original analysis

- Primary cohort and four disagreement quartiles; council, no-change and excess MAE; raw and baseline RMSE.
- Four batch summaries and four types of within-batch Spearman association.
- Twelve selector/coverage pairs: three selectors at 25/50/75/100%.
- Two regression responses with all continuous, batch and class coefficients: log(1+error) and excess error.
- Higher/lower disagreement halves in five volatility bins per batch.
- Mean-sign directional agreement comparison at a 0.5 pp band and six-of-seven threshold, plus always-up comparison.
- Six cohort/scoring sensitivities: expanded coverage, equities, original membership, removal of largest 1% errors, median aggregation and original-anchor scoring.
- Two alternative spread definitions: IQR and MAD.
- Three historical risk windows: 20/60/90 observations.
- Whole-asset cluster percentile intervals; 5,000 draws for means/paired contrasts and 2,000 for regressions, original seed 20261009.

## V2 additions

- Two direction aggregators: mean sign and modal direction with mean-sign fallback on ties; separate no-ties modal summary. Confusion matrices disclose down/flat/up counts.
- Sixteen sign-band/cutoff pairs: four bands (0,0.5,1,2 pp) times four thresholds (4,5,6,7), each with higher/lower groups and both accuracy definitions. All five attainable modal-count levels (3,4,5,6,7) are reported.
- Four individual-batch contrasts and four leave-one-batch-out contrasts for direction, excess-error gradient and selector loss.
- Three directional cohort restrictions: equities, original membership, expanded valid-risk cohort.
- Two stratifying scores (historical risk, signed momentum), five bins within each of four batches, both direction definitions. Weighted averages are descriptive, not fitted causal effects.
- Resampled-rank asset bootstrap for the Q4--Q1 excess-loss gap and the 25% volatility-versus-disagreement selector contrast; 5,000 draws, seed 20261014.
- Sixteen sector/non-equity-class blocks as a larger-dependence sensitivity for four contrasts; fixed archived rank membership, unchanged periods, 5,000 draws, seed 20261014. Group definitions are in `data/asset_dependency_groups.csv` and use the frozen archive's classifications, not certified historical vintages.
- Eighty dense coverage pairs: four selectors (D,V,D/V, risk-residualized D) at twenty coverages from 5% to100%.
- Four risk-scaled quartile summaries and pooled baseline-skill ratios, avoiding unstable individual loss/baseline ratios.
- Seven framework MAEs/accuracies; pooled and four batch-specific correlation matrices; dependence/variance diagnostics for three two-mode frameworks.
- Forecast, outcome, disagreement, risk and horizon distribution summaries; forecast/outcome Pearson correlation.
- Four simple magnitude comparators: no change, mean, median, repeat prior 60-observation return. The momentum rule is unfitted and horizon-mismatched, not a complete finance benchmark.
- Signed-momentum sensitivity for two regression responses; raw-error response sensitivity; n, parameter count, R-squared, partial R-squared, residual standard error, condition number and continuous VIFs.
- Three empirical spread-interval coverages (k=1,2,3), without nominal probabilistic-calibration claims.
- Retained/excluded valid-risk summaries, class-by-quartile/selector composition, entry delays, missing-risk/quarantine counts, and overlap of 20/90-window low-risk selections with the 60-window selection.
- Paired bootstrap council-minus-baseline RMSE by quartile and its Q4--Q1 contrast.
- Two anchor-compatible scoring sensitivities after excluding two records with different forecast/outcome anchor bases; primary entry scores retained.
- Three retrospective illustrative practical bounds (0.5,1,2 pp), no formal equivalence claim.

The detailed JSON/CSVs release unfavorable, favorable and unresolved results. Having inspected these patterns, we do not describe any subsequently chosen subset, cutoff, or selector as an untouched test. More non-overlapping mature periods and a prospectively fixed analysis are required to assess new-regime performance. Author-side input reconstruction is distinguished from external independent market-data replication.
