Payment API Outage

Date: 2026-09-03
Duration: 2 hours (09:14–11:16 UTC)
Severity: Critical

All payment traffic failed for two hours. Checkout and refund requests dropped to zero from 09:14 to 11:16 UTC, and support logged 340 customer complaints. The cause was an expired TLS certificate on the payment API's load balancer. The renewal job depended on a credential that had rotated three weeks earlier and failed silently after that rotation. No alert flagged the failed renewal, so the team learned of the problem only from customer reports.

Timeline
- 09:14 UTC — certificate expires, all payment traffic starts failing
- 09:22 UTC — customer support flags failed checkouts
- 09:31 UTC — on-call confirms the expired certificate
- 11:16 UTC — new certificate live, traffic recovery verified

Prevention

We will add expiry monitoring that alerts 14 days before any certificate expires. We will fix the renewal job's credential handling so a rotation cannot break it silently: the job will read the current credential at run time instead of a cached one set at deploy. We will add a synthetic check that calls the payment API over TLS every five minutes and pages on failure.
