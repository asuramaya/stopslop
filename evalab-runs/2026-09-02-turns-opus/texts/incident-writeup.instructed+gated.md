# Payment API outage, 2026-09-01

## Summary
Every payment authorization failed for 2 hours 7 minutes, from 03:14 to 05:21 UTC. Roughly 41,000 merchant requests to `api.payments.internal` were rejected at the transport layer and never reached the application. The cause was the TLS certificate on the edge load balancer, which expired at 03:14:00 UTC.

## Timeline
1. 03:14 UTC — the certificate expires. Health checks keep passing, because they run over plaintext on the internal port.
2. 03:49 UTC — on-call is paged, 35 minutes after the first merchant support ticket at 03:22.
3. 04:35 UTC — cause identified as an expired certificate.
4. 05:21 UTC — renewed certificate deployed to all four edge nodes; traffic recovers.

## Cause
The certificate was issued manually in 2025 and was never enrolled in the automated renewal system that covers the other 60 services. The expiry monitor reads from that system's inventory, so this certificate was never in scope for a warning.

## What will stop it recurring
The certificate is now enrolled in automated renewal, which removes this specific certificate as a source of expiry. That alone would leave the class of failure open, so the expiry monitor is being repointed at the load balancer's live certificate list rather than the renewal inventory. Any certificate served in production then gets a 30-day and a 7-day warning, whether or not anyone remembered to enroll it. The inventory-based check is retired once the new source has run clean for two weeks.

Edge health checks move to TLS, so a handshake failure fails the check instead of passing it. This is what would have caught the outage at 03:14 rather than 03:22.

The 35-minute delay before paging is tracked separately. The error-rate alert averages over 30 minutes, which is reasonable for partial degradation and wrong for total failure; a second rule pages at 2 minutes when the success rate for a service reaches zero.
