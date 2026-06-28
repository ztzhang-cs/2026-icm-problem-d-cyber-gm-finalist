# -*- coding: utf-8 -*-
from __future__ import annotations
import re, json, zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd

def _norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())

def load_column_map(path: str|Path) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def extract_zip(zip_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)
    return out_dir

def _read_any_table(file_path: Path) -> Optional[pd.DataFrame]:
    suf = file_path.suffix.lower()
    try:
        if suf in [".csv", ".txt"]:
            return pd.read_csv(file_path)
        if suf in [".xlsx", ".xls"]:
            return pd.read_excel(file_path)
        if suf in [".parquet"]:
            return pd.read_parquet(file_path)
    except Exception:
        return None
    return None

def _best_match_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    cols = list(df.columns)
    ncols = [_norm(c) for c in cols]
    alias_norm = [_norm(a) for a in aliases]
    for a in alias_norm:
        if a in ncols:
            return cols[ncols.index(a)]
    for a in alias_norm:
        for i, c in enumerate(ncols):
            if a and a in c:
                return cols[i]
    return None

def map_columns(df: pd.DataFrame, mapping: Dict[str, List[str]]) -> Tuple[pd.DataFrame, Dict[str,str], List[str]]:
    out = df.copy()
    used, missing = {}, []
    for target, aliases in mapping.items():
        col = _best_match_col(out, aliases)
        if col is None:
            missing.append(target)
        else:
            used[target] = col
    out = out.rename(columns={used[t]: t for t in used})
    return out, used, missing

def discover_tables(data_dir: Path) -> Dict[str, Path]:
    files = [p for p in data_dir.rglob("*") if p.is_file() and p.suffix.lower() in [".csv",".xlsx",".xls",".parquet"]]
    def score(p: Path, kws: List[str]) -> int:
        name = p.name.lower()
        return sum(1 for k in kws if k in name)
    buckets = {
        "macro": ["macro","fred","cpi","treasury","income","unemp","msa"],
        "games": ["game","schedule","ticket","attendance","home","match"],
        "roster": ["roster","player","salary","contract","ws","stats"],
        "finance": ["finance","revenue","operating","forbes","tax","payroll","cap"]
    }
    picked = {}
    for k, kws in buckets.items():
        cand = sorted(files, key=lambda p: (score(p,kws), p.stat().st_size), reverse=True)
        if cand and score(cand[0], kws) > 0:
            picked[k] = cand[0]
    return picked

def load_project_tables(data_zip: str, data_dir: str, out_extract_dir: Path,
                        column_map: Dict, pinned: Dict[str,str]) -> Tuple[Dict[str,pd.DataFrame], Dict]:
    report = {"data_root": "", "tables": {}}
    if data_dir:
        root = Path(data_dir)
    else:
        zpath = Path(data_zip)
        if not zpath.exists():
            raise FileNotFoundError(f"Cannot find data_zip: {zpath}")
        root = extract_zip(zpath, out_extract_dir)
    report["data_root"] = str(root)

    discovered = discover_tables(root)
    tables: Dict[str,pd.DataFrame] = {}
    for tname in ["macro","games","roster","finance"]:
        f_override = pinned.get(f"{tname}_table","") or pinned.get(tname+"_table","")
        fpath = (root / f_override) if f_override else discovered.get(tname)
        if not fpath or not Path(fpath).exists():
            report["tables"][tname] = {"file": None, "missing": list(column_map[tname].keys()), "used": {}}
            continue
        df = _read_any_table(Path(fpath))
        if df is None:
            report["tables"][tname] = {"file": str(fpath), "error": "cannot read file", "missing": list(column_map[tname].keys()), "used": {}}
            continue
        mapped, used, missing = map_columns(df, column_map[tname])
        report["tables"][tname] = {"file": str(fpath), "missing": missing, "used": used, "rows": int(len(mapped)), "cols": int(mapped.shape[1])}
        tables[tname] = mapped
    return tables, report
