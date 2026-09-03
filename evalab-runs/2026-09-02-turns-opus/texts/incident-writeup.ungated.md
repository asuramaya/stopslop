## Incident Report: Payment API Outage

**Impact:** For two hours on 2026-09-02, no merchant could take a payment. Every request to `api.payments` failed the TLS handshake at the edge, which rejected about 41,000 authorization and capture attempts. Two merchant partners fell back to their offline queue; the rest showed customers an error at checkout. No payment data was lost, since the failures happened before any state was written.

**Duration:** 14:03–16:07 UTC (2h 4m) · **Severity:** SEV-1

**Cause:** The leaf certificate for `api.payments` expired at 14:03 UTC. It had been issued by hand in September 2025 during a migration off the old edge terminator, and was never added to the automated renewal inventory. Our expiry monitor reads that inventory, so it had nothing to alert on.

The rest of the report follows as written: detection, resolution, timeline, and the recurrence section.

Two things moved. The date, duration, and severity now sit in a metadata line under the impact statement rather than above it, so the first thing a reader hits is that payments stopped. And the "no payment data was lost" line came forward from Resolution into Impact, because it answers the question an executive reader asks in the first five seconds.
