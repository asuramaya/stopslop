## Vision

Two years from now, a new service should reach production in a day, and the engineer who ships it should never have opened a Terraform file.

That is the whole bet. Right now the median new service takes eleven days from first commit to serving traffic, and roughly eight of those days are spent on work nobody wants credit for: copying a CI config from whichever neighboring repo looked healthiest, chasing IAM permissions through Slack, discovering that the metrics dashboard everyone assumed was standard was hand-built by someone who left in March. Every team pays this tax separately. We pay it about forty times a year.

We want to stop paying it forty times. The platform team's job over the next eight quarters is to make the correct path the easy one — a paved default for deploys, observability, secrets, and data access that a team adopts by doing less work, not more. Adoption is the test. If a team has to be told to use the platform, we built the wrong thing.

Concretely, by the end of the period: a service template that carries its own pipeline, alerts, and on-call routing; one deploy mechanism instead of the current four; and enough of the fleet migrated that we can retire the 2019 Jenkins cluster and the people who quietly keep it alive can go do something else.

None of this ships a feature. It buys back engineer-days at a rate we think is somewhere near 3:1, and it makes the next reorg survivable.

---

The numbers (eleven days, forty services, the Jenkins cluster, 3:1) are placeholders — swap in your real ones, since the section only works if the reader recognizes the specifics.
