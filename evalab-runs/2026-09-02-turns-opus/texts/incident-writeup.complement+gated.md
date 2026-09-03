# Payment API Outage, 2026-09-01

## Summary

Card authorizations, refunds, and webhook deliveries failed for 2 hours 7 minutes, from 03:14 to 05:21 UTC. Roughly 41,000 requests were declined, deferring about $310,000 in volume; no transactions were lost. Every client that verified the certificate chain refused to connect, because the edge certificate for `api-payments.example.com` expired at 03:14 UTC.
