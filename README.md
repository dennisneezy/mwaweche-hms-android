# Mwaeche HMS Android + Secure Server Foundation (starter)

This is the **first implementation foundation**, not a finished clinical app or production deployment. It is based on the supplied desktop source's existing `users`, `patients`, billing, lab, prescription and nursing concepts. The current desktop source exposes `/api/query` which accepts arbitrary SQL over plain HTTP; **do not expose or reuse that endpoint for Android or real patient data**. This starter deliberately introduces a typed API boundary instead.

## Intended architecture
- Mother computer: Windows service hosting the HMS API; PostgreSQL is the target central database.
- Android: Kotlin + Jetpack Compose, Android 9/API 28+, phone/tablet layouts.
- Offline: Room-based outbox for explicitly supported, low-risk queued actions; every mutation has a UUID idempotency key and base record version. Conflicts are returned for human review; never silently overwrite server data.
- Security: TLS for deployment, short-lived access tokens, hashed passwords, role checks on server, audit trail, least privilege. No credentials or patient details in logs.

## Included now
- Android project skeleton with server address entry and connection check UI.
- Room entities for a local outbox and cached patient summaries.
- Typed Retrofit API contracts for health, login, patient search and sync.
- FastAPI server foundation with authentication, role enforcement, patient read endpoint, idempotent offline mutation handling and version conflict detection.
- Deployment and integration notes.

## Not included / not yet production-ready
- Complete mobile screens for every desktop department.
- Migration of the entire existing SQLite schema to PostgreSQL.
- Production identity provisioning, password-reset, refresh-token rotation, device enrollment, TLS certificate management, backup/restore and full audit review UI.
- Full validation against the desktop program's workflows. Do not connect this starter to the live hospital database until those items are implemented and security-reviewed.

## Build
Open `android/` in Android Studio (current stable version with Android SDK 35 installed). It targets API 35 and supports API 28+. Gradle wrapper is not bundled in this source kit. Allow Android Studio to sync Gradle and install required SDK packages.

For the API: use Python 3.11+, create a virtual environment, install `server/requirements.txt`, configure environment variables described in `server/.env.example`, then run the API behind a TLS reverse proxy. `uvicorn` directly on the LAN is for local development only, not production.

## Offline sync rules
1. Queue only operations explicitly allowed to work offline.
2. Generate a unique `mutation_id` when queued; keep it on retries.
3. Include the `base_version` seen when editing.
4. Server stores processed mutation IDs so retries don't duplicate changes.
5. If `base_version` differs from the current server version, return HTTP 409 and require a user to resolve the conflict.
6. Clinical notes, medication administration, dispensing, payments, discharges and other safety/financially significant actions should remain online-only until each has a reviewed conflict policy. This starter only demonstrates versioned patient demographic updates.

## Build without installing Android Studio
See `BUILD_WITHOUT_ANDROID_STUDIO.md`. The included GitHub Actions workflow builds a debug APK on a hosted runner and makes it available as a downloadable workflow artifact. This builds only the current starter screen, not the complete HMS mobile application.
