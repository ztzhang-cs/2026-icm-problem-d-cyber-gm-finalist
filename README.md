# 2026 ICM Problem D: Cyber-GM V3.1

Cyber-GM V3.1 is a Finalist Award solution for 2026 ICM Problem D. The project builds a data-driven modeling pipeline for the Golden State Warriors case, combining macroeconomic sensitivity, player commercial value, expansion-draft protection logic, and dynamic ticket pricing into one reproducible Python workflow.

This repository contains the cleaned code and data package prepared for public release after the competition.

## Project Summary

- Competition: 2026 Interdisciplinary Contest in Modeling (ICM)
- Problem: Problem D
- Award: Finalist Award
- Case team: Golden State Warriors
- Model name: Cyber-GM V3.1

## What the Pipeline Does

- Loads four normalized input tables for the 2015-2025 seasons.
- Estimates or falls back to a ticket-demand model using macroeconomic and game-level features.
- Computes a WACC-based season finance report.
- Scores player commercial value using performance and social-media proxy features.
- Produces an expansion protection list with a configurable top-k limit.
- Optimizes game ticket prices under a simplified revenue and fan-conversion objective.

## Repository Layout

```text
.
├── config.yaml              # Project paths and model parameters
├── column_map.json          # Column aliases used when loading input tables
├── data_io.py               # Table discovery, reading, and column mapping helpers
├── model.py                 # Core model modules
├── run_pipeline.py          # Main entry point
├── requirements.txt         # Python dependencies
├── data/
│   ├── raw/                 # Source and reference CSV data
│   └── processed/           # Four clean tables used by the pipeline
└── docs/
    └── model_v3_1.md        # Full model write-up from the original project
```

Generated outputs are written to `out_v31/` and are intentionally ignored by Git.

## Quick Start

```bash
pip install -r requirements.txt
python run_pipeline.py
```

After a successful run, the main outputs are:

- `out_v31/manifest.json`: input files used, mapped columns, missing fields, and row counts.
- `out_v31/games_priced.csv`: optimized ticket price and predicted attendance for each game.
- `out_v31/protection_list.csv`: expansion protection list by season.
- `out_v31/season_report.csv`: revenue, cost, profit proxy, wins, and WACC by season.
- `out_v31/demand_fit.txt`: demand-model fit summary or fallback note.

## Data Notes

The project uses a compact processed dataset so that the code can run without the original zip bundle. The processed tables are in `data/processed/`:

- `macro_table.csv`
- `games_table.csv`
- `roster_table.csv`
- `finance_table.csv`

The `data/raw/` folder keeps the smaller source CSV files used as references when building those processed tables. Large PDFs, cache files, duplicate zip extracts, and old generated outputs were removed from this cleaned version.

## Modeling Caveats

Some fields are synthetic or backfilled because fine-grained historical data was not available in the original project. For example, game-level attendance and player-level social metrics are proxy values. The current code is designed to be replaceable: if better game, roster, finance, or macro tables become available, keep the same column names and replace the corresponding processed CSV.
