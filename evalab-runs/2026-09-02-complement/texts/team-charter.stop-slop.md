Platform Engineering Charter

We build and run the internal platform: CI pipelines, deploy tooling, the service template, observability plumbing, and the clusters underneath. Product teams ship on top of our work. When a product engineer sits waiting on infrastructure, that wait is our bug.

Our scope

We own the paved road from commit to production. Teams that follow it get our pager when the road breaks. We answer for pipeline reliability, deploy latency, and cluster spend. A team that steps off the road carries its own pager, and we still help them debug.

Outside our scope

We do not review product code, staff product on-call, or approve another team's architecture. We publish defaults and make them the cheapest path to take. Any team can route around us. We ask them to tell us why, and we write the reason down.

Working agreements

We take intake through one queue and groom it every Monday. We cap work in progress at two items per engineer. When a product engineer burns more than fifteen minutes on manual setup, we file a ticket, and we fix it the second time it happens. We ship documentation with the tool, in the same pull request.

Targets for the first two quarters

By the end of Q1 we cut median deploy time from 34 minutes to under 10 and move eight services onto the shared template. By the end of Q2 a new hire deploys a service on their first day without opening a ticket with us.

We reread this charter in April and change what the last six months proved wrong.
