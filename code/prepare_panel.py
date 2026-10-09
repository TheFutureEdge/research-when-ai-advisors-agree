"""Prepare a forecast-time, matched-horizon panel from a frozen evaluation archive.

Usage: python code/prepare_panel.py --archive /path/to/generation.zip
Raw market prices and operational metadata are not copied into the release.
"""
import argparse
from collections import defaultdict, Counter
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = "f4f9510fe0ae2900f124b12e638f06eac073f0397c5646e6dfea62a278555be1"

def sign(x):
    return 1 if x > 0.5 + 1e-10 else -1 if x < -0.5 - 1e-10 else 0

def prepare(archive_path):
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError("Input is not the frozen 8 October evaluation artifact.")
    with zipfile.ZipFile(archive_path) as z:
        modes = json.loads(z.read("advisor_modes.json"))
        data = json.loads(z.read("data.json"))
        prices = json.loads(z.read("strategy/prices.json"))
        actions = json.loads(z.read("strategy/actions.json"))
    configurations = {r["id"] for r in modes["scopes"]["completed_q1"]["ranking"]}
    assert len(configurations) == 10
    groups = defaultdict(lambda: defaultdict(list))
    candidate_rows = 0
    for r in data["observations"]:
        cid = r["advisor_id"] + "|" + r["mode"]
        if r["batch"] in (3, 4, 5, 6) and r["view"] == "q1" and cid in configurations:
            candidate_rows += 1
            groups[(r["batch"], r["asset_id"], r["entry"], r["target"])][cid].append(r)
    price_map = defaultdict(dict)
    for r in prices:
        if r["close"] is None or not math.isfinite(r["close"]) or r["close"] <= 0:
            continue
        key = r["date_id"]
        previous = price_map[r["asset_id"]].get(key)
        if previous is not None and previous != r["close"]:
            raise ValueError("Conflicting daily price duplicate")
        price_map[r["asset_id"]][key] = r["close"]
    split_map = defaultdict(dict)
    for a in actions:
        if a["action_type"] == "SPLIT" and a["pulse_status"] == "ACTIVE":
            ratio = a["numerator"] / a["denominator"]
            assert ratio > 0
            old = split_map[a["asset_id"]].get(a["ex_date"])
            assert old is None or old == ratio
            split_map[a["asset_id"]][a["ex_date"]] = ratio
    rows, source_rows, exclusions = [], [], Counter()
    for key, combos in sorted(groups.items()):
        if set(combos) != configurations:
            exclusions["incomplete_configuration_set"] += 1
            continue
        if any(len(v) != 1 for v in combos.values()):
            exclusions["duplicate_configuration"] += 1
            continue
        observations = [v[0] for v in combos.values()]
        realized = [r["actual_issued"] for r in observations]
        if max(realized) - min(realized) > 1e-6:
            exclusions["different_realized_returns"] += 1
            continue
        if len({r["issued"] for r in observations}) != 1:
            exclusions["different_issue_dates"] += 1
            continue
        by_persona = defaultdict(list)
        for r in observations:
            by_persona[r["advisor_id"]].append(r["predicted_issued"])
        predicted = [float(np.mean(v)) for v in by_persona.values()]
        anchor_personas = defaultdict(list)
        for r in observations:
            anchor_personas[r["advisor_id"]].append(r["predicted_anchor"])
        anchor_predictions = [float(np.mean(v)) for v in anchor_personas.values()]
        assert len(predicted) == 7
        if not all(math.isfinite(v) for v in predicted + realized):
            exclusions["nonfinite_returns"] += 1
            continue
        batch, aid, entry, target = key
        issued = observations[0]["issued"]
        before = sorted((d, p) for d, p in price_map[aid].items() if d < issued)
        daily_returns = []
        suspect_action = False
        for (d0, p0), (d1, p1) in zip(before, before[1:]):
            ratio = math.prod(v for d, v in split_map[aid].items() if d0 < d <= d1)
            raw = p1 / p0
            adjusted = raw * ratio
            if ratio != 1 and abs(math.log(adjusted)) > 0.4 and abs(math.log(raw)) < 0.2:
                suspect_action = True
            daily_returns.append((d1, math.log(adjusted)))
        annual_days = 365 if observations[0]["asset_class"] == "crypto" else 252
        horizon_days = (date.fromisoformat(target) - date.fromisoformat(entry)).days
        record = dict(batch=batch, asset_id=aid, asset=observations[0]["asset"],
                      symbol=observations[0]["symbol"], asset_class=observations[0]["asset_class"],
                      issued=issued, entry=entry, target=target, observed=observations[0]["observed"],
                      horizon_days=horizon_days, frameworks=7, configurations=10,
                      predicted_return_pp=float(np.mean(predicted)), actual_return_pp=float(np.mean(realized)),
                      predicted_anchor_pp=float(np.mean(anchor_predictions)), actual_anchor_pp=float(np.mean([r["actual_anchor"] for r in observations])),
                      disagreement_anchor_pp=float(np.std(anchor_predictions)),
                      disagreement_pp=float(np.std(predicted)), disagreement_iqr_pp=float(np.percentile(predicted, 75)-np.percentile(predicted,25)),
                      disagreement_mad_pp=float(np.median(np.abs(np.array(predicted)-np.median(predicted)))),
                      agreement_share=max(Counter(sign(p) for p in predicted).values())/7,
                      direction_consensus=sign(float(np.mean(predicted))),
                      direction_actual=sign(float(np.mean(realized))),
                      median_predicted_pp=float(np.median(predicted)),
                      mean_individual_error_pp=float(np.mean(np.abs(np.array(predicted)-np.mean(realized)))),
                      original_membership_all=all(r["task_id"] in data["original_members"].get(f"{batch}|{aid}", []) for r in observations),
                      risk_observations_available=len(daily_returns), risk_history_suspect_action=suspect_action)
        for window in (20, 60, 90):
            recent = daily_returns[-window:]
            record[f"risk_n_{window}"] = len(recent)
            record[f"risk_cutoff_{window}"] = recent[-1][0] if recent else None
            record[f"risk_pp_{window}"] = (100*float(np.std([v for d,v in recent], ddof=1))*math.sqrt(horizon_days*annual_days/365)
                                           if len(recent) >= max(15, int(0.75*window)) and not suspect_action else None)
        recent = daily_returns[-60:]
        record["momentum_pp"] = 100*math.expm1(sum(v for d,v in recent)) if recent else None
        record["max_preforecast_daily_log_move"] = max(abs(v) for d,v in recent) if recent else None
        rows.append(record)
        for r in observations:
            source_rows.append(dict(batch=batch, asset_id=aid, framework=r["advisor"], mode=r["mode"], model_version=r["model"],
                                    predicted_return_pp=r["predicted_issued"], issued=issued, entry=entry, target=target))
    panel = pd.DataFrame(rows)
    assert not panel.duplicated(["batch", "asset_id"]).any()
    panel["error_pp"] = abs(panel.predicted_return_pp-panel.actual_return_pp)
    panel["baseline_error_pp"] = abs(panel.actual_return_pp)
    panel["excess_error_pp"] = panel.error_pp-panel.baseline_error_pp
    panel["direction_correct"] = panel.direction_consensus == panel.direction_actual
    panel["always_up_correct"] = panel.direction_actual == 1
    common = set.intersection(*[set(panel.loc[panel.batch == b, "asset_id"]) for b in (3,4,5,6)])
    valid = panel.loc[panel.risk_pp_60.notna() & (panel.risk_pp_60 > 0)].copy()
    risk_common = set.intersection(*[set(valid.loc[valid.batch == b, "asset_id"]) for b in (3,4,5,6)])
    panel["balanced"] = panel.asset_id.isin(common)
    panel["risk_balanced"] = panel.asset_id.isin(risk_common)
    audit = dict(input_sha256=digest, cutoff="2026-10-08", candidate_voice_rows=candidate_rows,
                 candidate_date_groups=len(groups), exclusion_groups=dict(exclusions),
                 matched_outcomes=len(panel), matched_assets=panel.asset_id.nunique(),
                 by_batch={str(b):int((panel.batch==b).sum()) for b in (3,4,5,6)},
                 balanced_assets=len(common), balanced_outcomes=int(panel.balanced.sum()),
                 risk_available_outcomes=len(valid), risk_available_assets=valid.asset_id.nunique(),
                 risk_balanced_assets=len(risk_common), risk_balanced_outcomes=int(panel.risk_balanced.sum()),
                 classes=panel.asset_class.value_counts().to_dict(),
                 framework_names=sorted({r["framework"] for r in source_rows}),
                 configurations=sorted(configurations))
    ROOT.joinpath("data").mkdir(exist_ok=True)
    panel.to_csv(ROOT / "data/panel.csv", index=False, float_format="%.17g")
    pd.DataFrame(source_rows).to_csv(ROOT / "data/source_forecasts.csv", index=False, float_format="%.17g")
    (ROOT / "data/cohort_audit.json").write_text(json.dumps(audit, indent=2)+"\n")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    prepare(parser.parse_args().archive)
