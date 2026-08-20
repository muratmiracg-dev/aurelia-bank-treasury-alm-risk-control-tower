CREATE OR REPLACE VIEW aurelia_alm.v_balance_sheet AS
SELECT
    side,
    currency,
    product,
    SUM(balance_try_mn) AS balance_try_mn
FROM aurelia_alm.position
GROUP BY side, currency, product;

CREATE OR REPLACE VIEW aurelia_alm.v_worst_eve_loss AS
SELECT scenario, delta_eve_try_mn, delta_eve_tier1_pct
FROM aurelia_alm.eve_result
WHERE currency = 'TOTAL'
ORDER BY delta_eve_try_mn ASC
LIMIT 1;

CREATE OR REPLACE VIEW aurelia_alm.v_liquidity_stress AS
SELECT
    scenario,
    lcr_proxy_pct,
    nsfr_proxy_pct,
    survival_horizon_days,
    CASE
        WHEN lcr_proxy_pct >= 120 THEN 'GREEN'
        WHEN lcr_proxy_pct >= 100 THEN 'AMBER'
        ELSE 'RED'
    END AS lcr_signal
FROM aurelia_alm.liquidity_result;

CREATE OR REPLACE VIEW aurelia_alm.v_limit_breaches AS
SELECT control_id, control, observed, limit_value, severity
FROM aurelia_alm.risk_control
WHERE status = 'BREACH';

