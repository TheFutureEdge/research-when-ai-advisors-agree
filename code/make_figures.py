"""Publication figures; values come exclusively from the frozen study results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.dates as mdates

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"paper/figures"
OUT.mkdir(parents=True,exist_ok=True)
R=json.loads((ROOT/"results/results.json").read_text())
D=pd.read_csv(ROOT/"data/primary_panel.csv")
BLUE="#175676"; GOLD="#B17C24"; ORANGE="#C55B38"; GREY="#68727B"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.labelsize":11,
                     "axes.titlesize":12,"xtick.labelsize":10,"ytick.labelsize":10,
                     "legend.fontsize":10,"axes.spines.top":False,"axes.spines.right":False,
                     "axes.edgecolor":"#79838B","text.color":"#202A32","axes.labelcolor":"#202A32",
                     "pdf.fonttype":42,"ps.fonttype":42,"savefig.facecolor":"white"})

def save(fig,name):
    fig.savefig(OUT/(name+".pdf"),bbox_inches="tight")
    fig.savefig(OUT/(name+".png"),dpi=180,bbox_inches="tight")
    plt.close(fig)

def intervals(ax,x,estimates,bounds,color,marker="o",label=None):
    bounds=np.array(bounds); estimates=np.array(estimates)
    ax.errorbar(x,estimates,yerr=np.vstack([estimates-bounds[:,0],bounds[:,1]-estimates]),
                fmt=marker+"-",color=color,capsize=3,lw=1.7,ms=5,label=label)

def workflow():
    fig,ax=plt.subplots(figsize=(8,5.2)); ax.axis("off"); ax.set(xlim=(0,1),ylim=(0,1))
    def box(x,y,w,h,title,body,color=BLUE):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.012",
                                  fc="#F4F7F9",ec=color,lw=1.1))
        ax.text(x+w/2,y+h*.72,title,ha="center",va="center",fontsize=12,fontweight="bold",color=color)
        ax.text(x+w/2,y+h*.32,body,ha="center",va="center",fontsize=10.5,linespacing=1.5)
    def arrow(a,b):
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=13,lw=1.2,color=GREY))
    box(.02,.78,.29,.17,"Source forecasts","10 configurations\n7 frameworks")
    box(.355,.78,.29,.17,"Matched panel","232 assets x 4 batches\n928 completed quarters")
    box(.69,.78,.29,.17,"Future outcomes","Native-currency returns\nMatched dates and splits")
    arrow((.315,.86),(.34,.86)); arrow((.65,.86),(.675,.86))
    box(.05,.45,.37,.20,"What the council says","Mean return; forecast dispersion\nUp / flat / down agreement")
    box(.58,.45,.37,.20,"What was already visible","Pre-generation daily volatility\nMomentum and asset class",GOLD)
    arrow((.45,.78),(.25,.66)); arrow((.56,.78),(.75,.66))
    box(.23,.10,.54,.22,"Does disagreement add information?","Forecast error versus no-change error\nRisk adjustment; selective evaluation")
    arrow((.23,.45),(.39,.33)); arrow((.76,.45),(.62,.33));
    ax.text(.5,.015,"A retrospective audit of future outcomes; no forecasts were regenerated.",ha="center",fontsize=10,color=GREY)
    save(fig,"01_study_design")

def timeline():
    fig,ax=plt.subplots(figsize=(8,3.5))
    for j,b in enumerate((3,4,5,6)):
        g=D[D.batch==b]; issued=pd.to_datetime(g.issued).min(); lo=pd.to_datetime(g.observed).min(); hi=pd.to_datetime(g.observed).max()
        ax.plot([issued,hi],[j,j],color=BLUE,lw=2)
        ax.plot(issued,j,"o",color=BLUE,ms=7)
        ax.plot([lo,hi],[j,j],color=GOLD,lw=7,solid_capstyle="butt")
        ax.text(issued,j-.19,issued.strftime("%d %b"),ha="center",fontsize=10)
        ax.text(hi,j+.21,hi.strftime("%d %b"),ha="center",fontsize=10,color=GOLD)
    ax.set_yticks(range(4),["Batch 3","Batch 4","Batch 5","Batch 6"])
    ax.invert_yaxis(); ax.set_ylim(3.5,-.5)
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b 2026"))
    ax.set_xlim(pd.Timestamp("2026-04-01"),pd.Timestamp("2026-10-15")); ax.set_xlabel("Calendar date")
    ax.plot([],[],"o-",color=BLUE,label="Generation and outcome window")
    ax.plot([],[],color=GOLD,lw=5,label="Target-close range")
    ax.legend(loc="upper left",bbox_to_anchor=(0,1.22),ncol=2,frameon=False)
    ax.grid(axis="x",alpha=.2); save(fig,"02_timing")

def quartiles():
    fig,axes=plt.subplots(1,2,figsize=(8,3.6),layout="constrained")
    qs=R["quartiles"]; x=np.arange(1,5)
    for field,color,label,marker in [("error_pp",BLUE,"Council forecast","o"),("baseline_error_pp",GREY,"No change","s")]:
        intervals(axes[0],x,[q[field] for q in qs],[q[field+"_ci95"] for q in qs],color,marker,label)
    axes[0].set(ylim=(0,32),ylabel="Mean absolute return error (pp)",title="A. Absolute error")
    axes[0].legend(frameon=False,loc="upper left")
    intervals(axes[1],x,[q["excess_error_pp"] for q in qs],[q["excess_error_pp_ci95"] for q in qs],BLUE)
    axes[1].axhline(0,color=GREY,ls="--",lw=1)
    axes[1].set(ylabel="Council error minus no-change error (pp)",title="B. Error beyond the baseline")
    for ax in axes:
        ax.set_xticks(x,["Lowest","Q2","Q3","Highest"]); ax.set_xlabel("Within-batch disagreement quartile")
        ax.grid(axis="y",alpha=.18)
    save(fig,"03_disagreement_and_baseline")

def correlations():
    fig,axes=plt.subplots(1,2,figsize=(8,3.6),layout="constrained")
    axes[0].scatter(D.risk_pp_60,D.disagreement_pp,s=12,alpha=.27,color=BLUE,rasterized=True)
    axes[0].set(xscale="log",yscale="log",xlabel="Historical volatility at horizon scale (pp)",ylabel="Council disagreement (pp)",title="A. Disagreement tracks visible risk")
    x=np.arange(4); w=.24
    series=[("disagreement_risk",BLUE,"Disagreement vs risk"),("risk_error",GOLD,"Risk vs error"),("disagreement_error",GREY,"Disagreement vs error")]
    for i,(key,color,label) in enumerate(series):
        axes[1].bar(x+(i-1)*w,[R["correlations"][str(b)][key] for b in (3,4,5,6)],w,color=color,label=label)
    axes[1].set_xticks(x,["B3","B4","B5","B6"]); axes[1].set(ylim=(0,.85),ylabel="Within-batch Spearman correlation",title="B. Rank relationships by batch")
    axes[1].legend(frameon=False,fontsize=8.5,loc="upper left"); axes[1].grid(axis="y",alpha=.18)
    save(fig,"04_visible_risk")

def coverage():
    fig,axes=plt.subplots(1,2,figsize=(8,3.8),layout="constrained")
    selectors=[("disagreement_pp",BLUE,"Least disagreement","o"),("risk_pp_60",GOLD,"Lowest historical volatility","s"),
               ("normalized_disagreement",ORANGE,"Lowest disagreement / volatility","^")]
    for metric,color,label,marker in selectors:
        records=[r for r in R["risk_coverage"] if r["selector"]==metric]
        x=[r["coverage"]*100 for r in records]
        axes[0].plot(x,[r["error_pp"] for r in records],marker+"-",color=color,label=label,lw=1.8,ms=5)
        intervals(axes[1],x,[r["excess_error_pp"] for r in records],[r["excess_ci95"] for r in records],color,marker)
    axes[0].axhline(R["primary"]["error_pp"],color=GREY,lw=1,ls=":")
    axes[1].axhline(0,color=GREY,lw=1,ls="--")
    axes[0].set(ylim=(0,22),ylabel="Mean absolute return error (pp)",title="A. Lower error among retained forecasts")
    axes[1].set(ylabel="Council error minus no-change error (pp)",title="B. Does selection beat the baseline?")
    for ax in axes:
        ax.set_xticks([25,50,75,100]); ax.set_xlabel("Forecasts retained within each batch (%)"); ax.grid(axis="y",alpha=.18)
    fig.legend(*axes[0].get_legend_handles_labels(),loc="outside lower center",ncol=1,frameon=False)
    save(fig,"05_selective_evaluation")

def adjusted():
    fig,axes=plt.subplots(1,2,figsize=(8,3.8),layout="constrained")
    keys=["log_risk","forecast_magnitude","momentum","log_disagreement"]
    labels=["Historical volatility","Forecast magnitude","Historical momentum","Council disagreement"]
    estimates=R["regressions"]["log_error"]
    for j,k in enumerate(keys):
        value=estimates[k]; lo,hi=value["ci95"]; color=BLUE if k=="log_disagreement" else GREY
        axes[0].errorbar(value["estimate"],j,xerr=[[value["estimate"]-lo],[hi-value["estimate"]]],fmt="o",color=color,capsize=3)
    axes[0].set_yticks(range(4),labels); axes[0].invert_yaxis(); axes[0].axvline(0,color=GREY,lw=1,ls="--")
    axes[0].set(xlabel="Coefficient per 1 SD of transformed predictor",title="A. Adjusted association with log(1 + error)")
    groups=R["risk_stratified"]["groups"]; x=np.array([0,1])
    for field,c,label,offset in [("error_pp",BLUE,"Council",-.1),("baseline_error_pp",GREY,"No change",.1)]:
        bounds=[r["error_ci95" if field=="error_pp" else "baseline_ci95"] for r in groups]
        intervals(axes[1],x+offset,[r[field] for r in groups],bounds,c,"o",label)
    axes[1].set_xticks(x,["Lower spread","Higher spread"])
    axes[1].set(ylim=(0,24),ylabel="Mean absolute return error (pp)",xlabel="Compared within volatility groups",title="B. Similar-risk comparison")
    axes[1].legend(frameon=False); axes[1].grid(axis="y",alpha=.18)
    save(fig,"06_adjusted_comparison")

def directional():
    fig,axes=plt.subplots(1,2,figsize=(8,3.6),layout="constrained")
    records=R["agreement_groups"][::-1]; x=np.array([0,1])
    intervals(axes[0],x,[r["direction_hit_pct"] for r in records],[r["direction_ci95"] for r in records],BLUE,"o","Council")
    axes[0].plot(x,[r["always_up_hit_pct"] for r in records],"s--",color=GREY,label="Always up")
    axes[0].set(ylim=(0,75),ylabel="Correct up / flat / down forecasts (%)",title="A. Directional agreement")
    axes[0].legend(frameon=False)
    intervals(axes[1],x,[r["error_pp"] for r in records],[r["error_ci95"] for r in records],BLUE,"o","Council")
    axes[1].plot(x,[r["baseline_error_pp"] for r in records],"s--",color=GREY,label="No change")
    axes[1].set(ylim=(0,25),ylabel="Mean absolute return error (pp)",title="B. Agreement is not return precision")
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.set_xticks(x,["Fewer than 6 of 7","At least 6 of 7"]); ax.set_xlabel("Frameworks sharing a direction"); ax.grid(axis="y",alpha=.18)
    save(fig,"07_direction_vs_magnitude")

def sensitivity():
    records=[("Primary balanced panel",R["high_minus_low"]["excess_error_pp"])]
    labels={"expanded_coverage":"Expanded coverage","equities_only":"Equities only","original_membership":"Published-cohort membership",
            "exclude_largest_1pct_errors":"Remove largest 1% of errors","median_aggregation":"Median council forecast","anchor_return_scoring":"Original anchor scoring"}
    for key,value in R["sensitivity"].items():
        records.append((labels[key],value["high_minus_low"]["excess_error_pp"]))
    fig,ax=plt.subplots(figsize=(8,3.8),layout="constrained")
    for j,(label,r) in enumerate(records):
        lo,hi=r["ci95"]; ax.errorbar(r["estimate"],j,xerr=[[r["estimate"]-lo],[hi-r["estimate"]]],fmt="o",capsize=4,color=BLUE if j==0 else GREY)
    ax.set_yticks(range(len(records)),[v[0] for v in records]); ax.invert_yaxis(); ax.axvline(0,color=GREY,ls="--",lw=1)
    ax.set_xlabel("High-minus-low disagreement gap in error beyond no change (pp)")
    ax.grid(axis="x",alpha=.18); save(fig,"08_robustness")

if __name__=="__main__":
    for function in (workflow,timeline,quartiles,correlations,coverage,adjusted,directional,sensitivity):
        function()
    print("Eight figures exported as vector PDF and inspection PNG.")
