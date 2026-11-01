# Changelog

## Unreleased

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
