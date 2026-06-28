# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

from data_io import load_column_map, load_project_tables
from model import MSMParams, WACCParams, MSMModule, SPVEParams, SPVEModule, ERMParams, ERMModule, TicketParams, TicketModule

def main():
    base_dir = Path(__file__).resolve().parent
    cfg = yaml.safe_load((base_dir / "config.yaml").read_text(encoding="utf-8"))
    out_dir = base_dir / cfg["paths"]["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    colmap = load_column_map(base_dir / "column_map.json")
    data_dir = cfg["paths"].get("data_dir", "")
    data_zip = cfg["paths"].get("data_zip", "")
    tables, report = load_project_tables(
        data_zip=str(base_dir / data_zip) if data_zip else "",
        data_dir=str(base_dir / data_dir) if data_dir else "",
        out_extract_dir=out_dir/"_extracted",
        column_map=colmap,
        pinned=cfg.get("schema", {})
    )
    (out_dir/"manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    macro = tables.get("macro", pd.DataFrame(columns=["year","r_t","cpi","y_msa","unemp"]))
    games = tables.get("games", pd.DataFrame(columns=["season_year","base_price_usd","attendance_rate","capacity"]))
    roster = tables.get("roster", pd.DataFrame(columns=["season_year","player","ws","salary_musd"]))
    finance = tables.get("finance", pd.DataFrame(columns=["season_year","revenue_musd","operating_cost_musd","salary_total_musd","tax_paid_musd","wins"]))

    # Normalize macro year
    if "year" not in macro.columns and "season_year" in macro.columns:
        macro = macro.rename(columns={"season_year":"year"})
    macro["year"] = pd.to_numeric(macro.get("year", np.nan), errors="coerce")

    # Defaults for games
    games["season_year"] = pd.to_numeric(games.get("season_year", np.nan), errors="coerce")
    for col in ["weekend","holiday","opp_smv","rank_diff","month"]:
        if col not in games.columns: games[col]=0.0
    if "capacity" not in games.columns: games["capacity"]=18000
    if "base_price_usd" not in games.columns: games["base_price_usd"]=150.0

    msm_params = MSMParams(**cfg["demand_model"]["params"])
    wacc_params = WACCParams(
        tax_rate=float(cfg["wacc"]["tax_rate"]),
        equity_risk_premium=float(cfg["wacc"]["equity_risk_premium"]),
        beta_equity=float(cfg["wacc"]["beta_equity"]),
        credit_spread=float(cfg["wacc"]["credit_spread"])
    )
    msm = MSMModule(msm_params, wacc_params)

    # Demand fit
    att = pd.to_numeric(games.get("attendance_rate", pd.Series(dtype=float)), errors="coerce")
    if cfg["demand_model"].get("use_statsmodels", True) and att.dropna().nunique() > 1:
        try:
            res = msm.fit_demand(games.dropna(subset=["attendance_rate"]), macro)
            if res is not None:
                (out_dir/"demand_fit.txt").write_text(str(res.summary()), encoding="utf-8")
        except Exception as e:
            (out_dir/"demand_fit.txt").write_text(f"Demand fit failed: {e}\nFallback to default parameters.", encoding="utf-8")
    else:
        (out_dir/"demand_fit.txt").write_text(
            "Demand fit skipped because attendance_rate has no usable variation.\n"
            "Fallback to configured default demand parameters.",
            encoding="utf-8"
        )

    # Ticket optimization
    tp = cfg["ticket"]
    ticket = TicketModule(msm, TicketParams(
        R_aux_usd=float(tp["R_aux_usd"]),
        mu=float(tp["mu"]),
        xi_conv=float(tp["xi_conv"]),
        clv_fan_usd=float(tp["clv_fan_usd"]),
        price_bounds=(float(tp["price_bounds"][0]), float(tp["price_bounds"][1]))
    ))

    games_ok = games.dropna(subset=["season_year"]).copy()
    macro_ok = macro.dropna(subset=["year"]).copy()
    if len(games_ok)>0 and len(macro_ok)>0:
        games_ok["season_year"] = games_ok["season_year"].astype(int)
        macro_ok["year"] = macro_ok["year"].astype(int)
        games_ok = games_ok[games_ok["season_year"].isin(macro_ok["year"].tolist())]
        if len(games_ok)>0:
            priced = ticket.optimize_games(games_ok, macro_ok)
            priced.to_csv(out_dir/"games_priced.csv", index=False)

    # SPVE + protection list
    platforms = [c.split("followers_",1)[1] for c in roster.columns if str(c).startswith("followers_")]
    if not platforms:
        platforms = ["ig","x"]
    spve = SPVEModule(SPVEParams())
    erm = ERMModule(ERMParams(k_limit=int(cfg["erm"]["k_limit"])))

    prot_rows=[]
    if "season_year" in roster.columns and roster["season_year"].notna().any():
        roster["season_year"] = pd.to_numeric(roster["season_year"], errors="coerce")
        for season in sorted(roster["season_year"].dropna().astype(int).unique().tolist()):
            r_s = roster[roster["season_year"].astype(int)==season].copy()
            r_vals = spve.add_values(r_s, platforms)
            plist = erm.protection_list(r_vals).assign(season_year=season)
            prot_rows.append(plist[["season_year","player","ws","smv","prot_score"]])
    if prot_rows:
        pd.concat(prot_rows, ignore_index=True).to_csv(out_dir/"protection_list.csv", index=False)

    # season report
    debt_ratio = float(cfg["wacc"].get("default_debt_ratio", 0.35))
    reps=[]
    if "season_year" in finance.columns and finance["season_year"].notna().any():
        finance["season_year"] = pd.to_numeric(finance["season_year"], errors="coerce")
        for season in sorted(finance["season_year"].dropna().astype(int).unique().tolist()):
            fin = finance[finance["season_year"].astype(int)==season].iloc[0]
            mac = macro_ok[macro_ok["year"].astype(int)==season]
            r_t = float(mac.iloc[0].get("r_t", np.nan)) if len(mac)>0 else np.nan
            r_use = (r_t/100.0) if (not np.isnan(r_t) and r_t>0.2) else r_t
            wacc = msm.compute_wacc(r_use, debt_ratio) if not np.isnan(r_use) else np.nan
            revenue = float(fin.get("revenue_musd", 0.0))
            cost = float(fin.get("operating_cost_musd", 0.0)) + float(fin.get("salary_total_musd", 0.0)) + float(fin.get("tax_paid_musd", 0.0))
            profit = revenue - cost
            reps.append({"season_year": season, "revenue_musd": revenue, "cost_musd": cost, "profit_musd": profit, "wins": float(fin.get("wins", np.nan)), "wacc": wacc})
    if reps:
        pd.DataFrame(reps).to_csv(out_dir/"season_report.csv", index=False)

    print(f"[OK] Done. Outputs in: {out_dir.resolve()}")
    print("Open out_v31/manifest.json to see which columns were missing and which files were used.")

if __name__ == "__main__":
    main()
