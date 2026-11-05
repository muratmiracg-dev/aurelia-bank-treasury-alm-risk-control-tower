# Changelog

## Unreleased

- Fixed the IRRBB EVE risk measure. The limit control (RL02) and the executive summary
  netted currency gains against losses on the `TOTAL` row; the Basel standardised framework
  sums currency losses without cross-currency offset. `eve.csv` gains `eve_loss_try_mn` and
  `eve_loss_tier1_pct`; the worst EVE loss moves from 13.74% to 13.89% of Tier 1 (parallel
  up, still within the 15% limit). The netted `delta_eve_*` columns are kept as the
  management view. SQL schema/view, Power BI measures, executive figure and docs updated.
  The committed workbook, executive deck and PDF report are static snapshots built outside
  this pipeline and still quote the netted 13.7%; they are refreshed with the next release.

- Fixed the optional live EVDS connector for TCMB's EVDS3 service. The retired
  `evds2.tcmb.gov.tr/service/evds` endpoint now returns the web application's HTML, and
  EVDS has required the API key in the `key` HTTP header since April 2024. Requests now
  go to `https://evds3.tcmb.gov.tr/igmevdsms-dis/` with path-style parameters, and the key
  is sent only as a header, never in the URL.
- A non-JSON EVDS response now raises a clear `DataQualityError` naming the EVDS3 base URL.
- Added network-free tests for the request contract, key handling and response parsing.

## 1.1.0 - 2026-08-21

- Added a severe exploratory rapid-digital-run liquidity scenario with accelerated
  day-1/day-7 outflows, committed-facility utilisation and reduced inflow realisation.
- Added scenario-specific HQLA market-value shocks and transparent base-to-stressed
  liquidity-buffer attribution.
- Added configuration validation, regression tests, artifact invariants, API output,
  SQL/Power BI fields and ALCO governance documentation for the new scenario.
- Refreshed deterministic analytics, figures, SQLite, workbook, executive deck and PDF report.

## 1.0.0 - 2026-08-20

- Added deterministic synthetic bank balance sheet and official public-data snapshots.
- Added repricing/maturity gaps, six-scenario EVE, NII, DV01, liquidity, NSFR, FX and hedge modules.
- Added data-quality and risk-appetite controls, read-only API, SQLite delivery and SQL reference layer.
- Added Power BI semantic/report specification, ALCO workbook, executive deck and PDF report.
- Added CI, CodeQL, 43 automated tests and a 90% coverage gate.
