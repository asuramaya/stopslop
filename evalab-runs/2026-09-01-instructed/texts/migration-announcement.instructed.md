# Northwind is moving to Atlas on 14 January

Starting in Q1, Northwind runs on Atlas, our new hosting platform. The cutover happens on 14 January between 02:00 and 06:00 UTC. During that window the service is read-only: you can view and export your data, but saves and API writes will fail with a 503.

Why we're doing this. The current platform runs on hardware we can no longer get parts for, and its scheduled maintenance windows have cost you about four hours of downtime per quarter for the past three quarters. Atlas removes the shared-tenant bottleneck that caused most of those.

What changes for you:

1. API hostname. `api.northwind.example.com` becomes `api.atlas.northwind.example.com`. The old hostname redirects until 30 June, then stops resolving. Update your clients before then.
2. IP allowlists. If you filter our egress traffic by IP, add the Atlas ranges published at `status.northwind.example.com/atlas-ips`. The old ranges stop sending traffic on 14 January.
3. Webhook signatures. Same HMAC scheme, new signing key. Both keys validate through 28 February so you can rotate without a hard cutover.

What does not change: your credentials, your data, your billing plan, and the API request and response formats.

If you have a custom integration or a contract with an uptime clause, contact your account manager before 20 December so we can schedule you into an earlier or later window.

We will post progress during the cutover at `status.northwind.example.com`, and send a confirmation email once writes are enabled again.
