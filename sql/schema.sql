-- Aurelia Bank Treasury & ALM analytical schema (PostgreSQL 15+ reference)
CREATE SCHEMA IF NOT EXISTS aurelia_alm;

CREATE TABLE IF NOT EXISTS aurelia_alm.position (
    position_id text PRIMARY KEY,
    side text NOT NULL CHECK (side IN ('asset', 'liability', 'equity')),
    product text NOT NULL,
    currency char(3) NOT NULL CHECK (currency IN ('TRY', 'USD', 'EUR')),
    notional_ccy_mn numeric(20, 6) NOT NULL CHECK (notional_ccy_mn > 0),
    fx_to_try numeric(20, 6) NOT NULL CHECK (fx_to_try > 0),
    balance_try_mn numeric(20, 6) NOT NULL CHECK (balance_try_mn > 0),
    rate_type text NOT NULL,
    current_rate_pct numeric(12, 6) NOT NULL CHECK (current_rate_pct >= 0),
    maturity_years numeric(12, 6) NOT NULL CHECK (maturity_years >= 0),
    repricing_years numeric(12, 6) NOT NULL CHECK (repricing_years >= 0),
    hqla_level text NOT NULL,
    asf_factor numeric(8, 6) NOT NULL,
    rsf_factor numeric(8, 6) NOT NULL,
    liquidity_days integer NOT NULL,
    deposit_beta numeric(8, 6) NOT NULL,
    data_classification text NOT NULL,
    CHECK (repricing_years <= maturity_years)
);

CREATE TABLE IF NOT EXISTS aurelia_alm.cashflow (
    position_id text NOT NULL REFERENCES aurelia_alm.position(position_id),
    side text NOT NULL,
    product text NOT NULL,
    currency char(3) NOT NULL,
    time_years numeric(12, 6) NOT NULL,
    cashflow_try_mn numeric(20, 6) NOT NULL,
    cashflow_type text NOT NULL CHECK (cashflow_type IN ('interest', 'principal'))
);

CREATE TABLE IF NOT EXISTS aurelia_alm.eve_result (
    scenario text NOT NULL,
    currency text NOT NULL,
    baseline_eve_try_mn numeric(20, 6) NOT NULL,
    shocked_eve_try_mn numeric(20, 6) NOT NULL,
    delta_eve_try_mn numeric(20, 6) NOT NULL,
    delta_eve_tier1_pct numeric(12, 6) NOT NULL,
    PRIMARY KEY (scenario, currency)
);

CREATE TABLE IF NOT EXISTS aurelia_alm.nii_result (
    scenario text PRIMARY KEY,
    baseline_nii_try_mn numeric(20, 6) NOT NULL,
    shocked_nii_try_mn numeric(20, 6) NOT NULL,
    delta_nii_try_mn numeric(20, 6) NOT NULL,
    delta_nii_pct numeric(12, 6) NOT NULL
);

CREATE TABLE IF NOT EXISTS aurelia_alm.liquidity_result (
    scenario text PRIMARY KEY,
    base_hqla_try_mn numeric(20, 6) NOT NULL,
    hqla_try_mn numeric(20, 6) NOT NULL,
    hqla_market_value_loss_try_mn numeric(20, 6) NOT NULL,
    gross_outflows_30d_try_mn numeric(20, 6) NOT NULL,
    eligible_inflows_30d_try_mn numeric(20, 6) NOT NULL,
    net_outflows_30d_try_mn numeric(20, 6) NOT NULL,
    lcr_proxy_pct numeric(12, 6) NOT NULL,
    survival_horizon_days integer NOT NULL,
    available_stable_funding_try_mn numeric(20, 6) NOT NULL,
    required_stable_funding_try_mn numeric(20, 6) NOT NULL,
    nsfr_proxy_pct numeric(12, 6) NOT NULL
);

CREATE TABLE IF NOT EXISTS aurelia_alm.risk_control (
    control_id text PRIMARY KEY,
    control text NOT NULL,
    status text NOT NULL,
    observed text NOT NULL,
    limit_value text,
    severity text NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_position_currency_product
    ON aurelia_alm.position (currency, product);
CREATE INDEX IF NOT EXISTS ix_cashflow_position_time
    ON aurelia_alm.cashflow (position_id, time_years);
