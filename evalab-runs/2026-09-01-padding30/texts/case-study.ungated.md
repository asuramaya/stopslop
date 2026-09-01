Here's a ~250-word case study. Everything in it is invented — company, people, numbers — so treat it as a template to fill with real data before it goes anywhere near a customer.

---

## Kestrel Freight: from four releases a year to forty a week

Kestrel's dispatch software shipped on a release train that left the station once a quarter. A mis-priced route caught in February waited until May. Customers usually found it first.

The bottleneck wasn't the code. It was the deploy: a 140-step checklist that two engineers worked through on a Saturday, twice a year, with a printout and a phone bridge. "We had one person who knew the order of the database migrations," says Priya Raghavan, who runs platform engineering at Kestrel. "When she took vacation, we didn't release."

Kestrel moved to Arclight in March 2024. Migration took eleven weeks, and the first three went entirely into writing down what the Saturday checklist actually did — steps nobody had documented since 2017.

The pipeline now runs build, test, canary, production in about nineteen minutes. Kestrel deploys a median of 38 times a week. Rollback is a single command and takes 90 seconds, which changed the culture more than the speed did: engineers stopped batching risky changes into one enormous quarterly drop.

Change failure rate fell from 22% of releases to 4%. The on-call rotation grew from three people to nine, because deploying no longer required specialist knowledge.

"The thing I didn't expect," Raghavan says, "is that we argue less. When a release is small, nobody needs a meeting to approve it."

Kestrel is now extending the same pipeline to its warehouse scanning app.
