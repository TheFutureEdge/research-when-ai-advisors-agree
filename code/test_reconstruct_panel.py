"""Synthetic fixture: no market-derived rows or service calls."""
import numpy as np
import pandas as pd
from reconstruct_panel import reconstruct

def fixture():
    cohort=[];forecasts=[];market=[]
    for batch in (3,4,5,6):
        cohort.append(dict(batch=batch,asset_id='synthetic',issued='2026-04-01',entry='2026-04-02',target='2026-07-01',observed='2026-07-01',horizon_days=90,asset_class='equity',original_membership_all=True))
        for i in range(7):
            for mode in range(2 if i>=4 else 1):
                forecasts.append(dict(batch=batch,asset_id='synthetic',framework=f'framework_{i}',mode=f'mode_{mode}',predicted_return_pp=10+i+mode))
        record=dict(batch=batch,asset_id='synthetic',anchor_to_entry_ratio=.9,actual_return_pp=-1,actual_anchor_pp=10,risk_observations_available=100,risk_history_suspect_action=False,momentum_pp=2,max_preforecast_daily_log_move=.01)
        for w in (20,60,90):record.update({f'risk_pp_{w}':5,f'risk_n_{w}':w,f'risk_cutoff_{w}':'2026-03-31'})
        market.append(record)
    return tuple(pd.DataFrame(x) for x in (forecasts,cohort,market))

if __name__=='__main__':
    f,c,m=fixture();p,s=reconstruct(f,c,m)
    expected=np.array([10,11,12,13,14.5,15.5,16.5])
    assert np.allclose(p.predicted_return_pp,100*((1+expected.mean()/100)*.9-1))
    assert p.risk_balanced.all() and len(s)==40
    assert np.allclose(p.error_pp,abs(p.predicted_return_pp+1))
    bad=m.copy();bad['risk_cutoff_60']='2026-04-01'
    try:reconstruct(f,c,bad)
    except ValueError:pass
    else:raise AssertionError('Leaked history date accepted.')
    print('Synthetic grouping, rebasing, loss, balanced inclusion, and clock checks passed.')
