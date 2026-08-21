-- ALCO query 1: currency-level balance-sheet mix
SELECT currency, side, SUM(balance_try_mn) AS balance_try_mn
FROM aurelia_alm.position
GROUP BY currency, side
ORDER BY currency, side;

-- ALCO query 2: largest adverse EVE scenario
SELECT * FROM aurelia_alm.v_worst_eve_loss;

-- ALCO query 3: earnings sensitivity
SELECT scenario, delta_nii_try_mn, delta_nii_pct
FROM aurelia_alm.nii_result
ORDER BY delta_nii_try_mn;

-- ALCO query 4: liquidity escalation queue
SELECT *
FROM aurelia_alm.v_liquidity_stress
ORDER BY lcr_proxy_pct;

-- ALCO query 5: open limit breaches
SELECT * FROM aurelia_alm.v_limit_breaches;

-- ALCO query 6: rapid digital-run escalation metrics
SELECT
    scenario,
    stressed_hqla_try_mn,
    hqla_market_value_loss_try_mn,
    lcr_proxy_pct,
    survival_horizon_days
FROM aurelia_alm.liquidity_result
WHERE scenario = 'rapid_digital_run';
