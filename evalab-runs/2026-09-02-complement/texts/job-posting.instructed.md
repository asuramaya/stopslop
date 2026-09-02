Senior backend engineer
Boston or remote (US time zones) · $185k–$225k + equity

We process about 40 million card transactions a month for small business customers, and the ledger service that records them is the piece we care most about getting right. That service is Go, Postgres, and Kafka, deployed on EKS. You would own a meaningful share of it.

The work in the first year: splitting the monolithic ledger writer into per-tenant partitions without downtime, replacing our homegrown retry layer with something that survives a regional outage, and cutting p99 settlement latency from 900ms to under 300ms. There is also unglamorous work — reconciliation jobs, PCI audit evidence, a migration off an EOL Kafka version. We are honest that it is part of the job.

What we need you to have done before: five or more years writing production backend services, at least two of them somewhere money moved and correctness was not negotiable. Deep SQL, including the parts of Postgres that bite under load. Comfort being paged, and a track record of writing the postmortem that keeps the page from happening twice.

We are 140 people, 38 in engineering, Series C, profitable since Q2 2024. Engineers deploy their own code. Nobody has an on-call rotation tighter than one week in six.

Process: a 45-minute call with the hiring manager, a two-hour paid work sample using a sanitized version of our schema, then a half day with the team. Three weeks start to offer, and we tell you no quickly if the answer is no.

Apply at careers.example.com/backend, or email eng-hiring@example.com with anything you have built that you are proud of.
