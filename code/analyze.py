"""Reproduce all quantitative results from the derived, frozen study panel.

This is a retrospective observational analysis. No inference calls, trading
claims, nominal independence of reports, or prequential learning are implied.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261009
REPS = 5000
REGRESSION_REPS = 2000

def load_panel():
    data = pd.read_csv(ROOT / "data/panel.csv")
    for c in ("balanced", "risk_balanced", "original_membership_all", "direction_correct", "always_up_correct"):
        data[c] = data[c].astype(str).str.lower().eq("true")
    return data

def quartiles(frame, metric="disagreement_pp"):
    frame = frame.copy()
    frame["quartile"] = 0
    for b, g in frame.groupby("batch"):
        order = g.sort_values([metric, "asset_id"]).index
        frame.loc[order, "quartile"] = 1 + np.arange(len(g))*4//len(g)
    return frame

def bootstrap_means(frame, values, mask=None, reps=REPS):
    ids = sorted(frame.asset_id.unique())
    selected = frame if mask is None else frame.loc[mask]
    sums = selected.assign(value=np.asarray(values)[selected.index]).groupby("asset_id").value.sum().reindex(ids,fill_value=0).to_numpy()
    ns = selected.groupby("asset_id").size().reindex(ids,fill_value=0).to_numpy()
    rng = np.random.default_rng(SEED)
    weights = rng.multinomial(len(ids), np.full(len(ids),1/len(ids)),size=reps)
    return (weights@sums)/(weights@ns)

def ci(boot):
    return [float(x) for x in np.percentile(boot, [2.5,97.5])]

def mean_result(frame, field):
    frame = frame.reset_index(drop=True)
    values = frame[field].to_numpy(dtype=float)
    return {"estimate":float(values.mean()), "ci95":ci(bootstrap_means(frame,values))}

def summarize(frame):
    return dict(outcomes=len(frame),assets=frame.asset_id.nunique(),
                error_pp=float(frame.error_pp.mean()),baseline_error_pp=float(frame.baseline_error_pp.mean()),
                excess_error_pp=float(frame.excess_error_pp.mean()),
                direction_hit_pct=float(100*frame.direction_correct.mean()),always_up_hit_pct=float(100*frame.always_up_correct.mean()))

def quartile_results(frame, metric="disagreement_pp"):
    q = quartiles(frame,metric).reset_index(drop=True)
    results = []
    for level in (1,2,3,4):
        mask = q.quartile.eq(level)
        row = {"quartile":level, **summarize(q.loc[mask]),"mean_disagreement_pp":float(q.loc[mask,"disagreement_pp"].mean()),
               "mean_risk_pp":float(q.loc[mask,"risk_pp_60"].mean())}
        for field in ("error_pp", "baseline_error_pp", "excess_error_pp", "direction_correct"):
            row[field+"_ci95"] = ci(bootstrap_means(q,q[field].to_numpy(dtype=float),mask))
        results.append(row)
    difference = {}
    for field in ("error_pp","baseline_error_pp","excess_error_pp","direction_correct"):
        low = bootstrap_means(q,q[field].to_numpy(dtype=float),q.quartile.eq(1))
        high = bootstrap_means(q,q[field].to_numpy(dtype=float),q.quartile.eq(4))
        difference[field] = {"estimate":float(q.loc[q.quartile.eq(4),field].mean()-q.loc[q.quartile.eq(1),field].mean()),"ci95":ci(high-low)}
    return results,difference

def risk_coverage(frame):
    rows=[]
    for metric in ("disagreement_pp","risk_pp_60","normalized_disagreement"):
        for coverage in (.25,.5,.75,1.):
            kept=[]
            for batch,g in frame.groupby("batch"):
                kept.extend(g.sort_values([metric,"asset_id"]).index[:int(np.ceil(len(g)*coverage))])
            selected=frame.loc[kept].reset_index(drop=True)
            result={"selector":metric,"coverage":coverage,**summarize(selected)}
            result["error_ci95"]=mean_result(selected,"error_pp")["ci95"]
            result["excess_ci95"]=mean_result(selected,"excess_error_pp")["ci95"]
            rows.append(result)
    return rows

def design(frame, include_d=True, include_forecast=True):
    d=frame.copy()
    continuous={"log_risk":np.log(d.risk_pp_60),"momentum":np.log1p(abs(d.momentum_pp))}
    if include_forecast:
        continuous["forecast_magnitude"]=np.log1p(abs(d.predicted_return_pp))
    if include_d:
        continuous["log_disagreement"]=np.log1p(d.disagreement_pp)
    columns={"intercept":np.ones(len(d))}
    for name,values in continuous.items():
        columns[name]=(values-values.mean())/values.std(ddof=0)
    for b in (4,5,6):
        columns[f"batch_{b}"]=(d.batch==b).astype(float)
    for c in sorted(d.asset_class.unique())[1:]:
        columns[f"class_{c}"]=(d.asset_class==c).astype(float)
    return np.column_stack(list(columns.values())),list(columns)

def regression(frame):
    d=frame.reset_index(drop=True)
    x,names=design(d)
    ids=sorted(d.asset_id.unique())
    group=np.array([ids.index(v) for v in d.asset_id])
    rng=np.random.default_rng(SEED)
    weights=rng.multinomial(len(ids),np.full(len(ids),1/len(ids)),size=REGRESSION_REPS)
    results={}
    for target in ("log_error","excess_error_pp"):
        y=np.log1p(d.error_pp.to_numpy()) if target=="log_error" else d.excess_error_pp.to_numpy()
        beta=np.linalg.lstsq(x,y,rcond=None)[0]
        draws=[]
        for w in weights:
            sqrt=np.sqrt(w[group])
            draws.append(np.linalg.lstsq(x*sqrt[:,None],y*sqrt,rcond=None)[0])
        draws=np.array(draws)
        results[target]={name:{"estimate":float(beta[j]),"ci95":ci(draws[:,j])} for j,name in enumerate(names)}
        results[target]["r_squared"]=float(1-np.sum((y-x@beta)**2)/np.sum((y-y.mean())**2))
    return results

def stratified_contrast(frame):
    d=frame.copy()
    d["volatility_bin"] = 0
    d["within_risk_high_disagreement"] = False
    for b,g in d.groupby("batch"):
        order=g.sort_values(["risk_pp_60","asset_id"]).index
        d.loc[order,"volatility_bin"]=1+np.arange(len(g))*5//len(g)
    for key,g in d.groupby(["batch","volatility_bin"]):
        order=g.sort_values(["disagreement_pp","asset_id"]).index
        d.loc[order[len(order)//2:],"within_risk_high_disagreement"]=True
    records=[]
    for level in (False,True):
        g=d.loc[d.within_risk_high_disagreement.eq(level)]
        records.append({"higher_disagreement_within_risk_bin":level,**summarize(g),
                        "error_ci95":mean_result(g,"error_pp")["ci95"],
                        "baseline_ci95":mean_result(g,"baseline_error_pp")["ci95"]})
    d=d.reset_index(drop=True)
    high=d.within_risk_high_disagreement.to_numpy()
    diff={}
    for field in ("error_pp","excess_error_pp"):
        values=d[field].to_numpy()
        draws=bootstrap_means(d,values,high)-bootstrap_means(d,values,~high)
        diff[field]={"estimate":float(values[high].mean()-values[~high].mean()),"ci95":ci(draws)}
    return {"groups":records,"difference":diff}

def run():
    data=load_panel()
    main=data.loc[data.risk_balanced].copy().reset_index(drop=True)
    main["normalized_disagreement"]=main.disagreement_pp/main.risk_pp_60
    main["normalized_error"]=main.error_pp/main.risk_pp_60
    assert len(main)==928 and main.asset_id.nunique()==232
    assert all(main.risk_cutoff_60 < main.issued)
    assert all(main.issued <= main.entry)
    main.to_csv(ROOT/"data/primary_panel.csv",index=False,float_format="%.17g")
    qs,contrast=quartile_results(main)
    extended=data.loc[data.risk_pp_60.notna() & (data.risk_pp_60>0)].copy()
    equities=main.loc[main.asset_class.eq("equity")].copy()
    sensitivities={}
    masks={"expanded_coverage":extended,"equities_only":equities,
           "original_membership":main.loc[main.original_membership_all],
           "exclude_largest_1pct_errors":main.loc[main.error_pp<=main.error_pp.quantile(.99)],
           "median_aggregation":main.copy(),"anchor_return_scoring":main.copy()}
    masks["median_aggregation"]["error_pp"]=abs(main.median_predicted_pp-main.actual_return_pp)
    masks["median_aggregation"]["excess_error_pp"]=masks["median_aggregation"].error_pp-main.baseline_error_pp
    anchor=masks["anchor_return_scoring"]
    anchor["error_pp"]=abs(anchor.predicted_anchor_pp-anchor.actual_anchor_pp)
    anchor["baseline_error_pp"]=abs(anchor.actual_anchor_pp)
    anchor["excess_error_pp"]=anchor.error_pp-anchor.baseline_error_pp
    anchor["disagreement_pp"]=anchor.disagreement_anchor_pp
    for label,frame in masks.items():
        if len(frame):
            _,delta=quartile_results(frame)
            sensitivities[label]={"summary":summarize(frame),"high_minus_low":delta}
    correlations={str(b):{"disagreement_error":float(spearmanr(g.disagreement_pp,g.error_pp).statistic),
                          "risk_error":float(spearmanr(g.risk_pp_60,g.error_pp).statistic),
                          "disagreement_risk":float(spearmanr(g.disagreement_pp,g.risk_pp_60).statistic),
                          "disagreement_excess_error":float(spearmanr(g.disagreement_pp,g.excess_error_pp).statistic)}
                  for b,g in main.groupby("batch")}
    high_agreement=main.agreement_share>=6/7-1e-10
    agreement_groups=[{"agreement":"at least 6 of 7",**summarize(main.loc[high_agreement])},
                      {"agreement":"fewer than 6 of 7",**summarize(main.loc[~high_agreement])}]
    for result, mask in zip(agreement_groups,(high_agreement,~high_agreement)):
        result["direction_ci95"] = [100*v for v in mean_result(main.loc[mask],"direction_correct")["ci95"]]
        result["error_ci95"] = mean_result(main.loc[mask],"error_pp")["ci95"]
    agreement_differences={}
    main["direction_gain_vs_always_up"] = main.direction_correct.astype(float)-main.always_up_correct.astype(float)
    for field in ("direction_correct","direction_gain_vs_always_up","error_pp"):
        values=main[field].to_numpy(dtype=float)
        draws=bootstrap_means(main,values,high_agreement)-bootstrap_means(main,values,~high_agreement)
        agreement_differences[field]={"estimate":float(values[high_agreement].mean()-values[~high_agreement].mean()),"ci95":ci(draws)}
    # Shared asset draws preserve covariance between different selection rules.
    selected_masks = {}
    for metric in ("disagreement_pp", "risk_pp_60"):
        indices = []
        for b, g in main.groupby("batch"):
            indices.extend(g.sort_values([metric,"asset_id"]).index[:int(np.ceil(len(g)*.25))])
        selected_masks[metric] = main.index.isin(indices)
    delta = bootstrap_means(main,main.error_pp.to_numpy(),selected_masks["risk_pp_60"]) - bootstrap_means(main,main.error_pp.to_numpy(),selected_masks["disagreement_pp"])
    selector_difference = {"volatility_minus_disagreement_error_pp": {
        "estimate":float(main.loc[selected_masks["risk_pp_60"],"error_pp"].mean()-main.loc[selected_masks["disagreement_pp"],"error_pp"].mean()), "ci95":ci(delta)}}
    spread_sensitivity={}
    for metric in ("disagreement_iqr_pp", "disagreement_mad_pp"):
        _, spread_delta = quartile_results(main,metric)
        spread_sensitivity[metric]=spread_delta
    rmse_by_quartile=[]
    qm=quartiles(main)
    for q,g in qm.groupby("quartile"):
        rmse_by_quartile.append({"quartile":int(q),"council_rmse_pp":float(np.sqrt(np.mean(g.error_pp**2))),"no_change_rmse_pp":float(np.sqrt(np.mean(g.baseline_error_pp**2)))})
    selectors=[]
    for window in (20,60,90):
        available=main.loc[main[f"risk_pp_{window}"].notna() & (main[f"risk_pp_{window}"]>0)].copy()
        available["risk_pp_60"]=available[f"risk_pp_{window}"]
        available["normalized_disagreement"]=available.disagreement_pp/available.risk_pp_60
        selection=[r for r in risk_coverage(available) if r["coverage"]==.25 and r["selector"]=="risk_pp_60"][0]
        selectors.append({"window":window,**selection})
    # This explicitly audits label availability; no learned live policy is claimed.
    timing={str(b):int(((main.batch<b)&(main.observed<main.loc[main.batch.eq(b),"issued"].min())).sum()) for b in (3,4,5,6)}
    result=dict(cutoff="2026-10-08",seed=SEED,bootstrap_reps=REPS,regression_bootstrap_reps=REGRESSION_REPS,
                primary=summarize(main),primary_classes=main.asset_class.value_counts().to_dict(),
                primary_excess=mean_result(main,"excess_error_pp"),quartiles=qs,high_minus_low=contrast,
                by_batch={str(b):summarize(g) for b,g in main.groupby("batch")},
                correlations=correlations,risk_coverage=risk_coverage(main),regressions=regression(main),
                risk_stratified=stratified_contrast(main),selector_difference=selector_difference,spread_sensitivity=spread_sensitivity,rmse_by_quartile=rmse_by_quartile,agreement_groups=agreement_groups,agreement_differences=agreement_differences,
                volatility_window_sensitivity=selectors,
                sensitivity=sensitivities,prior_completed_outcomes_at_issue=timing,
                limitations=["Retrospective analysis, not preregistered or a learned prospective deployment test.",
                             "Asset-cluster pointwise percentile intervals condition on fixed selection scores; they do not remove common market dependence.",
                             "Seven frameworks share historical Gemini versions; they are not seven independent provider models.",
                             "Disagreement is spread among point forecasts, not a calibrated probability interval."])
    ROOT.joinpath("results").mkdir(exist_ok=True)
    (ROOT/"results/results.json").write_text(json.dumps(result,indent=2)+"\n")
    pd.DataFrame(qs).to_csv(ROOT/"results/quartiles.csv",index=False)
    pd.DataFrame(result["risk_coverage"]).to_csv(ROOT/"results/risk_coverage.csv",index=False)
    brief={k:result[k] for k in ("primary","primary_excess","high_minus_low","risk_stratified","agreement_groups","prior_completed_outcomes_at_issue")}
    brief["adjusted_disagreement"]={k:r["log_disagreement"] for k,r in result["regressions"].items()}
    print(json.dumps(brief,indent=2))
    return result

if __name__=="__main__":
    run()
