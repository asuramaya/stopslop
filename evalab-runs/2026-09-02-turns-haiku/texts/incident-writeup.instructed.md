Payment API outage — 2026-09-03, 14:22–16:18 UTC

The payment API was unreachable for two hours, failing 8,400 transactions across 340 merchant accounts. A TLS certificate expired at 14:15 UTC after the renewal cronjob completed without writing the new certificate to disk. All client requests returned connection errors; no transactions were processed during the window.

Root cause: The certificate renewal process failed silently on 2026-09-02 at 23:00 UTC. The renewal cronjob ran without error but did not write the new certificate to disk. No monitoring rule existed for certificate age or renewal success, so no alert was triggered.

Timeline:

- 2026-09-02 23:00: Certificate renewal cronjob runs but fails to write the new certificate to disk. No alert is triggered.
- 2026-09-03 14:15: Certificate expires; API becomes unreachable.
- 2026-09-03 14:47: Oncall identifies the expired certificate as root cause.
- 2026-09-03 16:18: Manual certificate renewal is deployed and full service restoration is confirmed.

Prevention

The outage stemmed from three gaps: the renewal cronjob lacked error reporting, certificate age had no monitoring, and renewal was never tested post-deployment. Three changes will address these.

First, monitoring will alert when certificates expire within 30 days. A second alert will fire if the renewal cronjob completes without writing a valid certificate to disk. These rules will catch problems days or hours before expiry.

Second, the renewal cronjob will log success and failure outcomes to CloudWatch. The oncall dashboard will surface renewal failures in real time, not after they cause an outage.

Third, a monthly staging test will exercise the full renewal and deployment path. This will catch cronjob failures and deployment issues before they reach production.
