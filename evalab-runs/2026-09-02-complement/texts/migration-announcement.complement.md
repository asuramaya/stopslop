**Subject: Northwind Analytics moves to Halyard on 1 October**

Starting 1 October, Northwind Analytics runs on Halyard, our new hosting platform. Here is what that means for you.

Your account, dashboards, saved queries, and API keys carry over. You do not need to rebuild anything or re-enter billing details. Sign in at the same address; we redirect you to Halyard automatically.

Two things do change. API endpoints move from `api.northwind.io/v2` to `api.halyard.northwind.io/v2`. The old endpoint keeps working until 31 March 2027, so you have six months to update your integrations at your own pace. Second, scheduled report delivery shifts from 04:00 UTC to 02:00 UTC, which affects anyone whose downstream jobs assume the later time.

We are making the move for reasons you will feel directly. Halyard cuts query latency on datasets above 50 million rows by roughly half, and it lifts the concurrent export cap from 5 jobs to 25. It also gives us row-level access controls, which several of you have asked for since last year.

The cutover happens on 1 October between 02:00 and 06:00 UTC. During that window, the dashboard is read-only and writes to the API return a 503. Exports queued before the window run after it completes.

If you have a custom integration, a high-volume pipeline, or a compliance review that the endpoint change touches, write to migrations@northwind.io and we will schedule a call before September ends. We would rather hear from you early than sort out a surprise on cutover morning.

— The Northwind team
