Vision

By the end of 2028, a new engineer on a product team ships a service to production in their first week. They read one page, run one command, and get a running service with logging and secrets already wired in. They file no ticket, and they ask nobody which of our four deploy scripts is the current one.

We are a long way from that. A product engineer who needs a new service today copies configuration out of a neighboring repo, guesses at the parts that do not apply, and finds the mistakes during an incident three weeks later. Four teams keep four different answers to the same question about database migrations. We swapped the auth library in March and six engineers spent two weeks making the same edit in six repos. None of that work taught us anything we did not already know. Over the next two years, the platform team builds one paved road and moves teams onto it.

We own the service template, the deploy pipeline, and the migration tooling, and we own the pager for all three.

Product teams stop maintaining private copies of our infrastructure and get that time back for their own roadmaps, which is where the argument for this investment starts and ends. We are asking the company to trade throughput now for throughput later. For the first three quarters, product teams will see slower support from us on their bespoke setups while we build the replacement. We will publish a migration schedule per team and hold ourselves to it.

We will know this worked when a team can answer "how long to stand up a new service" in hours, and when the platform team stops appearing in the credits of other teams' incident reviews.
