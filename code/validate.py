"""Independent integrity and reconstruction checks for the derived companion data."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
def validate():
    p=pd.read_csv(ROOT/'data/panel.csv')
    d=pd.read_csv(ROOT/'data/primary_panel.csv')
    s=pd.read_csv(ROOT/'data/source_forecasts.csv')
    r=json.loads((ROOT/'results/results.json').read_text())
    a=json.loads((ROOT/'data/cohort_audit.json').read_text())
    checks=[]
    def check(label,condition):
        assert bool(condition),label
        checks.append(label)
    check('Unique asset-batch panel',not p.duplicated(['batch','asset_id']).any())
    check('Matched source counts',len(p)==1227 and len(s)==12270 and len(s)==10*len(p))
    check('Primary dimensions',len(d)==928 and d.asset_id.nunique()==232)
    check('Four complete batches',d.groupby('asset_id').batch.nunique().eq(4).all())
    check('Balanced primary batch sizes',d.groupby('batch').size().eq(232).all())
    check('No future prices in risk cutoff',(d.risk_cutoff_60<d.issued).all())
    check('Evaluation starts after issue',(d.entry>=d.issued).all())
    check('Future target and observed dates',((d.target>d.entry)&(d.observed>d.entry)).all())
    check('Minimum 60-window coverage',d.risk_n_60.ge(45).all())
    check('Finite positive risk',np.isfinite(d.risk_pp_60).all() and d.risk_pp_60.gt(0).all())
    categorize=lambda x:np.where(np.asarray(x)>.5+1e-10,1,np.where(np.asarray(x)<-.5-1e-10,-1,0))
    check('Council direction formula',np.array_equal(d.direction_consensus,categorize(d.predicted_return_pp)))
    check('Realized direction formula',np.array_equal(d.direction_actual,categorize(d.actual_return_pp)))
    check('Directional accuracy formula',np.array_equal(d.direction_correct,d.direction_consensus==d.direction_actual))
    check('Error formula',np.allclose(d.error_pp,abs(d.predicted_return_pp-d.actual_return_pp),atol=1e-7))
    check('Baseline formula',np.allclose(d.baseline_error_pp,abs(d.actual_return_pp),atol=1e-7))
    check('Excess-error formula',np.allclose(d.excess_error_pp,d.error_pp-d.baseline_error_pp,atol=1e-7))
    grouped=s.groupby(['batch','asset_id','framework']).predicted_return_pp.mean()
    reconstructed=grouped.groupby(['batch','asset_id']).agg(['mean',lambda x:np.std(x,ddof=0),'count']).reset_index()
    reconstructed.columns=['batch','asset_id','mean','dispersion','framework_count']
    joined=p.merge(reconstructed,on=['batch','asset_id'],validate='one_to_one')
    check('Seven framework means',joined.framework_count.eq(7).all())
    check('Council reconstructs from individual forecasts',np.allclose(joined.predicted_return_pp,joined['mean'],atol=1e-7))
    check('Disagreement reconstructs from individual forecasts',np.allclose(joined.disagreement_pp,joined.dispersion,atol=1e-7))
    signs=np.where(grouped.to_numpy()>.5+1e-10,1,np.where(grouped.to_numpy()<-.5-1e-10,-1,0))
    categories=pd.Series(signs,index=grouped.index).groupby(['batch','asset_id']).agg(lambda x:x.value_counts().max()/7).rename('rebuilt_agreement').reset_index()
    j=p.merge(categories,on=['batch','asset_id'],validate='one_to_one')
    check('Directional agreement reconstruction',np.allclose(j.agreement_share,j.rebuilt_agreement,atol=1e-10))
    check('Result mean matches panel',abs(r['primary']['error_pp']-d.error_pp.mean())<1e-7)
    check('Result excess matches panel',abs(r['primary_excess']['estimate']-d.excess_error_pp.mean())<1e-7)
    check('Quartile outcomes',sum(x['outcomes'] for x in r['quartiles'])==928 and all(x['outcomes']==232 for x in r['quartiles']))
    check('Audit lineage',a['input_sha256']=='f4f9510fe0ae2900f124b12e638f06eac073f0397c5646e6dfea62a278555be1')
    check('No pending Batch 7 outcomes',set(d.batch)=={3,4,5,6})
    report={'status':'passed','checks':checks,'check_count':len(checks),'outcomes':len(d),'assets':d.asset_id.nunique()}
    (ROOT/'qa').mkdir(exist_ok=True)
    (ROOT/'qa/integrity_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report
if __name__=='__main__':
    validate()
