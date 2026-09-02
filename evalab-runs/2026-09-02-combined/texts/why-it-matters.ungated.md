Draft below (~245 words). It passes the project's own `slopwatch` gate.

---

## Your dashboards are lying to you

Every service I've worked on had a green dashboard the day it fell over.

That's not a knock on dashboards. It's the nature of the thing: a dashboard answers questions you thought of in advance. CPU, memory, request rate, error percentage. Those four graphs will catch the failures you've already seen. They will not catch the one where a single customer's malformed webhook payload sends one pod into a retry loop that quietly exhausts a connection pool shared by six other services, while every graph on the wall stays green, because 0.4% of requests failing rounds to nothing.

Observability is the difference between "is the system up?" and "why is this request slow, right now, for this user?" The first question has a yes/no answer and a monitoring tool. The second is open-ended, and you can only answer it if the system emitted enough context at the time it happened: trace IDs, structured logs with the tenant and the endpoint attached, spans that cross service boundaries.

Most teams find the gap at 3 a.m. Someone is SSH'd into a box, grepping. Someone else scrolls Slack for the last deploy. Forty minutes in, nobody has ruled anything out, and the incident channel has twenty people in it.

The cost of that night isn't the outage. It's the forty minutes.

---

Two things to check against your own experience: the webhook/connection-pool example and the 3 a.m. scene are invented, so swap in a real incident of yours if you have one — the section lands much harder with a war story the reader can't argue with.
