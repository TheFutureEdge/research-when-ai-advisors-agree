# Retrospective study protocol

Recorded 9 October 2026, after the initial exploratory audit; extended for version 2 on 14 October. Neither version is preregistered. The outcome cutoff and primary cohort are unchanged.

## Estimand and cohort

Question: does council numerical disagreement identify future return error beyond visible asset risk and a no-change return baseline? A secondary question concerns directional concordance.

Unit: one asset and one generation batch, evaluated at its native first-quarter target. Keep Batches 3, 4, 5, and 6 and all ten configurations in the frozen archive's completed-Q1 configuration set. Require matching entry/target/issue dates, one observation per configuration, finite values, and identical realized returns to tolerance 1e-6. No ranking-position threshold or outcome-performance filter is used.

Match 1,227 outcomes / 376 assets. Require all four batches: 932 outcomes / 233 assets. Require valid positive 60-observation historical volatility in every batch: 928 outcomes / 232 assets. The expanded risk-available sensitivity includes 1,221 outcomes / 373 assets. Daily evaluation refreshes are not independent new forecasts.

## Forecast clock and score

Issued date comes from the archived generation record. Entry is the first saved close after generation; predicted and realized target returns are rebased to that close. Rebased forecast features are known at entry, rather than necessarily at generation. Risk history only uses observations dated strictly before issue. Target and observed-close dates are retained. Earlier targets can be within an approximate quarter because their saved forecast anchor precedes generation; this audit uses the native target, not a newly imposed 90-day target.

Historical price vintages and prompt inputs are not immutable point-in-time captures. The frozen October archive supports reproducibility of this audit but does not certify every contemporaneous input or revised corporate action.

Average modes within each framework, then equal-weight all seven frameworks. Primary council is an arithmetic mean. Numerical disagreement is population SD of seven framework returns. Compare absolute council return error with absolute realized return, the zero-return baseline. Excess error is their paired difference; negative is better than the baseline.

## Covariates and risk

Historical daily log returns incorporate recorded active split ratios. Flag potential double adjustments when adjusted absolute log move >0.4 and raw absolute log move <0.2. A flag in the available pre-issue history invalidates volatility for that asset/batch. Keep at least 75% of the requested window and at least 15 returns: 45 for a 60-observation window. Use sample SD. Horizon-scale risk = 100 * SD * sqrt(calendar horizon days * annual observations / 365), with annual observations 365 for crypto and 252 otherwise. This is a descriptive scale, not a probability model. Momentum is cumulative return over up to 60 prior observed returns. Source archive starts in November 2025.

## Analyses

1. Assign disagreement quartiles separately within each batch. Tie-break by stable asset ID. Pool the four batches with equal primary batch size.
2. Fit retrospective OLS of log(1+absolute error), then excess error, on standardized transformed log volatility, log(1+absolute momentum), log(1+absolute council prediction), log(1+disagreement), batch indicators, and asset-class indicators.
3. Compare higher/lower disagreement halves within five volatility bins per batch. Odd bin sizes give the higher half one more outcome.
4. Select lowest scores at 25/50/75/100% within each batch using raw disagreement, volatility, and disagreement/volatility. Round retained counts upward. These label-free scores describe selection at entry; the asset-complete cohort and choice of scores are retrospective.
5. Define direction using >+0.5pp, <-0.5pp, otherwise flat. A 1e-10pp numerical tolerance at the +/-0.5pp boundaries avoids floating-point classification artifacts. Modal agreement is fraction of seven frameworks in the most frequent direction. High agreement means at least six. Evaluate council-mean sign, which need not equal the modal sign. Always up is the direction baseline.
6. Sensitivities: expanded coverage, equities, original-cohort membership, 1% largest error removal, median aggregation, original-anchor scoring, IQR/MAD spread, RMSE, 20/90-observation volatility.

## Version 2 additions

- Score both mean-sign and modal-direction predictions. Modal ties fall back to mean sign, with a separate no-ties summary. Report bands 0/0.5/1/2 pp, agreement cutoffs 4/5/6/7, all attainable agreement levels, confusion matrices, batch/leave-one-batch-out contrasts, equity/expanded-cohort checks, and population-size-weighted risk and signed-momentum strata comparisons. These are exploratory sensitivities, not threshold optimization.
- Preserve original fixed-group intervals and add 5,000 asset resamples with within-batch ranks and retained membership recomputed. Seed 20261014; entire four-observation asset clusters share resampling weights. Both targets condition on the observed periods, not future common market shocks.
- Report 5% retention increments for D,V,D/V and residuals of within-batch log(1+D) on log(V). Residualization uses the full observed cross-section, no outcomes; it is not an untouched prospective validation.
- Report mean E/V and pooled skill 1-sum(E)/sum(E0), not means of unstable individual E/E0. Add distribution summaries, framework/mode forecast dependence, individual MAE, and an unfitted repeat-prior-60-observation-return comparator with its horizon caveat.
- Add standardized asinh(momentum/10) to the original adjusted design as a retrospective signed-momentum sensitivity. Use 2,000 draws with seed 20261014; report n, parameter count, R-squared, condition number and continuous VIFs. No fitted model is represented as deployable at past issuance dates.
- Report empirical coverage of mean +/- kD at k=1,2,3 without assigning nominal Gaussian coverage. Three illustrative practical bounds (0.5,1,2 pp) are retrospective reference values; no equivalence test/claim is used.
- Compare primary/excluded valid-risk records, class/quartile/selector composition, risk-window selection overlap, and entry delays. Missing-risk and split-quarantine counts remain separate from incomplete configuration exclusions.
- Distinguish recorded forecast anchor quotes from historical outcome anchor closes. Two primary Batch 3 commodity records have different conversion factors; additionally report entry and original-anchor sensitivities excluding those records. Do not force a shared original anchor basis in the reconstruction adapter.

The executable additions are in `code/analyze_v2.py`, with aggregate outputs in `results/results_v2.json`, `direction_thresholds.csv`, and `risk_coverage_dense.csv`. Public `data/MARKET_INPUT_RECIPE.md` describes the adapter boundary. Fixed-membership calculations below retain their original seed and interpretation.

## Original conditional uncertainty and nonclaims

Seed 20261009. Asset clusters contain all retained observations for an asset. Use 5,000 multinomial whole-asset resamples for means/paired contrasts and 2,000 for regression. Pointwise percentile intervals condition on fixed cohort/rank selections. These are not simultaneous intervals, not common-market-shock robust inference, and not prospective guarantees. Regressions are retrospective; only one preceding primary-panel outcome was available at Batch 6 issue, and none at Batches 4 or 5.

No causal independence claim, provider comparison, trading backtest, interval coverage/calibration, or learned prospective confidence model is established. Only four overlapping periods are observed. Multiple secondary comparisons are exploratory and unadjusted for multiplicity.
