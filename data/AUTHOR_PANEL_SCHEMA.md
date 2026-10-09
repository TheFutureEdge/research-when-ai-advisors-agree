# Companion data dictionary

Grain is explicit for every table. `pp` denotes percentage points, not fractions; +5 means +5%, rather than 0.05%. Empty CSV numeric cells indicate unavailable historical risk. Dates use ISO YYYY-MM-DD. Stable asset identifiers join tables; framework labels are configured AI personas, not human endorsements.

## panel.csv

1,227 matched asset-batch observations, 376 assets. One row per `(batch, asset_id)`.

| Field(s) | Meaning |
|---|---|
| `batch` | Native generation batch: 3, 4, 5, or 6. |
| `asset_id`, `asset`, `symbol`, `asset_class` | Stable identifier and descriptive asset metadata. |
| `issued` | Archived generation issue date. |
| `entry` | First saved close used for post-generation return evaluation. |
| `target` | Saved native first-quarter target date. |
| `observed` | Actual close date used to resolve that target. |
| `horizon_days` | Calendar days from entry to target; not imposed to be exactly 90. |
| `frameworks`, `configurations` | Seven framework means derived from ten mode configurations. |
| `predicted_return_pp` | Equal-weight mean of seven framework returns rebased to entry. |
| `actual_return_pp` | Realized return rebased to entry. |
| `predicted_anchor_pp`, `actual_anchor_pp` | Corresponding predicted and realized returns relative to the original forecast anchor. |
| `disagreement_anchor_pp` | Population SD across framework forecasts on original-anchor returns. |
| `disagreement_pp` | Population SD across seven entry-rebased framework returns. |
| `disagreement_iqr_pp` | Framework forecast 75th minus 25th percentile, NumPy default linear interpolation. |
| `disagreement_mad_pp` | Median absolute deviation from the framework median; no normal-consistency multiplier. |
| `agreement_share` | Modal up/flat/down share among seven frameworks, range 1/7 to 1. |
| `direction_consensus`, `direction_actual` | Sign categories: -1 down, 0 flat, +1 up; threshold +/-0.5pp, tolerance 1e-10pp. |
| `median_predicted_pp` | Median of seven framework returns. |
| `mean_individual_error_pp` | Mean absolute error of the seven framework returns, before council averaging. Not the primary loss. |
| `original_membership_all` | All ten tasks belong to the original archived asset-batch membership. |
| `risk_observations_available` | Number of valid positive-close daily log returns available before issue in the frozen price archive. |
| `risk_history_suspect_action` | Conservative potential double split-adjustment flag in pre-issue history. |
| `risk_n_20`, `risk_n_60`, `risk_n_90` | Number of observed daily returns used in each historical window. |
| `risk_cutoff_20`, `risk_cutoff_60`, `risk_cutoff_90` | Latest price-return date used; must precede issue. |
| `risk_pp_20`, `risk_pp_60`, `risk_pp_90` | Historical sample daily log-return SD multiplied by 100 and approximate horizon square-root scale; see METHODS.md. |
| `momentum_pp` | Cumulative historical price return over at most the last 60 observed daily returns. |
| `max_preforecast_daily_log_move` | Maximum absolute daily log move in the last 60 observations; audit diagnostic, not a return in pp. |
| `error_pp` | Absolute council return error. |
| `baseline_error_pp` | Absolute realized return, the zero-return forecast error. |
| `excess_error_pp` | Council error minus no-change error; negative favors council. |
| `direction_correct` | Whether council-mean sign equals realized sign. |
| `always_up_correct` | Whether realized sign is up. |
| `balanced` | Asset has matched outcomes in all four batches. |
| `risk_balanced` | Asset has valid positive 60-window risk in all four batches; defines primary panel. |

## primary_panel.csv

928 rows, 232 assets. The `risk_balanced` subset of `panel.csv`, with these additional derived analysis fields:

- `normalized_disagreement`: `disagreement_pp / risk_pp_60`.
- `normalized_error`: `error_pp / risk_pp_60`.

`direction_gain_vs_always_up` is computed inside the analysis after this CSV is written; it is not persisted in this input file.

## source_forecasts.csv

12,270 rows: ten configurations for each of the 1,227 matched outcomes. Grain `(batch, asset_id, framework, mode)`. Fields: `batch`, `asset_id`, `framework`, `mode`, `model_version`, `predicted_return_pp`, `issued`, `entry`, `target`. Only the matched native Q1 prediction is retained, not the complete long-horizon report or prompt text.

Model version identifiers are `20251119_preview_release` for Batches 3--4 and `20260201_preview_release` for Batches 5--6. Their identifiers are operational archive labels, not claims about current provider branding or performance. All retained configurations belong to the historical Gemini family. The modes include the archived creativity/thinking settings in their technical names; they do not establish experimentally isolated effects of these settings.

## JSON and results tables

`cohort_audit.json` contains the source fingerprint, candidate counts, exclusion reasons, coverage dimensions, framework labels and eligible configuration IDs.

`results/results.json` is the full deterministic analysis output: dimensions, class counts, batch estimates, quartiles, risk coverage, paired selector contrast, regressions, risk-stratified contrast, directional comparisons, volatility windows, spread and cohort sensitivities, RMSE, label-maturity audit, seed and bootstrap repetitions.

`results/quartiles.csv` and `results/risk_coverage.csv` provide flat views of the corresponding JSON sections. Interval arrays are serialized as lists in CSV; use JSON for unambiguous programmatic interval access.

## Rights and provenance

No raw daily price series are included. Historical risk and realized return values derive from the iPulse AI market-history archive. These derived market variables retain any applicable source terms; the local author package is not a blanket grant of public redistribution rights. Original model-generated forecasts, manuscript, code and charts are distinguished from price-derived variables. See LICENSE.md.
