# Power BI implementation specification

This folder is a source-controlled report starter, not a pre-rendered claim. Import the
committed CSV extracts from `data/demo/` and `artifacts/results/`, apply
`Aurelia_ALM_Theme.json`, and paste the measures from `ALM_Measures.dax`.

## Recommended semantic model

- `positions[position_id]` 1-* `cashflows[position_id]`
- Disconnected scenario tables: `eve`, `nii`, `liquidity`, `liquidity_ladder`
- Control tables: `data_quality_controls`, `risk_limit_controls`
- Decision tables: `hedges`, `fx`, `dv01`, `repricing_gap`
- Currency dimension with TRY, USD and EUR
- Scenario dimension with display order and risk-view classification

## Seven report pages

1. **ALCO Executive Overview** - assets, deposits, Tier 1, worst EVE/NII, LCR/NSFR,
   breaches, and three management actions.
2. **Balance Sheet & Repricing** - asset/liability mix, repricing ladder, cumulative gap,
   rate-type and currency decomposition.
3. **IRRBB Economic Value** - six prescribed EVE scenarios, currency contributions,
   DV01 and risk-appetite comparison.
4. **NII Sensitivity** - parallel up/down earnings impact, product contribution and
   deposit-beta sensitivity.
5. **Liquidity & Funding** - base/idiosyncratic/market/combined/rapid-digital-run LCR
   proxy, survival ladder, base-to-stressed HQLA bridge, net outflows and NSFR proxy.
6. **FX & Hedge Simulation** - open positions, FX stress P&L, proposed hedge notionals
   and pre/post exposure.
7. **Controls & Governance** - data-quality evidence, limit status, methodology links,
   ownership and escalation state.

## Visual rules

- Red is reserved for a breach or negative management outcome.
- Every scenario visual must show units and the as-of date.
- Proxies must retain the word `proxy`; they are not regulatory returns.
- A hedge recommendation must always show `ALCO_REVIEW_REQUIRED`.
- The rapid-digital-run scenario must be labelled `exploratory management stress`, not a
  regulatory calibration or point forecast.

Power BI Project documentation: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
