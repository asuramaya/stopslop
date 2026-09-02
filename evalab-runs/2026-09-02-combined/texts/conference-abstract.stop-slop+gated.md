**From One Deploy to Forty: What We Learned Breaking Up a Ten-Year-Old Rails Monolith**

We spent eighteen months splitting a 400,000-line Rails application into services. Half of what we did was wrong.

This talk covers the parts nobody puts in the migration blog posts. We picked our first service boundary because billing seemed self-contained, then spent four months discovering that billing read from twelve tables owned by other teams. We built a shared library to hide the network calls and recreated the monolith with worse latency. We ran the strangler pattern for a year and kept both code paths alive far longer than we planned, because deleting the old path required proving something we had no way to prove.

You will see our actual dependency graphs, the three boundary decisions we reversed, and the on-call load before and after. I will show the deploy pipeline we built to run forty services with a nine-person team, including the parts of it we later ripped out.

Attendees leave with a method for finding real service boundaries from database access patterns instead of org charts, and a list of the migrations we would skip if we started again.

For engineers and leads considering a decomposition, or partway through one and wondering whether to keep going.
