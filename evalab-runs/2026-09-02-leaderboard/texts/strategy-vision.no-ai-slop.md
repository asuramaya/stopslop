**Vision**

By the end of 2028, an engineer at Northwind can take a new service from empty repo to production traffic in a single day, without filing a ticket.

Today it takes about three weeks, and most of that is waiting. Two days for a namespace. A week for someone on Infra to write the Terraform. Another few days chasing a TLS cert, a dashboard, and a slot in an on-call rotation. Six product teams have each solved this once, in six incompatible ways, so when the person who built one of those setups leaves, we pay for it again.

We plan to build one paved road and make it the cheapest path. A service template that ships with logging, tracing, auth, and a deploy pipeline already wired. Golden defaults for the things nobody wants to think about, and an escape hatch for the teams that genuinely need something else. Self-service where a ticket sits today.

This is not a mandate to migrate everything. Legacy services stay where they are until their owners want to move, and we expect two or three to never move at all. The road has to win on merit, or we have built a tax.

Two years out, we should be able to check three numbers: median time from repo creation to first production request, the share of new services on the template, and the number of Infra tickets per engineer per quarter. If the first and third have not dropped by more than half, the investment did not work, and we should say so plainly and stop.
