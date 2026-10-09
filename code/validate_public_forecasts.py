"""Validate the redistributable forecast/cohort edition without market inputs."""
from pathlib import Path
from collections import defaultdict
import csv, json, math, statistics
ROOT = Path(__file__).resolve().parents[1]
with (ROOT/'data/source_forecasts.csv').open() as f:
    forecasts = list(csv.DictReader(f))
with (ROOT/'data/cohort.csv').open() as f:
    cohort = list(csv.DictReader(f))
keys = {(x['batch'], x['asset_id']) for x in cohort}
assert len(keys) == len(cohort) == 1227
primary = [x for x in cohort if x['risk_balanced'] == 'True']
assert len(primary) == 928 and len({x['asset_id'] for x in primary}) == 232
assert len(forecasts) == 12270
groups = defaultdict(list)
for x in forecasts:
    assert math.isfinite(float(x['predicted_return_pp']))
    groups[x['batch'], x['asset_id']].append(x)
assert set(groups) == keys
summary = []
for (batch, asset_id), records in sorted(groups.items()):
    assert len(records) == 10
    framework_values = defaultdict(list)
    configurations = set()
    for record in records:
        framework_values[record['framework']].append(float(record['predicted_return_pp']))
        configurations.add((record['framework'], record['mode']))
    assert len(framework_values) == 7 and len(configurations) == 10
    values = [statistics.mean(v) for v in framework_values.values()]
    summary.append(dict(batch=batch, asset_id=asset_id,
                        predicted_anchor_pp=statistics.mean(values),
                        disagreement_anchor_pp=statistics.pstdev(values)))
# These are the original generation-anchor returns, not market-rebased returns.
with (ROOT/'data/forecast_grouping.csv').open('w', newline='') as f:
    writer=csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader();writer.writerows(summary)
print(json.dumps(dict(status='passed', configurations=len(forecasts),
                     matched_records=len(cohort), primary_records=len(primary),
                     primary_assets=232, frameworks_per_record=7,
                     note='Market-outcome calculations require separate compatible inputs.'), indent=2))
