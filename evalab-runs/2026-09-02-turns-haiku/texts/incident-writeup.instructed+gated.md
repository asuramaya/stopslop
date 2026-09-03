Payment API outage — September 3, 2026

On September 3, 2026, from 14:22 to 16:18 UTC, the payment API went down, blocking 8,400 transactions across 340 merchant accounts and costing us $395K in lost revenue. An expired TLS certificate on the primary load balancer caused all payment processing requests to fail.

The certificate expired at 14:00 UTC. Our certificate renewal process relies on a cron job that runs weekly, but it failed silently on August 27 when the certificate authority was unreachable. No alert was triggered. The certificate expiration date was not tracked in our monitoring system, so no preventive alert would have fired. We only learned of the problem when customers started experiencing errors.

Timeline

14:00 UTC - Certificate expired on the primary load balancer.

14:22 UTC - Payment API became unavailable as TLS handshakes failed.

14:32 UTC - Connection-failure alerts fired, on-call engineer began investigating.

16:18 UTC - Replacement certificate deployed and all queued transactions processed.

Prevention

We will add certificate expiration tracking to our monitoring system with alerts 30 days before expiry. This gives us a month to renew before the certificate becomes invalid. The certificate renewal cron job will be reconfigured to emit explicit alerts on any failure instead of silently logging errors. Additionally, we are moving to automatic certificate renewal through ACME to remove the dependency on a manual weekly process.
