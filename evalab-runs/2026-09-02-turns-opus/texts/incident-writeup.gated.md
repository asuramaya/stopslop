## Incident Report — Payments API Outage

Date: 2 September 2026
Duration: 09:14–11:22 UTC (2h 08m)

For two hours and eight minutes, no customer could take a payment.

Every call to `/v1/charges` and `/v1/refunds` failed at the TLS handshake, so the outage was total rather than degraded, and roughly 41,000 transactions were rejected outright. No data was lost and nothing was accessed without authorization. The cause was an expired certificate on `api.payments.internal`.

### Timeline (UTC)

| Time | Event |
|---|---|
| 09:14 | Certificate for `api.payments.internal` expires. All TLS handshakes start failing. |
| 09:21 | Error-rate alarm pages on-call. Triage begins against the gateway's generic 502s. |
| 10:40 | On-call reads the raw handshake error and identifies the expired certificate. |
| 11:18 | Manually issued certificate rolled out. Traffic fully recovered by 11:22. |

### What happened

Renewal had been automated in 2024 through cert-manager. But this host was migrated to the new cluster in July and its Certificate resource was never recreated, so nothing was watching the old host at all.

The 30-day expiry alert did fire on schedule. It routed to a Slack channel we archived in June, where nobody read it.

Then the first 79 minutes went to the wrong layer. The gateway masked the handshake failure as a 502, so the on-call engineer chased upstream health before looking at the transport.

### What stops it recurring

Renewal stopped, the warning went nowhere, and the symptom pointed away from the cause. All three had to fail together, and any one of them working would have kept the outage short or prevented it outright, so each gets its own fix.

Renewal coverage. Platform will reconcile every TLS endpoint in the new cluster against its cert-manager Certificate resource and fail CI on any host without one. The July migration checklist gains a certificates step. Platform owns this, due 12 Sept.

Warnings that reach a person. Expiry alerts move from Slack to PagerDuty at 45 and 14 days. A quarterly test fires a synthetic expiry to confirm the page still lands on somebody's phone. SRE owns this, due 19 Sept.

Faster diagnosis. A synthetic probe will check the handshake itself and report certificate expiry as its own alarm, and the gateway will stop collapsing TLS errors into 502. The gateway team owns this, due 26 Sept. None of these three fixes is watertight alone, and we are not claiming otherwise.

What the combination buys us is that a repeat now needs a silent renewal failure, a dead alert path, and a probe outage at once.
