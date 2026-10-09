# When AI Advisors Agree

**When AI Advisors Agree: Distinguishing Forecast Risk from Forecast Reliability**

Russlan Ramdowar · Future Edge Group FZE / iPulse AI · 9 October 2026

An observational study of 928 completed quarterly forecasts for 232 assets across four production batches. Ten historical Gemini configurations represent seven framework labels. The study separates asset risk, agreement about direction, and precision of forecast magnitude; it does not evaluate current models or the evidence-weighted synthesizer.

## Read and inspect

- `When_AI_Advisors_Agree.pdf`: manuscript.
- `paper/`: portable LaTeX source and eight figures.
- `data/source_forecasts.csv`: 12,270 original configuration forecasts.
- `data/cohort.csv`: 1,227 matched records and primary-cohort membership.
- `results/`: aggregate estimates, confidence intervals, quartile and selection analyses.
- `METHODS.md`: timing, grouping, baseline and inference definitions.

## Reproduction boundary

This public release contains original forecasts, cohort metadata, aggregate results, manuscript and analysis code. It **does not contain** the full market-derived outcome panel or raw historical prices. The code documents the complete calculations; recomputing outcome-dependent results requires compatible market data obtained under appropriate terms or authorized access to the author-side input. This release does not claim that all outcome results can be independently recomputed offline from these public files.

Use an existing Python environment and `requirements.txt`. With the full author-side `data/panel.csv` available, run:

```bash
python code/validate.py
python code/analyze.py
python code/make_figures.py
```

`code/prepare_panel.py --archive PATH` documents extraction for an authorized holder of the frozen archive (SHA-256 `f4f9510fe0ae2900f124b12e638f06eac073f0397c5646e6dfea62a278555be1`). The outcome cutoff is 8 October 2026. No production services or new model requests are needed to analyze an available outcome panel.

To compile the manuscript, run `pdflatex main.tex` twice in `paper/`, or use Tectonic. No shell escape or external bibliography processor is required.

## Principal finding and limits

Numerical disagreement sorts raw error, but a no-change baseline shows almost the same error gradient. Historical volatility selects lower-error cases more effectively. Strong directional agreement is associated with greater directional accuracy and larger magnitude errors. These are descriptive associations in four overlapping periods, not causal effects, probabilistic calibration or trading profitability. See the manuscript for confidence intervals and robustness checks.

Original paper, figures, forecast data, cohort metadata and research summaries: CC BY 4.0. Code: MIT. Third-party material retains its own terms; see `LICENSE.md`. Market history is described as the iPulse AI market-history archive; no alternate provider attribution is implied.

Contact: russlan@ipulseai.com · ORCID: https://orcid.org/0009-0004-9311-6957
