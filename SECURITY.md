# Security policy

Report suspected vulnerabilities privately through GitHub's security advisory function.
Do not open a public issue containing secrets or exploit details.

The committed demo contains no credentials, customer records or confidential bank data.
Live EVDS access requires a user-supplied key through `EVDS_API_KEY`; it must never be
committed. The API is read-only and supports an optional `AURELIA_API_KEY` for non-local use.

