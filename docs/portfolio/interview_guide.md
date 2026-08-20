# Interview guide

## 60-second explanation

I built an auditable ALM decision-support platform for a fictional Turkish deposit bank.
The project combines official TCMB market anchors and BDDK sector benchmarks with a
fully reconciled synthetic bank balance sheet. It measures repricing mismatch, Basel's six
IRRBB EVE shocks, one-year NII sensitivity, liquidity and stable-funding proxies, FX open
position and partial hedge alternatives. The important result is not that every metric is
green: the model identifies a structural FX limit breach and a combined liquidity stress
weakness, then carries both into an ALCO action queue.

## Questions to expect

**Why use synthetic bank data?**  Internal maturity ladders and deposit behaviour are not
public. I separated official external observations from transparent synthetic internal data
instead of presenting invented records as real.

**Why do EVE and NII tell different stories?**  EVE captures the present-value impact over
the cash-flow life; NII captures a one-year earnings horizon and depends on repricing speed
and pass-through.

**Why call LCR and NSFR proxies?**  The public model lacks the full regulatory counterparty,
encumbrance and jurisdictional detail needed for an official return.

**What would you productionise first?**  Source-system reconciliation, market-data controls,
behavioural model calibration, independent validation, granular limits and approved hedge
workflow integration.

