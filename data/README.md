# Public data

`source_forecasts.csv` contains 12,270 original model configuration forecasts: ten forecasts for each of 1,227 matched asset-batch records. Returns are in percentage points at the original generation anchor (`predicted_anchor` in the frozen archive), taken from model-generated quarterly forecast paths. They are predictions, not observed market prices. They differ from the author-side `source_forecasts.csv`, which records market-rebased forecasts used for outcome evaluation. That author-side file is not part of this public edition.

`cohort.csv` identifies those 1,227 matched records, their asset and issue/horizon dates, and membership flags. `risk_balanced=True` identifies the 928 records (232 assets across batches 3-6) used in the main analysis. Dates and flags are audit metadata, not price series.

V2 adds `asset_dependency_groups.csv`: one row per matched asset, with a stable frozen archive sector group for equities and an asset-class group otherwise. Sixteen groups are represented in the primary panel. This is a resampling diagnostic, not a claim that sectors are independent, immutable historical classifications, or independent market regimes. `MARKET_INPUT_RECIPE.md` specifies the separate compatible inputs needed for the reconstruction adapter.

`AUTHOR_PANEL_SCHEMA.md` describes the full author-side analysis input. That full panel is **not** distributed here: realized returns, volatility, momentum, market-derived rebasing and per-record errors remain outside the public release. Aggregate results and the original figures are included under `results/` and `paper/figures/`.

The public files reproduce forecast grouping and disclose the cohort and aggregate findings. Recomputing market-outcome statistics, regressions, bootstrap intervals and scatter plots requires the author-side panel or independently obtained compatible market inputs. Do not mistake aggregate tables for an independently verifiable outcome dataset.
