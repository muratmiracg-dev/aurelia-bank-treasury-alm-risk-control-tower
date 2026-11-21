# Validation report

## Verified analytical snapshot

| Test | Result |
|---|---:|
| Automated tests | 46 passed |
| Line coverage | 93.88% (above the 90% quality gate) |
| Data-quality controls | 10 / 10 passed |
| Accounting difference | effectively zero |
| Principal cash-flow maximum reconciliation error | below TRY 0.0001 million |
| IRRBB scenarios | 6 / 6 present |
| Curve points | 19 for each of TRY, USD and EUR |
| Open risk-limit breaches | 2 (FX open position; combined survival horizon) |

## Independent reasonableness checks

- A parallel rate increase lowers EVE because the TRY asset duration exceeds the effective
  liability duration.
- Parallel NII effects are symmetric by construction under the static balance sheet.
- The combined liquidity scenario is more severe than market-wide, idiosyncratic and base
  scenarios.
- The rapid-digital-run scenario is more severe than combined stress, recognises 55% of
  30-day outflows on day 1 and 85% by day 7, and produces a 5-day survival horizon.
- The survival horizon is the last whole day before cumulative net liquidity turns negative,
  interpolated linearly between ladder points. Combined stress is TRY 24.95bn positive on day 7
  and TRY 3.24bn negative on day 30, so it survives 27 days and breaches the 30-day limit.
- Base HQLA reconciles to TRY 59.40bn; the scenario-specific market-value overlay explains
  the full TRY 1.46bn reduction to stressed HQLA.
- FX hedge overlays reduce, rather than amplify, the absolute USD and EUR open positions.
- The synthetic balance sheet reconciles assets to liabilities plus equity.

## Known validation limits

- No independent market system was available for trade-level PV replication.
- Behavioural deposit and prepayment models are transparent assumptions, not statistically
  estimated production models.
- LCR and NSFR are management proxies and were not reconciled to a regulatory return.
- Rapid-digital-run parameters are expert assumptions for vulnerability exploration, not an
  empirical forecast or a backtested runoff distribution.
- Hedge effectiveness excludes basis, collateral, CVA, transaction cost and accounting
  designation effects.

Validation status: **fit for portfolio demonstration and controlled analytical learning;
not approved for production or regulatory reporting.**
