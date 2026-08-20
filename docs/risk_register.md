# Model and implementation risk register

| ID | Risk | Current control | Residual status |
|---|---|---|---|
| R1 | Synthetic balance sheet differs from a real bank | Explicit classification and reconciliation | Medium |
| R2 | Zero curves are not executable market quotes | Visible calibration label and replaceable config | Medium |
| R3 | NMD behaviour is misspecified | Six-point runoff, beta sensitivity and model boundary | High |
| R4 | LCR/NSFR proxies are mistaken for regulatory returns | Proxy naming in code, files, dashboard and report | Medium |
| R5 | Hedge sizing is treated as a trade instruction | Partial targets and mandatory ALCO review status | Medium |
| R6 | FX translation becomes stale | As-of date, source URL and optional live connector | Low |
| R7 | Reproducibility drifts | Fixed seed, tests, CI and SHA-256 manifest | Low |
| R8 | A limit breach is hidden by aggregation | Currency views and explicit breach table | Low |

