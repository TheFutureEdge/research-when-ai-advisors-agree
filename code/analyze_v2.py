"""Exploratory v2 diagnostics on the unchanged, frozen v1 outcome panel.

No model calls or data refresh. Public outputs are aggregates; input outcomes
remain in the private author edition. All intervals condition on observed periods.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import analyze as base

ROOT = Path(__file__).resolve().parents[1]
SEED, REPS = 20261014, 5000
def sign(x, band=.5):
    return np.where(x > band+1e-10,1,np.where(x < -band-1e-10,-1,0))
def summary(d):
    return {k:float(d[k].mean()) for k in ('error_pp','baseline_error_pp','excess_error_pp','risk_pp_60','disagreement_pp','momentum_pp')} | {'n':len(d),'assets':d.asset_id.nunique()}
def interval(x):
    return np.percentile(x,[2.5,97.5]).tolist()
def boot(d,values,mask=None):
    d=d.reset_index(drop=True)
    return base.bootstrap_means(d,np.asarray(values,float),mask,reps=REPS)
def contrast(d,values,mask):
    a=np.asarray(values,float); mask=np.asarray(mask,bool)
    return {'estimate':float(a[mask].mean()-a[~mask].mean()),'ci95':interval(boot(d,a,mask)-boot(d,a,~mask))}
def ranked_indices(d,metric,fraction):
    return np.concatenate([g.sort_values([metric,'asset_id']).index[:int(np.ceil(len(g)*fraction))] for _,g in d.groupby('batch')])
def direction_summary(d,f,band=.5,cutoff=6):
    fs=sign(f,band); counts=np.column_stack([(fs==c).sum(1) for c in (-1,0,1)])
    ties=(counts==counts.max(1)[:,None]).sum(1)>1
    raw_modal=np.array([-1,0,1])[counts.argmax(1)]
    mean=sign(f.mean(1),band); actual=sign(d.actual_return_pp.to_numpy(),band)
    modal=np.where(ties,mean,raw_modal)
    high=counts.max(1)>=cutoff
    rows=[]
    for name,m in [('lower',~high),('higher',high)]:
        row={'group':name,'n':int(m.sum()),'modal_ties':int((ties&m).sum())}
        if m.any():
            row.update(mean_accuracy_pct=float(100*(mean[m]==actual[m]).mean()),modal_accuracy_pct=float(100*(modal[m]==actual[m]).mean()),always_up_pct=float(100*(actual[m]==1).mean()),
                       modal_no_ties_accuracy_pct=float(100*(raw_modal[m&~ties]==actual[m&~ties]).mean()),modal_no_ties_n=int((m&~ties).sum()),
                       council_mae_pp=float(d.error_pp.to_numpy()[m].mean()),baseline_mae_pp=float(d.baseline_error_pp.to_numpy()[m].mean()),
                       excess_mae_pp=float(d.excess_error_pp.to_numpy()[m].mean()))
            for key,vals in [('mean_accuracy_pct',100*(mean==actual)),('modal_accuracy_pct',100*(modal==actual)),('excess_mae_pp',d.excess_error_pp)]:
                row[key+'_ci95']=interval(boot(d,vals,m))
        rows.append(row)
    differences={k:contrast(d,v,high) for k,v in {'mean_accuracy_pct':100*(mean==actual),'modal_accuracy_pct':100*(modal==actual),'excess_mae_pp':d.excess_error_pp}.items()} if high.any() and (~high).any() else {}
    return {'band_pp':band,'cutoff':cutoff,'groups':rows,'differences':differences,'ties':int(ties.sum()),'modal_mean_mismatches_no_ties':int(((raw_modal!=mean)&~ties).sum()),
            'high_modal_mean_mismatches':int(((raw_modal!=mean)&high).sum())},mean,modal,actual,counts,ties
def run():
    full=base.load_panel(); d=full[full.risk_balanced].reset_index(drop=True).copy()
    s=pd.read_csv(ROOT/'data/source_forecasts.csv')
    ftable=s.groupby(['batch','asset_id','framework']).predicted_return_pp.mean().unstack('framework')
    ftable=ftable.reindex(pd.MultiIndex.from_frame(d[['batch','asset_id']]))
    f=ftable.to_numpy(); assert np.allclose(f.mean(1),d.predicted_return_pp,atol=1e-10)
    r,mean,modal,actual,counts,ties=direction_summary(d,f)
    out={'version':'2.0.0','seed':SEED,'bootstrap_reps':REPS,'outcome_cutoff':'2026-10-08','revision_date':'2026-10-14','direction':r}
    # Threshold grid is descriptive; it is not a search for a preferred cutoff.
    grid=[]
    for band in (0,.5,1,2):
        fs=sign(f,band); ct=np.column_stack([(fs==c).sum(1) for c in (-1,0,1)])
        tie=(ct==ct.max(1)[:,None]).sum(1)>1
        mn=sign(f.mean(1),band); ac=sign(d.actual_return_pp.to_numpy(),band)
        mo=np.where(tie,mn,np.array([-1,0,1])[ct.argmax(1)])
        for cutoff in (4,5,6,7):
            hi=ct.max(1)>=cutoff
            for name,m in [('higher',hi),('lower',~hi)]:
                grid.append({'band_pp':band,'cutoff':cutoff,'group':name,'n':int(m.sum()),'mean_accuracy_pct':float(100*(mn[m]==ac[m]).mean()) if m.any() else None,'modal_accuracy_pct':float(100*(mo[m]==ac[m]).mean()) if m.any() else None})
    pd.DataFrame(grid).to_csv(ROOT/'results/direction_thresholds.csv',index=False)
    levels=[]
    for n in range(3,8):
        m=counts.max(1)==n
        levels.append({'agreeing_frameworks':n,'n':int(m.sum()),'mean_accuracy_pct':float(100*(mean[m]==actual[m]).mean()) if m.any() else None,'modal_accuracy_pct':float(100*(modal[m]==actual[m]).mean()) if m.any() else None})
    out['agreement_levels']=levels
    out['confusion_matrices']={name:[[int(((pred==a)&(actual==b)).sum()) for b in (-1,0,1)] for a in (-1,0,1)] for name,pred in [('mean_sign',mean),('modal_mean_tie_fallback',modal),('always_up',np.ones(len(d)))]}
    out['confusion_axes']={'rows':'forecast down,flat,up','columns':'outcome down,flat,up'}
    # Conditional contrasts and observed-period sensitivity, not future-regime CIs.
    out['by_batch']={};out['leave_one_batch_out']=[]
    hi=counts.max(1)>=6
    for b in (3,4,5,6):
        m=d.batch.eq(b).to_numpy()
        out['by_batch'][str(b)]={'mean_accuracy_gap_pct':float(100*((mean==actual)[m&hi].mean()-(mean==actual)[m&~hi].mean())),
             'modal_accuracy_gap_pct':float(100*((modal==actual)[m&hi].mean()-(modal==actual)[m&~hi].mean()))}
        sub=d[~m].reset_index(drop=True); subf=f[~m]
        rr,*_=direction_summary(sub,subf)
        _,qdelta=base.quartile_results(sub)
        out['leave_one_batch_out'].append({'omitted':b,'mean_accuracy_gap_pct':rr['differences']['mean_accuracy_pct']['estimate'],
            'modal_accuracy_gap_pct':rr['differences']['modal_accuracy_pct']['estimate'],'disagreement_excess_gap_pp':qdelta['excess_error_pp']['estimate']})
    out['direction_subgroups']={}
    for label,m in [('equities',d.asset_class.eq('equity')),('original_cohort',d.original_membership_all)]:
        rr,*_=direction_summary(d[m].reset_index(drop=True),f[m])
        out['direction_subgroups'][label]=rr
    extended=full[full.risk_pp_60.notna() & (full.risk_pp_60>0)].reset_index(drop=True)
    # Rebuild extended matrix from all source rows, not primary-only matrix.
    ef=s.groupby(['batch','asset_id','framework']).predicted_return_pp.mean().unstack('framework').reindex(pd.MultiIndex.from_frame(extended[['batch','asset_id']])).to_numpy()
    out['direction_subgroups']['expanded_risk_valid']=direction_summary(extended,ef)[0]
    out['direction_stratified']={}
    for metric in ('risk_pp_60','momentum_pp'):
        bands=np.zeros(len(d),int)
        for b,g in d.groupby('batch'):
            ix=g.sort_values([metric,'asset_id']).index;bands[ix]=np.arange(len(ix))*5//len(ix)
        rows=[]
        for b in (3,4,5,6):
            for k in range(5):
                m=d.batch.eq(b).to_numpy()&(bands==k)
                if (m&hi).any() and (m&~hi).any():
                    rows.append({'batch':b,'bin':k+1,'n':int(m.sum()),'mean_gap_pct':float(100*((mean==actual)[m&hi].mean()-(mean==actual)[m&~hi].mean())),
                         'modal_gap_pct':float(100*((modal==actual)[m&hi].mean()-(modal==actual)[m&~hi].mean()))})
        out['direction_stratified'][metric]={'bin_contrasts':rows,'n_covered':sum(x['n'] for x in rows),'weighted_mean_gap_pct':float(np.average([x['mean_gap_pct'] for x in rows],weights=[x['n'] for x in rows])),
            'weighted_modal_gap_pct':float(np.average([x['modal_gap_pct'] for x in rows],weights=[x['n'] for x in rows]))}
    # Resample complete assets and recompute rank membership for every replicate.
    ids=sorted(d.asset_id.unique()); ids_index={a:i for i,a in enumerate(ids)}
    orders={metric:[g.sort_values([metric,'asset_id']).index.to_numpy() for _,g in d.groupby('batch')] for metric in ('disagreement_pp','risk_pp_60')}
    weights=np.random.default_rng(SEED).multinomial(len(ids),np.full(len(ids),1/len(ids)),size=REPS)
    groups=np.array([ids_index[a] for a in d.asset_id]);err=d.error_pp.to_numpy();ex=d.excess_error_pp.to_numpy()
    selector_draws=[];quartile_draws=[]
    for w in weights:
        retained={};delta=[]
        for metric,batches in orders.items():
            selected=[]
            for order in batches:
                ix=np.repeat(order,w[groups[order]])
                selected.extend(ix[:int(np.ceil(len(ix)*.25))])
                if metric=='disagreement_pp':
                    bins=np.arange(len(ix))*4//len(ix)
                    delta.append(ex[ix[bins==3]].mean()-ex[ix[bins==0]].mean())
            retained[metric]=err[selected].mean()
        selector_draws.append(retained['risk_pp_60']-retained['disagreement_pp']);quartile_draws.append(np.mean(delta))
    out['reranked_bootstrap']={'quartile_excess_gap_ci95_pp':interval(quartile_draws),'volatility_minus_disagreement_selector_ci95_pp':interval(selector_draws),'reps':REPS,'seed':SEED}
    # Scale-aware errors and a residual spread score; no outcome-trained selector.
    d['normalized_disagreement']=d.disagreement_pp/d.risk_pp_60
    d['residual_disagreement']=0.
    for _,g in d.groupby('batch'):
        x=np.column_stack([np.ones(len(g)),np.log(g.risk_pp_60)])
        y=np.log1p(g.disagreement_pp);d.loc[g.index,'residual_disagreement']=y-x@np.linalg.lstsq(x,y,rcond=None)[0]
    qr=base.quartiles(d); scaled=[]
    for q,g in qr.groupby('quartile'):
        scaled.append({'quartile':int(q),'n':len(g),'risk_scaled_error':float((g.error_pp/g.risk_pp_60).mean()),
            'risk_scaled_baseline':float((g.baseline_error_pp/g.risk_pp_60).mean()),'pooled_absolute_skill':float(1-g.error_pp.sum()/g.baseline_error_pp.sum())})
    out['scaled_quartiles']=scaled
    out['risk_coverage_dense']=[]
    for metric in ('disagreement_pp','risk_pp_60','normalized_disagreement','residual_disagreement'):
        for coverage in [k/20 for k in range(1,21)]:
            g=d.loc[ranked_indices(d,metric,coverage)]
            out['risk_coverage_dense'].append({'selector':metric,'coverage':float(coverage),**summary(g),'scaled_error':float((g.error_pp/g.risk_pp_60).mean()),'pooled_absolute_skill':float(1-g.error_pp.sum()/g.baseline_error_pp.sum())})
    out['frameworks']={}
    for i,name in enumerate(ftable.columns):
        out['frameworks'][name]={'mae_pp':float(np.abs(f[:,i]-d.actual_return_pp.to_numpy()).mean()),'direction_pct':float(100*(sign(f[:,i])==actual).mean())}
    out['average_framework_mae_pp']=float(np.abs(f-d.actual_return_pp.to_numpy()[:,None]).mean())
    out['framework_correlations']={'labels':list(ftable.columns),'pearson':np.corrcoef(f,rowvar=False).tolist(),
        'by_batch':{str(b):np.corrcoef(f[d.batch.eq(b)],rowvar=False).tolist() for b in (3,4,5,6)}}
    modes=[]
    for framework,g in s.groupby('framework'):
        pivot=g.pivot(index=['batch','asset_id'],columns='mode',values='predicted_return_pp').reindex(pd.MultiIndex.from_frame(d[['batch','asset_id']]))
        if pivot.shape[1]==2:
            a,b=pivot.to_numpy().T
            modes.append({'framework':framework,'mode_correlation':float(np.corrcoef(a,b)[0,1]),'variance_of_average_divided_by_mean_mode_variance':float(np.var((a+b)/2)/np.mean([np.var(a),np.var(b)]))})
    out['two_mode_dependence']=modes
    out['descriptive_quantiles']={key:{str(q):float(np.quantile(vals,q)) for q in (0,.25,.5,.75,.9,.95,1)} for key,vals in
        {'abs_forecast_pp':abs(d.predicted_return_pp),'realized_return_pp':d.actual_return_pp,'disagreement_pp':d.disagreement_pp,'risk_pp':d.risk_pp_60,'horizon_days':d.horizon_days}.items()}
    out['forecast_outcome_pearson']=float(np.corrcoef(d.predicted_return_pp,d.actual_return_pp)[0,1])
    # Unfitted diagnostics, not a newly selected or optimized trading model.
    momentum = d.momentum_pp.to_numpy()
    forecasts = {'no_change':np.zeros(len(d)), 'council_mean':f.mean(1),
                 'council_median':np.median(f,axis=1),
                 'last_60_observation_return':momentum}
    out['benchmark_diagnostics'] = {}
    for name,pred in forecasts.items():
        losses=np.abs(pred-d.actual_return_pp.to_numpy())
        out['benchmark_diagnostics'][name]={'mae_pp':float(losses.mean()),
            'difference_vs_no_change_pp':float((losses-d.baseline_error_pp).mean()),
            'difference_ci95_pp':interval(boot(d,losses-d.baseline_error_pp)),
            'direction_pct':float(100*(sign(pred)==actual).mean())}
    # Retrospective signed-momentum control; outcome-free covariates are not
    # enough to make an outcome-fitted model historically deployable.
    x0,names0=base.design(d)
    signed=np.arcsinh(momentum/10);signed=(signed-signed.mean())/signed.std()
    x=np.column_stack([x0,signed]);names=names0+['signed_momentum']
    out['signed_momentum_regression']={}
    for target,y in [('log_error',np.log1p(d.error_pp.to_numpy())),('excess_error_pp',d.excess_error_pp.to_numpy())]:
        coef=np.linalg.lstsq(x,y,rcond=None)[0]; draws=[]
        for w in weights[:2000]:
            sw=np.sqrt(w[groups]);draws.append(np.linalg.lstsq(x*sw[:,None],y*sw,rcond=None)[0])
        draws=np.array(draws)
        out['signed_momentum_regression'][target]={'n':len(d),'parameter_count':x.shape[1],
            'r_squared':float(1-np.sum((y-x@coef)**2)/np.sum((y-y.mean())**2)),
            'coefficients':{name:{'estimate':float(coef[j]),'ci95':interval(draws[:,j])} for j,name in enumerate(names)}}
    out['spread_coverage_diagnostic']={str(k):float((d.error_pp<=k*d.disagreement_pp).mean()) for k in (1,2,3)}
    out['spread_coverage_note']='Empirical coverage of mean +/- kD; k is not a normal-theory confidence level and no probabilistic calibration is implied.'
    out['cohort']={'matched':len(full),'valid_risk':len(extended),'primary':len(d),'excluded_risk_records':len(full)-len(extended),'split_suspect_records':int(full.risk_history_suspect_action.astype(str).str.lower().eq('true').sum()),
         'entry_delay_days_counts':{str(k):int(n) for k,n in (pd.to_datetime(d.entry)-pd.to_datetime(d.issued)).dt.days.value_counts().sort_index().items()},
         'retained':summary(extended[extended.risk_balanced]),'excluded':summary(extended[~extended.risk_balanced])}
    out['class_by_quartile']=pd.crosstab(qr.asset_class,qr.quartile).to_dict()
    out['class_in_selectors']={metric:d.loc[ranked_indices(d,metric,.25)].asset_class.value_counts().to_dict() for metric in ('disagreement_pp','risk_pp_60')}
    out['window_selection_overlap']={}
    ref=set(ranked_indices(d,'risk_pp_60',.25))
    for w in (20,90):
        keep=set(ranked_indices(d,f'risk_pp_{w}',.25));out['window_selection_overlap'][str(w)]={'intersection':len(ref&keep),'jaccard':len(ref&keep)/len(ref|keep)}
    x,names=base.design(d)
    out['regression_diagnostics']={'n':len(d),'parameter_count':x.shape[1],'condition_number':float(np.linalg.cond(x)),
        'vif':{name:float(1/(1-(1-np.sum((x[:,j]-np.delete(x,j,1)@np.linalg.lstsq(np.delete(x,j,1),x[:,j],rcond=None)[0])**2)/np.sum((x[:,j]-x[:,j].mean())**2)))) for j,name in enumerate(names) if name in ('log_risk','forecast_magnitude','momentum','log_disagreement')}}
    out['regression_fit_diagnostics']={}
    for name,y in [('log_error',np.log1p(d.error_pp.to_numpy())),('excess_error_pp',d.excess_error_pp.to_numpy()),('raw_error_pp',d.error_pp.to_numpy())]:
        coef=np.linalg.lstsq(x,y,rcond=None)[0];sse=np.sum((y-x@coef)**2)
        partial={}
        for j,key in enumerate(names):
            if key in ('log_risk','forecast_magnitude','momentum','log_disagreement'):
                reduced=np.delete(x,j,axis=1);sse0=np.sum((y-reduced@np.linalg.lstsq(reduced,y,rcond=None)[0])**2)
                partial[key]=float((sse0-sse)/sse0)
        out['regression_fit_diagnostics'][name]={'residual_standard_error':float(np.sqrt(sse/(len(d)-x.shape[1]))),
            'r_squared':float(1-sse/np.sum((y-y.mean())**2)),'partial_r_squared':partial}
        if name=='raw_error_pp':
            draws=[]
            for w in weights[:2000]:
                sw=np.sqrt(w[groups]);draws.append(np.linalg.lstsq(x*sw[:,None],y*sw,rcond=None)[0])
            out['regression_fit_diagnostics'][name]['coefficients']={key:{'estimate':float(coef[j]),'ci95':interval(np.array(draws)[:,j])} for j,key in enumerate(names)}
    qd=base.quartiles(d);q=qd.quartile.to_numpy()
    rmse_draws={}
    out['rmse_excess_diagnostic']={}
    for k in (1,2,3,4):
        m=q==k
        draws=np.sqrt(boot(d,err**2,m))-np.sqrt(boot(d,d.baseline_error_pp.to_numpy()**2,m))
        rmse_draws[k]=draws
        out['rmse_excess_diagnostic'][str(k)]={'estimate_pp':float(np.sqrt(np.mean(err[m]**2))-np.sqrt(np.mean(d.baseline_error_pp.to_numpy()[m]**2))),'ci95_pp':interval(draws)}
    out['rmse_excess_diagnostic']['high_minus_low_ci95_pp']=interval(rmse_draws[4]-rmse_draws[1])
    out['selector_leave_one_batch_out']=[]
    for b in (3,4,5,6):
        sub=d[d.batch.ne(b)].reset_index(drop=True)
        vals={metric:float(sub.loc[ranked_indices(sub,metric,.25),'error_pp'].mean()) for metric in ('risk_pp_60','disagreement_pp')}
        out['selector_leave_one_batch_out'].append({'omitted':b,'volatility_minus_disagreement_mae_pp':vals['risk_pp_60']-vals['disagreement_pp']})
    # Larger cross-asset blocks as a dependence sensitivity; no common-regime fix.
    grouping=pd.read_csv(ROOT/'data/asset_dependency_groups.csv').set_index('asset_id').dependency_group
    dg=d.asset_id.map(grouping);assert dg.notna().all()
    block_labels=sorted(dg.unique());block_idx=np.array([block_labels.index(v) for v in dg])
    block_weights=np.random.default_rng(SEED).multinomial(len(block_labels),np.full(len(block_labels),1/len(block_labels)),size=REPS)
    def block_mean(values,mask):
        sums=np.bincount(block_idx[mask],weights=np.asarray(values,float)[mask],minlength=len(block_labels))
        ns=np.bincount(block_idx[mask],minlength=len(block_labels));denom=block_weights@ns
        return np.divide(block_weights@sums,denom,out=np.full(REPS,np.nan),where=denom>0)
    masks={metric:d.index.isin(ranked_indices(d,metric,.25)) for metric in ('risk_pp_60','disagreement_pp')}
    draws={'mean_direction_gap_points':block_mean(100*(mean==actual),hi)-block_mean(100*(mean==actual),~hi),
        'modal_direction_gap_points':block_mean(100*(modal==actual),hi)-block_mean(100*(modal==actual),~hi),
        'quartile_excess_gap_pp':block_mean(ex,q==4)-block_mean(ex,q==1),
        'selector_volatility_minus_disagreement_pp':block_mean(err,masks['risk_pp_60'])-block_mean(err,masks['disagreement_pp'])}
    out['dependency_block_sensitivity']={'groups':len(block_labels),'assets_per_group':d.groupby(dg).asset_id.nunique().to_dict(),
        'ci95':{k:interval(v[np.isfinite(v)]) for k,v in draws.items()},'valid_draws':{k:int(np.isfinite(v).sum()) for k,v in draws.items()},
        'scope':'Resample whole equity sectors and non-equity asset classes with all their assets/periods. Fixed archived rank membership, unequal block sizes, few groups, and no resampling of common market periods limit inference.'}
    out['precision_reference']={'candidate_bounds_pp':[.5,1.,2.],'status':'Retrospective interpretation grid, not a preregistered equivalence margin; no equivalence claim is made.'}
    ratio=(1+d.predicted_return_pp/100)/(1+d.predicted_anchor_pp/100)
    aligned=np.isclose(100*((1+d.actual_anchor_pp/100)*ratio-1),d.actual_return_pp,atol=1e-6,rtol=0)
    aligned_panel=d[aligned].copy()
    anchor=aligned_panel.copy();anchor['error_pp']=abs(anchor.predicted_anchor_pp-anchor.actual_anchor_pp)
    anchor['baseline_error_pp']=abs(anchor.actual_anchor_pp);anchor['excess_error_pp']=anchor.error_pp-anchor.baseline_error_pp
    anchor['disagreement_pp']=anchor.disagreement_anchor_pp
    out['anchor_basis_diagnostic']={'primary_records_with_mismatched_anchor_basis':int((~aligned).sum()),
        'entry_scoring_excluding_mismatches':base.quartile_results(aligned_panel.reset_index(drop=True))[1]['excess_error_pp'],
        'anchor_scoring_excluding_mismatches':base.quartile_results(anchor.reset_index(drop=True))[1]['excess_error_pp'],
        'note':'Two Batch 3 commodity forecast rebasing factors differ from historical outcome anchor ratios. Primary entry scoring is retained; original-anchor sensitivity is additionally restricted to compatible bases.'}
    pd.DataFrame(out['risk_coverage_dense']).to_csv(ROOT/'results/risk_coverage_dense.csv',index=False)
    (ROOT/'results/results_v2.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:out[k] for k in ('direction','reranked_bootstrap','by_batch','regression_diagnostics','cohort')},indent=2))
if __name__=='__main__':run()
