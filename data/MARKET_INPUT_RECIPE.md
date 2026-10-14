# Reconstructing market-dependent results

V2 supplies a market-summary adapter, not a licensed market dataset. It joins independently prepared inputs to the public original-anchor forecasts and cohort. Exact equality with the author archive is not promised for a different provider or data vintage.

## Required input table

`market_inputs.csv` has one row per `(batch, asset_id)` for all 1,227 matched records. Use `cohort.csv` to map symbol, asset class, issue, entry, target, and actual observed-close date. Keep provider mappings, download date, timezone, currency and corporate-action conventions in your own provenance log.

- `anchor_to_entry_ratio`: recorded forecast anchor quote divided by the saved entry close, with the forecast's share/currency basis reconciled. The original anchor may precede issue. The exact original forecast anchor quotes are not in this public release; do not silently substitute the issue close or assume a provider's daily close is identical. Compatible forecast anchor inputs or authorized access are required.
- `actual_return_pp`: `100 * (observed_close / entry_close - 1)`, using price-only native-currency returns and the recorded observed date; reconcile any split crossing the horizon on a consistent share basis.
- `actual_anchor_pp`: realized return relative to the historical close at the recorded anchor date. Compare `(1 + actual_anchor_pp/100) * anchor_to_entry_ratio - 1` with `actual_return_pp/100`, but do not force equality when the recorded forecast anchor quote differs from that historical close. Two Batch 3 commodity records have this difference in the frozen archive. The adapter records `forecast_anchor_matches_outcome_basis`; original-anchor sensitivities should additionally restrict to compatible bases.
- `risk_observations_available`: count of usable daily log returns dated strictly before `issued`.
- `risk_history_suspect_action`: boolean split-quarantine flag, using the rule below.
- For each window `w=20,60,90`: `risk_n_w`, `risk_cutoff_w` and `risk_pp_w`.
- `momentum_pp`: `100 * expm1(sum(last up to 60 historical log returns))`.
- `max_preforecast_daily_log_move`: maximum absolute log return in the last up to 60 observations.

Only forecasts, dates, grouping, and aggregate results are public here. Realized returns and risk summaries supplied to this adapter are market-dependent inputs with their own rights.

## Computing history summaries

1. Use finite positive price closes with dates strictly earlier than issue. Order by observation date, reject conflicting duplicates, and do not forward-fill absent trading days. There is no requirement that a quarter be exactly 90 days: use the recorded `horizon_days`.
2. For consecutive dates d0,d1, multiply the close ratio by every active split numerator/denominator with ex-date in `(d0,d1]`, then take its logarithm. Do not apply splits again to an already adjusted series. A provider's dividend-adjusted total-return close changes this study's price-only estimand.
3. The original conservative heuristic quarantines the asset/batch history when a split-adjusted absolute log move exceeds 0.4 while its raw absolute log move is below 0.2. This possible double-adjustment rule is not a universal corporate-action validator. Mark all three risk values missing on quarantined histories.
4. For each window take the most recent w observed returns and use sample SD (ddof=1). Require at least `max(15, int(0.75*w))` observations: 15,45,67 respectively. Record the count and latest date.
5. `risk_pp_w = 100 * daily_SD * sqrt(horizon_days * annual_days / 365)`, with annual_days=365 for crypto and 252 otherwise. This is a historical descriptive scale, not a Gaussian predictive distribution.
6. The frozen author archive begins in November 2025 and ends at the 8 October 2026 cutoff. Extending history, changing the split vintage, or altering observed-close selection can change risk and inclusion. Original anchor dates should come from the forecast provenance, not a newly imposed quarter start. Record deviations rather than calling a changed panel an exact replication.

The archived `prepare_panel.py` shows the original extraction and history calculations for an authorized holder of the frozen archive. `reconstruct_panel.py` accepts the resulting summaries in a provider-neutral schema; it does not fetch data or establish redistribution rights.

## Running the adapter

```sh
python code/reconstruct_panel.py --forecasts data/source_forecasts.csv --cohort data/cohort.csv --market-inputs /authorized/path/market_inputs.csv --output-dir /private/path/rebuilt/data
```

The adapter converts each original-anchor model return p to the entry basis as `100*((1+p/100)*anchor_to_entry_ratio-1)`. It then averages modes within frameworks, averages the seven frameworks, recomputes losses and directions, and re-evaluates balanced risk membership. It rejects duplicate keys, non-positive conversion ratios, incomplete configurations, leaked post-issue risk dates, and nonmissing risk on quarantined histories.

To run `analyze.py`, `analyze_v2.py`, and `make_figures.py`, place the rebuilt private `data/panel.csv` and entry-rebased `data/source_forecasts.csv` inside a separate local copy of this project. Do not overwrite or commit the public original-anchor forecast CSV. Compare cohort counts and aggregate outputs before interpreting differences. Never commit or upload the rebuilt panel without checking your input-data rights.

The adapter was validated against the private derived panel using authorized market summaries; this is author-side reconstruction, not independent external market-data replication. Synthetic inputs and validation commands are included in `code/test_reconstruct_panel.py`.
