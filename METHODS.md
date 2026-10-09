# Retrospective study protocol

Recorded 9 October 2026, after the initial exploratory audit. This document is not a preregistration.

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

## Uncertainty and nonclaims

Seed 20261009. Asset clusters contain all retained observations for an asset. Use 5,000 multinomial whole-asset resamples for means/paired contrasts and 2,000 for regression. Pointwise percentile intervals condition on fixed cohort/rank selections. These are not simultaneous intervals, not common-market-shock robust inference, and not prospective guarantees. Regressions are retrospective; only one preceding primary-panel outcome was available at Batch 6 issue, and none at Batches 4 or 5.

No causal independence claim, provider comparison, trading backtest, interval coverage/calibration, or learned prospective confidence model is established. Only four overlapping periods are observed. Multiple secondary comparisons are exploratory and unadjusted for multiplicity.
