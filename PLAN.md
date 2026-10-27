# Implementation plan

## Phase 1 — foundation (this package)
- Android API-28+ Compose app shell for server URL and health checks.
- Room outbox/cache data contracts and Retrofit API contracts.
- New typed FastAPI service, PostgreSQL-only configuration, password hashing, short-lived JWTs, role checks, and version-aware/idempotent sync demonstration.

## Phase 2 — central data and authentication
- Audit every existing SQLite table and every SQL call in the desktop source.
- Map existing tables to a versioned PostgreSQL schema; implement an offline-tested one-time migration with row counts, checksums, rollback and a read-only source backup.
- Replace desktop `/api/query` raw-SQL transport with typed endpoints; never accept arbitrary SQL from clients.
- Add staff provisioning, password reset, token rotation/revocation, audit log, device registration and rate limiting.

## Phase 3 — full Android modules
Implement and test role-gated modules in this order: sign-in/server selection; patient search/registration; OPD and encounters; vitals/nursing; lab orders/results; prescriptions/pharmacy; admissions/transfers/discharge; billing/payments/receipts; reports/admin. Each endpoint must enforce permission on the server.

## Phase 4 — safe offline synchronization
- Explicit allow-list of offline actions per role and risk category.
- Room encrypted-at-rest strategy and Android Keystore-backed key management; no sensitive data in logs/notifications.
- Per-mutation UUID, idempotency table, base version, actor/device/time metadata.
- Server conflicts return HTTP 409 or typed conflict response; user reviews and resolves. Never last-write-wins for clinical, dispensing, payment or discharge records.
- Queue expiry, logout cleanup, device lost/revocation and sync observability.

## Phase 5 — release
- HTTPS certificates, firewall/VPN rules, hardened PostgreSQL accounts, automated encrypted backups and restore drills.
- Automated unit/integration tests, concurrent-write tests, offline/online/retry tests, security review, usability testing on Android 9 and current Android, signed APK and staged rollout.

## Acceptance criteria
- A workstation and Android device can discover and verify the same mother server.
- Authentication and every operation are role-checked server-side.
- Android 9+ builds and tests on physical phone and tablet.
- Retry never duplicates a mutation; concurrent edits are detected and surfaced.
- Internet loss does not affect LAN operation; mother-server loss limits the app to explicitly cached/read-only data plus approved queued actions.
- Full backup restoration and data migration are proven before live patient data is used.
