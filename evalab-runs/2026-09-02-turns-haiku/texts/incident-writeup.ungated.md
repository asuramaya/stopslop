# Incident Report: Payment API Outage

**Incident:** Payment API Service Unavailability
**Duration:** 2 hours
**Date:** September 3, 2026
**Severity:** Critical

## Summary
Payment processing was completely unavailable for 2 hours, blocking approximately 47,000 transactions and affecting merchants and customers during peak transaction hours. The root cause was an expired TLS certificate on the load balancer.

## Timeline

| Time (UTC) | Event |
|---|---|
| **14:23** | Monitoring alerts triggered on API endpoints returning certificate validation errors. |
| **14:31** | On-call engineer confirmed TLS certificate expiration (issued Sept 3, 2024; expired Sept 3, 2026). |
| **14:45** | Certificate renewal initiated; propagation began across load balancers. |
| **16:23** | All endpoints restored to normal operation; traffic normalized. |

## Root Cause
The TLS certificate expired due to lapsed renewal automation. The certificate renewal process failed silently in the CI/CD pipeline, and manual renewal oversight was not in place.

## Impact
- Approximately 47,000 transactions failed or were rejected.
- 12 merchants reported service disruptions to support.
- Estimated customer-facing revenue impact: $38,000.

## Prevention
To prevent recurrence, we will implement defense-in-depth controls:

1. **Automated alerts:** Trigger notifications 30 days before any certificate expiration across all domains.
2. **CI/CD pipeline hardening:** Add explicit logging and failure escalation for certificate renewal jobs; fail deployments if renewal verification is incomplete.
3. **Manual verification:** Add certificate expiration checks to the on-call runbook as a weekly verification task.
4. **Inventory audit:** Complete audit of certificate management processes across all payment-critical services and implement centralized tracking.

These changes will ensure certificate lifecycle issues surface early and remain visible until resolved.
