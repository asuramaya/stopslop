# Incident report: payment API outage, 2026-08-28

## Summary
Roughly 41,000 payment requests were rejected over 2 hours 4 minutes, from 03:12 to 05:16 UTC. Authorizations, captures, and refunds all failed. The API returned TLS handshake errors to every client that verified the certificate chain, because the leaf certificate for api-payments.internal expired at 03:12:00 UTC.

## Timeline (UTC)
| Time | Event |
| --- | --- |
| 03:12 | Certificate expires. Handshakes start failing for every verifying client. |
| 03:38 | A merchant support ticket arrives. First human signal, 26 minutes after the failure. |
| 04:20 | On-call identifies the expired leaf certificate as the cause. |
| 05:11 | Replacement certificate installed; traffic recovers by 05:16. |

## What happened
The certificate was issued in August 2025 with a 12-month lifetime and renewed by hand. When the service moved from the shared ingress to its own load balancer in February, the renewal ticket stayed attached to the old ingress hostname, so nothing tracked the new listener. Expiry monitoring covered certificates presented by the shared ingress only.

Paging was delayed. The synthetic check that would have caught this ran against an internal endpoint that skips verification, so it stayed green.

## What stops it recurring
Two failures had to line up: a certificate nobody owned, and a check that could not see the failure it was written for.

Automatic renewal removes the first. Under ACME the certificate is reissued at 30 days remaining without a human in the path, so a stale ticket or a departed owner no longer matters. A migration that moves a listener carries its renewal with it.

The second needs the check to fail for the right reason. Verifying the chain from outside the trust boundary means the synthetic sees what a merchant sees, and a 21-day expiry threshold pages us three weeks before any customer notices. The listener audit closes the gap between these two: any certificate ACME does not manage gets a named owner or gets retired.

## Actions
1. Move api-payments.internal to ACME with automatic renewal at 30 days remaining. Owner: platform. Due 2026-09-12.
2. Change the synthetic check to verify the chain and fail on expiry inside 21 days. Owner: platform. Due 2026-09-08.
3. Audit all listeners for certificates with no renewal owner. Owner: SRE. Due 2026-09-19.
