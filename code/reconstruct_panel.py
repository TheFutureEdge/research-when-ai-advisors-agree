"""Rebuild outcome scores from public forecasts and authorized market summaries.

Market inputs are deliberately not supplied. See data/MARKET_INPUT_RECIPE.md.
The output is private unless the input license permits redistribution.
"""
from pathlib import Path
import argparse
from collections import Counter
import numpy as np
import pandas as pd

def sign(x):
    return np.where(x>.5+1e-10,1,np.where(x<-.5-1e-10,-1,0))

def reconstruct(forecasts,cohort,market):
    keys=['batch','asset_id']
    required=keys+['anchor_to_entry_ratio','actual_return_pp','actual_anchor_pp',
        'risk_observations_available','risk_history_suspect_action','momentum_pp',
        'max_preforecast_daily_log_move']
    for w in (20,60,90):required.extend([f'risk_pp_{w}',f'risk_n_{w}',f'risk_cutoff_{w}'])
    missing=set(required)-set(market)
    if missing:raise ValueError(f'Missing market fields: {sorted(missing)}')
    if cohort.duplicated(keys).any() or market.duplicated(keys).any():
        raise ValueError('One row per batch/asset is required.')
    if forecasts.duplicated(keys+['framework','mode']).any():raise ValueError('Duplicate configuration.')
    d=cohort.merge(market[required],on=keys,how='left',validate='one_to_one')
    if d[['anchor_to_entry_ratio','actual_return_pp','actual_anchor_pp']].isna().any().any():
        raise ValueError('All cohort rows require compatible anchor and outcome inputs.')
    if (d.anchor_to_entry_ratio<=0).any():raise ValueError('Anchor conversion must be positive.')
    if not np.isfinite(d[['anchor_to_entry_ratio','actual_return_pp','actual_anchor_pp']]).all().all():
        raise ValueError('Anchor and outcome inputs must be finite.')
    # Archived forecast-anchor quotes need not equal the historical daily close
    # used for anchor-based outcomes. Keep the two bases explicit, not forced.
    implied=100*((1+d.actual_anchor_pp/100)*d.anchor_to_entry_ratio-1)
    d['forecast_anchor_matches_outcome_basis']=np.isclose(implied,d.actual_return_pp,atol=1e-6,rtol=0)
    for w in (20,60,90):
        valid=d[f'risk_pp_{w}'].notna()
        if (pd.to_datetime(d.loc[valid,f'risk_cutoff_{w}'])>=pd.to_datetime(d.loc[valid,'issued'])).any():
            raise ValueError('Historical risk must strictly precede issue.')
    d['risk_history_suspect_action']=d.risk_history_suspect_action.astype(str).str.lower().eq('true')
    for w in (20,60,90):
        if (d.loc[d.risk_history_suspect_action,f'risk_pp_{w}'].notna()).any():
            raise ValueError('Quarantined split histories must have missing risk.')
    f=forecasts.merge(d[keys+['anchor_to_entry_ratio']],on=keys,validate='many_to_one')
    f['anchor_return_pp']=f.predicted_return_pp
    f['predicted_return_pp']=100*((1+f.anchor_return_pp/100)*f.anchor_to_entry_ratio-1)
    framework=f.groupby(keys+['framework']).predicted_return_pp.mean().unstack('framework')
    anchors=f.groupby(keys+['framework']).anchor_return_pp.mean().unstack('framework')
    index=pd.MultiIndex.from_frame(d[keys]);mat=framework.reindex(index).to_numpy();anc=anchors.reindex(index).to_numpy()
    if mat.shape[1]!=7 or not np.isfinite(mat).all():raise ValueError('Seven complete frameworks required.')
    if not f.groupby(keys).size().eq(10).all():raise ValueError('Ten configurations per record required.')
    d['predicted_return_pp']=mat.mean(1);d['predicted_anchor_pp']=anc.mean(1)
    d['disagreement_pp']=mat.std(1);d['disagreement_anchor_pp']=anc.std(1)
    d['disagreement_iqr_pp']=np.percentile(mat,75,axis=1)-np.percentile(mat,25,axis=1)
    d['median_predicted_pp']=np.median(mat,axis=1)
    d['disagreement_mad_pp']=np.median(np.abs(mat-d.median_predicted_pp.to_numpy()[:,None]),axis=1)
    d['agreement_share']=[max(Counter(row).values())/7 for row in sign(mat)]
    d['direction_consensus']=sign(d.predicted_return_pp);d['direction_actual']=sign(d.actual_return_pp)
    d['mean_individual_error_pp']=np.abs(mat-d.actual_return_pp.to_numpy()[:,None]).mean(1)
    d['error_pp']=abs(d.predicted_return_pp-d.actual_return_pp);d['baseline_error_pp']=abs(d.actual_return_pp)
    d['excess_error_pp']=d.error_pp-d.baseline_error_pp
    d['direction_correct']=d.direction_consensus==d.direction_actual;d['always_up_correct']=d.direction_actual==1
    common=set.intersection(*[set(d.loc[d.batch.eq(b),'asset_id']) for b in (3,4,5,6)])
    valid=d[d.risk_pp_60.notna()&(d.risk_pp_60>0)]
    risk_common=set.intersection(*[set(valid.loc[valid.batch.eq(b),'asset_id']) for b in (3,4,5,6)])
    # Recompute inclusion from supplied risk instead of assuming v1 flags still fit.
    d['balanced']=d.asset_id.isin(common);d['risk_balanced']=d.asset_id.isin(risk_common)
    return d.drop(columns='anchor_to_entry_ratio'),f.drop(columns=['anchor_to_entry_ratio','anchor_return_pp'])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--forecasts',type=Path,required=True)
    parser.add_argument('--cohort',type=Path,required=True)
    parser.add_argument('--market-inputs',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    a=parser.parse_args();panel,source=reconstruct(pd.read_csv(a.forecasts),pd.read_csv(a.cohort),pd.read_csv(a.market_inputs))
    a.output_dir.mkdir(parents=True,exist_ok=True)
    panel.to_csv(a.output_dir/'panel.csv',index=False,float_format='%.17g')
    source.to_csv(a.output_dir/'source_forecasts.csv',index=False,float_format='%.17g')
    print(f'Rebuilt {len(panel)} records; {int(panel.risk_balanced.sum())} in compatible balanced risk panel.')
