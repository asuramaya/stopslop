**Cutting the Monolith: What Two Years of Extraction Actually Cost Us**

We started with a Rails app of 400,000 lines and a deploy that took 50 minutes. We ended with 19 services. In between, we made almost every mistake available.

This talk is the honest version. I'll walk through the three extractions that worked — billing, search, notifications — and the two we rolled back, including the one that gave us a distributed transaction bug nobody could reproduce for six weeks. You'll see the seams we cut along, why we chose those seams, and how we were wrong twice about where the real boundaries were.

The uncomfortable conclusion: most of our latency wins came from a database index, not from the architecture. What microservices bought us was team autonomy, and that turned out to be a people problem wearing an infrastructure costume.

If you're being asked to break up a monolith, come find out which parts of the pitch survive contact with production. If you already have, come argue with me. Bring your rollback stories.

Attendees will leave with a decision checklist for extraction order, and a rough cost model for the operational overhead nobody budgets for.

---

The numbers (400k lines, 19 services, 50-minute deploys, six weeks) are placeholders — swap in your real figures, since the specificity is what makes the abstract land.
