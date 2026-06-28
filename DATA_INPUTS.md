# Data Inputs

This project expects four normalized CSV tables in `data/processed/`. The loader also supports column aliases through `column_map.json`, but the cleanest workflow is to keep the canonical column names below.

## 1. `macro_table.csv`

Used by the macroeconomic sensitivity and WACC portions of the model.

Required columns:

- `year`: season year.
- `r_t`: 10-year Treasury yield, expressed in percentage-point units such as `2.136` for 2.136%.
- `cpi`: CPI index.
- `y_msa`: Bay Area income or GDP-per-capita proxy.
- `unemp`: unemployment rate. The current processed data uses `0.0` where this field was unavailable.

## 2. `games_table.csv`

Used by demand fitting and dynamic ticket pricing.

Required or expected columns:

- `season_year`: season year.
- `game_id`: unique game identifier.
- `month`: game month.
- `weekend`: `1` for weekend games, otherwise `0`.
- `holiday`: `1` for holiday games, otherwise `0`.
- `opp_smv`: opponent star-market-value proxy.
- `rank_diff`: relative ranking difference proxy.
- `capacity`: arena capacity.
- `base_price_usd`: baseline ticket price.
- `attendance_rate`: attendance as a share of capacity.

The original data did not include true game-level attendance, ticket price, and opponent feature data for every home game, so this table contains synthetic home-game rows anchored to available capacity, attendance, and average ticket-price assumptions.

## 3. `roster_table.csv`

Used by the star player value engine and expansion protection module.

Required or expected columns:

- `season_year`: season year.
- `player`: player name.
- `ws`: win-shares or performance proxy.
- `salary_musd`: salary in millions of USD.
- `followers_ig`, `engagement_ig`, `cpe_ig`: Instagram commercial-value inputs.
- `followers_x`, `engagement_x`, `cpe_x`: X/Twitter commercial-value inputs.
- `fit_lambda`: team-fit multiplier.

The current table uses proxy social-media values and simplified performance assumptions where player-level historical data was missing.

## 4. `finance_table.csv`

Used by the season-level finance report.

Required columns:

- `season_year`: season year.
- `revenue_musd`: revenue in millions of USD.
- `operating_cost_musd`: operating cost in millions of USD.
- `salary_total_musd`: total team salary in millions of USD.
- `tax_paid_musd`: luxury tax paid in millions of USD.
- `wins`: season wins.

Where detailed team finance values were unavailable, revenue and cost values were backfilled from available Forbes-style revenue and operating-income assumptions, adjusted across years with CPI.

## Replacing Data

To improve the model, replace any processed table with a higher-quality CSV that preserves the same canonical column names. The code will automatically use the updated files on the next run.
