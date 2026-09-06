# Security Policy

## Scope

This is a benchmarking tool meant to run locally against a throwaway database. It has no
authentication and is not designed to be exposed to a network. `docker compose` binds both
PostgreSQL and the app to `127.0.0.1` for that reason.

**The tool writes to the database it connects to**: it truncates `users` when reseeding, and creates
and drops `sqlperf_orders` and `sqlperf_idx_users_age`. Never point it at a database holding data you
care about.

## Reporting a vulnerability

Open a [security advisory](../../security/advisories/new) rather than a public issue.

Please include the version or commit, reproduction steps, and the impact you observed.
