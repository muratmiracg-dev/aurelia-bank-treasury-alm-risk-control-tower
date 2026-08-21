# Rapid digital deposit-run scenario

## Purpose

`rapid_digital_run` is a severe exploratory management stress designed to test how quickly
the fictional Aurelia Bank could exhaust immediately monetisable liquidity when withdrawals
accelerate through digital channels. It supplements the base, idiosyncratic, market-wide and
combined scenarios; it does not replace a regulatory LCR calculation.

## Governed assumptions

| Driver | Assumption | Interpretation |
|---|---:|---|
| Demand-deposit runoff | 45% | High-velocity withdrawal of non-maturity balances |
| Term-deposit runoff | 30% | Early non-renewal and breakage pressure |
| Wholesale runoff | 100% | No rollover of short-term market funding |
| Committed-facility draw | 50% | Customers draw contingent liquidity lines |
| Inflow realisation | 40% | Contractual inflows are only partially available |
| Day-1 share of 30-day outflows | 55% | Digital acceleration front-loads the run |
| Day-7 share of 30-day outflows | 85% | Most monthly pressure arrives inside one week |
| Level 1 HQLA market-value shock | 2% | Additional monetisation stress after base eligibility |
| Level 2A HQLA market-value shock | 10% | Wider market-liquidity discount |
| Level 2B HQLA market-value shock | 25% | Severe discount where such assets exist |

Every parameter is stored in `config/assumptions.yml`. The numbers are internal portfolio
demonstration assumptions, not statutory thresholds, historical estimates or predictions.

## Calculation path

1. Apply the existing configured regulatory-style haircut to each HQLA position.
2. Apply the scenario-specific market-value shock to the remaining eligible amount.
3. Calculate 30-day retail, term, wholesale and committed-facility outflows.
4. Recognise only the configured share of eligible inflows, subject to the existing cap.
5. Compute the LCR proxy from stressed HQLA divided by net 30-day outflows.
6. Apply the scenario timing curve to find the first governed day with negative cumulative
   liquidity.

The HQLA formula is:

`stressed HQLA = balance × (1 - regulatory haircut) × (1 - market-value shock)`

## Verified snapshot

| Output | Result |
|---|---:|
| Base eligible HQLA | TRY 59.40bn |
| Stressed eligible HQLA | TRY 57.94bn |
| HQLA market-value loss | TRY 1.46bn |
| Gross 30-day outflows | TRY 74.20bn |
| LCR proxy | 78.09% |
| Survival horizon | 7 days |

## ALCO interpretation

The result is a vulnerability signal, not a forecast. A seven-day survival horizon calls for
an executable contingency funding playbook: pre-position collateral, confirm central-bank and
secured-funding operational readiness, protect unencumbered HQLA, establish intraday liquidity
monitoring and coordinate customer-communication escalation. Owners, limits and execution
authority remain human governance decisions.

## Model boundaries

- The model uses aggregate product runoff rather than depositor-level concentration or
  behavioural segmentation.
- It does not model intraday payment queues, collateral settlement timing, central-bank
  eligibility, operational deposit classification or currency-specific regulatory LCR rules.
- It does not estimate reputational contagion, social-media propagation or management actions
  endogenously.
- A production implementation requires empirical calibration, independent validation, legal
  review and reconciliation to the bank's regulatory liquidity reporting stack.

