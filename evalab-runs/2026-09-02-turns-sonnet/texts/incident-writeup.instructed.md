Incident Report: Payment API Outage

**Summary**
The payment API was unavailable for 2 hours and 4 minutes on 2026-09-03, from 06:12 UTC to 08:16 UTC. All payment requests failed with TLS handshake errors, and an estimated 4,200 payment attempts were lost, costing roughly $38,000 in revenue.

**Cause**
The TLS certificate for api.payments.example.com expired at 06:12 UTC. The certificate had been issued for 90 days with no automated renewal configured; the team responsible for renewal did not receive an expiry alert because the monitoring check covered only the primary domain, not this subdomain.

**Detection**
Monitoring caught the outage 6 minutes after expiry, via failed health checks from three regions. PagerDuty paged the on-call engineer at 06:18 UTC.

**Timeline**
06:12 UTC — Certificate expires; all payment requests fail with TLS handshake errors.
06:18 UTC — Health checks fail across three regions; PagerDuty pages the on-call engineer.
06:41 UTC — On-call engineer issues a new certificate through the existing ACME client.
07:55 UTC — New certificate deploys to the load balancers after a manual restart clears a stuck pipeline job; service restores.

**Resolution**
The delay between issuance and deployment came from a stuck deployment pipeline job that required a manual restart.

**Impact**
An estimated 4,200 payment attempts failed during the outage. Revenue loss is estimated at $38,000.

**What stops this from recurring**
Automated renewal removes the single point of failure that caused this outage: a certificate with no renewal job behind it. The renewal will run 30 days before expiry and retry daily until it succeeds, so a one-time failure cannot reach expiry unnoticed.

The monitoring gap is closed by checking every subdomain under api.payments.example.com individually, not just the parent domain. This catches the next certificate on any subdomain, not only this one.

The deployment delay is addressed separately: a pipeline health check pages on-call if a job stalls for more than 10 minutes, so a stuck job is caught within minutes instead of surfacing only when someone checks manually.

**Follow-up actions**
1. Add automated certificate renewal 30 days before expiry for all payment subdomains.
2. Extend the monitoring check to cover every subdomain under api.payments.example.com.
3. Add a deployment pipeline health check that pages on-call if a job stalls for more than 10 minutes.
