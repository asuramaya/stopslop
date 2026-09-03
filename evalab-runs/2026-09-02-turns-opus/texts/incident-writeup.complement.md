# Incident Report: Payment API Outage, 2026-08-28

**Duration:** 14:02–16:07 UTC (2h 05m)
**Impact:** All requests to api.payments.internal returned TLS handshake failures. Roughly 41,000 authorization attempts failed. No transactions were double-charged; no data was lost.

## What happened

Every client of api.payments.internal lost the ability to authorize payments for two hours. Client SDKs rejected the connection at the handshake and retried, which added load to the gateway but did not extend the outage.

The cause was an expired TLS certificate. It had been issued manually in August 2025 during a migration off the automated renewal path, and was never returned to that path, so cert-manager did not track it. The expiry monitor only watched certificates cert-manager knew about.

## Timeline

- 14:02 UTC. Certificate expires. Error rate goes to 100%.
- 14:09 UTC. Two merchants report failures. On-call paged.
- 15:20 UTC. New certificate issued, after 49 minutes spent locating the CA account owner.
- 16:07 UTC. Certificate deployed to all six gateway nodes. Traffic recovers.

## What will stop it recurring

Three gaps produced this outage, and each has a fix.

The certificate sat outside automated renewal. Moving api.payments.internal back under cert-manager removes the manual step entirely.

The monitor watched the wrong list. Checking live TLS endpoints against the cert-manager inventory, rather than trusting the inventory alone, catches any future certificate that drops off the automated path.

Nobody knew who held the CA account. Recording the account owner in the service catalogue and adding a backup holder removes the 49-minute lookup from the recovery path.

## Follow-up

1. Move api.payments.internal back under cert-manager. Owner: platform. Due 2026-09-10.
2. Audit every TLS endpoint against the cert-manager inventory; alert on any certificate absent from it. Owner: platform. Due 2026-09-17.
3. Alert at 30 and 7 days before expiry, paging at 7. Owner: SRE. Due 2026-09-10.
4. Record CA account owner and backup in the service catalogue. Owner: SRE. Due 2026-09-10.
