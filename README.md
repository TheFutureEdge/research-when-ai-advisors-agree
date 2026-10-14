# When AI Advisors Agree

**When AI Advisors Agree: Distinguishing Forecast Risk from Forecast Reliability**

Russlan Ramdowar · Future Edge Group FZE / iPulse AI · Version 2, 14 October 2026

An observational study of 928 completed quarterly forecasts for 232 assets across four production batches. Ten historical Gemini configurations represent seven framework labels. The study separates asset risk, agreement about direction, and precision of forecast magnitude; it does not evaluate current models or the evidence-weighted synthesizer.

Public repository: https://github.com/TheFutureEdge/research-when-ai-advisors-agree

Research artifacts DOI, v2: https://doi.org/10.5281/zenodo.23373782

All artifact versions: https://doi.org/10.5281/zenodo.23262215

Paper: [arXiv:2610.13431](https://arxiv.org/abs/2610.13431) · [arXiv PDF](https://arxiv.org/pdf/2610.13431). The revised PDF in this release is v2; arXiv mirrors replacements after its processing/announcement cycle.

iPulse AI research page: https://ipulseai.com/research/when-ai-advisors-agree

## Read and inspect

- `When_AI_Advisors_Agree.pdf`: manuscript.
- `paper/`: portable LaTeX source and eleven vector figures.
- `data/source_forecasts.csv`: 12,270 original configuration forecasts.
- `data/cohort.csv`: 1,227 matched records and primary-cohort membership.
- `results/`: aggregate estimates, confidence intervals, quartile and selection analyses.
- `METHODS.md`: timing, grouping, baseline and inference definitions.
- `CHANGELOG.md`: changes from v1 and unresolved generalization/replication limits.
- `ANALYSIS_INVENTORY.md`: released comparisons and exploration boundaries.
- `data/asset_dependency_groups.csv`: frozen sector/class grouping for the dependence sensitivity.
- `data/MARKET_INPUT_RECIPE.md`: compatible market-summary reconstruction recipe.

Run `python code/validate_public_forecasts.py` to validate all public rows and regenerate the seven-framework summaries in `data/forecast_grouping.csv`. Those summaries use the original generation anchor; outcome evaluation uses the separate market rebasing explained in the manuscript.

## Reproduction boundary

This public release contains original forecasts, cohort metadata, aggregate results, manuscript and analysis code. It **does not contain** the full market-derived outcome panel or raw historical prices. The code documents the complete calculations; recomputing outcome-dependent results requires compatible market data obtained under appropriate terms or authorized access to the author-side input. This release does not claim that all outcome results can be independently recomputed offline from these public files.

Use an existing Python environment and `requirements.txt`. With the full author-side `data/panel.csv` available, run:

```bash
python code/validate.py
python code/analyze.py
python code/analyze_v2.py
python code/make_figures.py
```

`code/prepare_panel.py --archive PATH` documents extraction for an authorized holder of the frozen archive (SHA-256 `f4f9510fe0ae2900f124b12e638f06eac073f0397c5646e6dfea62a278555be1`). The outcome cutoff is 8 October 2026. No production services or new model requests are needed to analyze an available outcome panel.

To compile the manuscript, run `pdflatex main.tex` twice in `paper/`, or use Tectonic. No shell escape or external bibliography processor is required.

`python code/test_reconstruct_panel.py` runs a synthetic grouping, rebasing, loss, inclusion and clock check without private data. `reconstruct_panel.py` accepts authorized market summaries; its author-side validation does not establish independent external price replication. Preserve the public original-anchor CSV before using a separate private entry-rebased input with the same analysis filename.

## Principal finding and limits

Numerical disagreement sorts raw error, but a no-change baseline shows almost the same error gradient. Historical volatility selects lower-error cases more effectively. The directional advantage associated with strong agreement is specific to the sign of the average return: modal voting removes the positive contrast. Overall MAE is 15.15 pp against 14.99 for no change, with an unresolved paired difference. These descriptive associations in four overlapping periods do not establish causal effects, equivalence, probabilistic calibration, future-regime performance, or trading profitability. See the manuscript for uncertainty, recomputed-rank bootstrap, dependence and robustness diagnostics.

Original paper, figures, forecast data, cohort metadata and research summaries: CC BY 4.0. Code: MIT. Third-party material retains its own terms; see `LICENSE.md`. Market history is described as the iPulse AI market-history archive; no alternate provider attribution is implied.

Contact: russlan@ipulseai.com · ORCID: https://orcid.org/0009-0004-9311-6957
