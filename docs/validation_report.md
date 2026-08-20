# Validation report

## Verified analytical snapshot

| Test | Result |
|---|---:|
| Automated tests | 43 passed |
| Statement coverage | 94.88% |
| Data-quality controls | 10 / 10 passed |
| Accounting difference | effectively zero |
| Principal cash-flow maximum reconciliation error | below TRY 0.0001 million |
| IRRBB scenarios | 6 / 6 present |
| Curve points | 19 for each of TRY, USD and EUR |
| Open risk-limit breaches | 1 |

## Independent reasonableness checks

- A parallel rate increase lowers EVE because the TRY asset duration exceeds the effective
  liability duration.
- Parallel NII effects are symmetric by construction under the static balance sheet.
- The combined liquidity scenario is more severe than market-wide, idiosyncratic and base
  scenarios.
- FX hedge overlays reduce, rather than amplify, the absolute USD and EUR open positions.
- The synthetic balance sheet reconciles assets to liabilities plus equity.

## Known validation limits

- No independent market system was available for trade-level PV replication.
- Behavioural deposit and prepayment models are transparent assumptions, not statistically
  estimated production models.
- LCR and NSFR are management proxies and were not reconciled to a regulatory return.
- Hedge effectiveness excludes basis, collateral, CVA, transaction cost and accounting
  designation effects.

Validation status: **fit for portfolio demonstration and controlled analytical learning;
not approved for production or regulatory reporting.**

