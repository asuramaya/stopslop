Incident Report — Payment API Outage

Date: September 2, 2026  
Duration: 2 hours (14:30–16:30 UTC)  
Service: Payment Processing API  
Status: Resolved

Summary

8,400 payment transactions failed over 2 hours, totaling $340K in failed payment attempts. The Payment API became unavailable due to an expired TLS certificate on the primary load balancer.

Root Cause

The TLS certificate for `payments.api.internal` expired at 14:15 UTC. The certificate renewal process had failed silently three weeks prior due to an invalid email address in the certificate authority account. No alert notified the ops team of the expiration.

Timeline

| Time (UTC) | Event |
|---|---|
| 14:30 | Issue detected — customers report payment failures |
| 15:10 | Root cause identified — TLS certificate expired |
| 15:45 | New certificate provisioned and deployed to load balancer |
| 16:30 | Service restored — payment queue cleared and normal operations resumed |

Impact

- 8,400 transactions failed, totaling $340K in payment attempts
- Customers experienced checkout failures
- Average transaction recovery time was 12 minutes after service restored

Resolution

We reissued the TLS certificate, deployed it to the load balancer, and flushed the failed transaction queue.

Prevention

- Enable certificate expiration alerts 60 and 30 days before expiration via automated scanning of all load balancers and APIs.
- Verify all certificate authority account contact information and test renewal workflows quarterly.
- Implement automated certificate renewal via ACME to eliminate manual intervention and silent failures.

These measures ensure certificate status is visible, renewal does not depend on outdated contacts, and expiration cannot occur undetected.
