# Analytical methodology

## 1. Decision scope

The platform supports an illustrative Asset-Liability Committee (ALCO) for a fictional
deposit bank. It links balance-sheet structure to five decision views:

1. contractual maturity and repricing mismatch;
2. economic value of equity (EVE);
3. one-year net interest income (NII) sensitivity;
4. liquidity and stable-funding resilience; and
5. structural foreign-exchange exposure and bounded hedge sizing.

No module executes a trade, changes a limit, or represents a regulatory submission.

## 2. Portfolio boundary

The bank portfolio contains deterministic synthetic assets, liabilities and Tier 1 capital.
Amounts are expressed in TRY million; USD and EUR positions retain original-currency
notionals and the official TCMB-linked FX translation rate. The accounting identity is
enforced to machine precision.

Floating instruments are treated as repricing at the next reset date for EVE. Fixed
instruments retain their contractual maturity. Non-maturity deposits use a transparent
six-point behavioural runoff profile. These are governed demonstration assumptions, not
calibrated customer behaviour.

## 3. Curve framework

The demo uses 19 IRRBB time bands and one synthetic zero curve per material currency.
The TRY curve is anchored to the observable policy environment; USD and EUR curves are
illustrative. Curve points are not claimed as executable market quotes. Users can replace
them through `config/assumptions.yml` without changing code.

## 4. Economic value

Signed position cash flows are discounted with interpolated currency zero rates:

`PV = cash flow / (1 + zero rate)^time`

EVE is the sum of asset and liability present values. The six prescribed Basel scenarios
are parallel up, parallel down, steepener, flattener, short-rate up and short-rate down.
TRY, USD and EUR shocks use the July 2024 Basel recalibration effective from 1 January
2026. Results are measured both in TRY million and as a share of synthetic Tier 1 capital.

## 5. Earnings view

NII uses a one-year static-balance-sheet horizon. Positions that reprice within the year
receive the remaining-horizon portion of the shock. Pass-through is explicit by rate type;
non-maturity deposit sensitivity uses the configured deposit beta. Fixed positions do not
reprice within this simplified view.

## 6. Liquidity and funding

The liquidity module calculates:

- eligible HQLA after configured haircuts;
- 30-day stressed outflows by funding type;
- conservative recognised inflows;
- an LCR decision proxy;
- cumulative survival horizon; and
- an NSFR decision proxy from visible ASF/RSF factors.

The fifth scenario, `rapid_digital_run`, is a severe exploratory management stress. It
combines elevated retail and term-deposit runoff, full wholesale runoff, higher committed
facility utilisation, weaker inflow realisation, front-loaded day-1/day-7 withdrawals and
an additional market-value shock to already eligible HQLA. Scenario-adjusted HQLA is:

`stressed HQLA = balance × (1 - regulatory haircut) × (1 - market-value shock)`

The digital-run timing profile recognises 55% of 30-day outflows on day 1 and 85% by day 7.
These internally governed assumptions are deliberately visible in YAML and are not presented
as historical estimates, legal thresholds or regulatory calibrations.

The ratios deliberately retain the label `proxy`. A regulatory calculation requires more
granular counterparty, operational-deposit, encumbrance, cap, currency and jurisdictional
rules than the public demonstration contains.

## 7. FX and hedge decisions

Net open position equals foreign-currency assets less liabilities plus any explicit hedge
overlay. Stress P&L applies symmetric TRY appreciation/depreciation shocks. Proposed IRS
and FX-swap/forward notionals target only a portion of exposure and are always labelled
`ALCO_REVIEW_REQUIRED`.

## 8. Reproducibility

The seed is `20260819`. Every generated input, output, chart and SQLite table can be
regenerated with `make demo`. `MANIFEST.sha256` records output hashes. Tests cover data
contracts, Basel shock mechanics, accounting reconciliation, limits, API behaviour and the
end-to-end pipeline, including ordering, HQLA attribution and runoff-timing invariants for
the rapid-digital-run scenario.
