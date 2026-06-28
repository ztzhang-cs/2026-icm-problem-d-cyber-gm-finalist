# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List, Any
import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
except Exception:
    sm = None

def clip(x, lo, hi): return max(lo, min(hi, x))
def safe_log(x, eps=1e-12): return np.log(np.maximum(x, eps))

@dataclass
class MSMParams:
    alpha: float = 0.0
    beta_p: float = -0.8
    beta_I: float = 0.6
    beta_U: float = -0.2
    gamma_weekend: float = 0.08
    gamma_holiday: float = 0.10
    gamma_opp_smv: float = 0.02
    gamma_rankdiff: float = -0.01
    gamma_month: float = 0.00

@dataclass
class WACCParams:
    tax_rate: float = 0.21
    equity_risk_premium: float = 0.05
    beta_equity: float = 1.2
    credit_spread: float = 0.02

class MSMModule:
    def __init__(self, params: MSMParams, wacc: WACCParams):
        self.p = params
        self.wacc_p = wacc
        self._fit = None

    @staticmethod
    def prepare_macro(macro: pd.DataFrame) -> pd.DataFrame:
        m = macro.copy()
        for c in ["year","r_t","cpi","y_msa","unemp"]:
            if c not in m.columns:
                m[c] = np.nan
        if m["unemp"].isna().all():
            m["unemp"] = 0.0
        return m

    def fit_demand(self, games: pd.DataFrame, macro: pd.DataFrame) -> Optional[Any]:
        if sm is None:
            return None
        g = games.copy()
        m = self.prepare_macro(macro)
        g = g.merge(m[["year","cpi","y_msa","unemp"]], left_on="season_year", right_on="year", how="left")
        g["ln_q"] = safe_log(g["attendance_rate"].astype(float))
        g["ln_p_real"] = safe_log(g["base_price_usd"].astype(float) / g["cpi"].astype(float))
        g["ln_income"] = safe_log(g["y_msa"].astype(float))
        for col in ["weekend","holiday","opp_smv","rank_diff","month"]:
            if col not in g.columns:
                g[col] = 0.0
        X_cols = ["ln_p_real","ln_income","unemp","weekend","holiday","opp_smv","rank_diff","month"]
        X = sm.add_constant(g[X_cols])
        y = g["ln_q"]
        self._fit = sm.OLS(y, X, missing="drop").fit()
        return self._fit

    def predict_q(self, games: pd.DataFrame, macro: pd.DataFrame, price_col: str) -> pd.Series:
        g = games.copy()
        m = self.prepare_macro(macro)
        g = g.merge(m[["year","cpi","y_msa","unemp"]], left_on="season_year", right_on="year", how="left")
        P = g[price_col].astype(float)
        ln_p_real = safe_log(P / g["cpi"].astype(float))
        ln_income = safe_log(g["y_msa"].astype(float))
        unemp = g["unemp"].astype(float)
        weekend = g.get("weekend", 0).astype(float)
        holiday = g.get("holiday", 0).astype(float)
        opp_smv = g.get("opp_smv", 0).astype(float)
        rank_diff = g.get("rank_diff", 0).astype(float)
        month = g.get("month", 0).astype(float)

        if self._fit is not None:
            X = pd.DataFrame({
                "ln_p_real": ln_p_real, "ln_income": ln_income, "unemp": unemp,
                "weekend": weekend, "holiday": holiday, "opp_smv": opp_smv,
                "rank_diff": rank_diff, "month": month
            })
            X = sm.add_constant(X)
            ln_q = self._fit.predict(X)
        else:
            p = self.p
            ln_q = (p.alpha + p.beta_p*ln_p_real + p.beta_I*ln_income + p.beta_U*unemp
                    + p.gamma_weekend*weekend + p.gamma_holiday*holiday
                    + p.gamma_opp_smv*opp_smv + p.gamma_rankdiff*rank_diff + p.gamma_month*month)
        return pd.Series(np.clip(np.exp(ln_q), 0.0, 1.0), index=g.index)

    def compute_wacc(self, r_t: float, debt_ratio: float) -> float:
        eq = 1.0 - float(debt_ratio)
        wp = self.wacc_p
        Re = float(r_t) + wp.beta_equity * wp.equity_risk_premium
        Rd = float(r_t) + wp.credit_spread
        return eq*Re + float(debt_ratio)*Rd*(1.0-wp.tax_rate)

@dataclass
class SPVEParams:
    default_cpe: float = 0.02

class SPVEModule:
    def __init__(self, p: SPVEParams):
        self.p = p

    def smv(self, row: pd.Series, platforms: List[str]) -> float:
        lam = float(row.get("fit_lambda", 1.0))
        total = 0.0
        for k in platforms:
            F = float(row.get(f"followers_{k}", 0.0))
            E = float(row.get(f"engagement_{k}", 0.0))
            CPE = float(row.get(f"cpe_{k}", self.p.default_cpe))
            total += F * E * CPE
        return total * lam

    def add_values(self, roster: pd.DataFrame, platforms: List[str]) -> pd.DataFrame:
        out = roster.copy()
        out["smv"] = [self.smv(r, platforms) for _, r in out.iterrows()]
        out["prot_score"] = 0.6*out.get("ws",0).astype(float) + 0.4*out["smv"].astype(float)
        return out

@dataclass
class ERMParams:
    k_limit: int = 8

class ERMModule:
    def __init__(self, p: ERMParams):
        self.p = p

    def protection_list(self, roster_vals: pd.DataFrame) -> pd.DataFrame:
        return roster_vals.sort_values("prot_score", ascending=False).head(self.p.k_limit)

@dataclass
class TicketParams:
    R_aux_usd: float = 35.0
    mu: float = 0.5
    xi_conv: float = 0.02
    clv_fan_usd: float = 5000.0
    price_bounds: Tuple[float,float] = (10.0, 800.0)

class TicketModule:
    def __init__(self, msm: MSMModule, p: TicketParams):
        self.msm = msm
        self.p = p

    def solve_price(self) -> float:
        K = self.p.R_aux_usd + self.p.mu*self.p.xi_conv*self.p.clv_fan_usd
        b = self.msm.p.beta_p
        if b >= 0 or abs(1+b) < 1e-6:
            return 150.0
        return float(clip(-b*K/(1+b), self.p.price_bounds[0], self.p.price_bounds[1]))

    def optimize_games(self, games: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
        m = MSMModule.prepare_macro(macro)
        out = games.copy()
        out["opt_price_usd"] = self.solve_price()
        out["price_usd"] = out["opt_price_usd"]
        out["q_hat"] = self.msm.predict_q(out, m, price_col="price_usd")
        cap = out.get("capacity", 18000).astype(float)
        K = self.p.R_aux_usd + self.p.mu*self.p.xi_conv*self.p.clv_fan_usd
        out["obj_hat"] = (out["opt_price_usd"]+K)*out["q_hat"]*cap
        return out
