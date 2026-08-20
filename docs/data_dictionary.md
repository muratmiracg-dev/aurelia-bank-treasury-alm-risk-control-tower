# Core data dictionary

## Position table

| Field | Definition |
|---|---|
| `position_id` | Stable synthetic instrument identifier |
| `side` | Asset, liability or equity |
| `product` | Treasury or banking-book product class |
| `currency` | TRY, USD or EUR |
| `notional_ccy_mn` | Original-currency amount in millions |
| `balance_try_mn` | TRY-equivalent carrying amount in millions |
| `rate_type` | Fixed, floating, overnight, non-maturity or non-interest |
| `current_rate_pct` | Current nominal annual rate |
| `maturity_years` | Contractual or governed behavioural maturity |
| `repricing_years` | Time to next rate reset used in gap and NII views |
| `hqla_level` | LEVEL_1, LEVEL_2A, LEVEL_2B or NONE |
| `asf_factor` | Available Stable Funding factor used by the proxy |
| `rsf_factor` | Required Stable Funding factor used by the proxy |
| `deposit_beta` | Fraction of market-rate change passed to NMD pricing |

## Key measures

| Measure | Definition |
|---|---|
| Repricing gap | Rate-sensitive assets less liabilities in a time bucket |
| EVE | Present value of signed banking-book cash flows |
| Delta EVE | Shocked EVE less baseline EVE |
| NII | One-year interest income less interest expense |
| LCR proxy | Eligible HQLA divided by 30-day stressed net outflows |
| NSFR proxy | Available stable funding divided by required stable funding |
| Survival horizon | First cumulative stress point where liquidity turns negative |
| FX open position | Foreign-currency assets less liabilities plus hedge overlay |
| DV01 | EVE change from a one-basis-point parallel rate increase |

