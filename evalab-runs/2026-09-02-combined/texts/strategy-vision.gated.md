## Vision

Two years from now, an engineer joining this company should be able to put a new service into production during their first week, without reading a wiki page that was last edited in 2023.

That is the whole idea. Everything else in this document is bookkeeping toward it.

Today, each team builds its own road to production. We run three secret stores. We have deploy scripts that were copied between repos and then diverged. We keep runbooks that describe a system we replaced last spring. None of this shows up cleanly in a quarterly number, which is exactly why it has survived. It shows up instead as the six weeks between "the code works" and "the code is serving traffic."

The plan is to move that cost into one place and pay it once. A platform team owns the paved road: build, deploy, configuration, secrets, observability, and the default answers for storage and queues. Product teams own their code and their SLOs. A team that needs to leave the road can leave it, and inherits the maintenance that comes with the detour. That is a trade we offer on purpose, not a rule we police.

Success here looks unglamorous. Deploy lead time drops and stays down. Configuration drift stops causing incidents. The number of Slack threads that begin "how do I" falls by half.

We are not shipping a product. We are pouring the floor our products stand on, and floors get judged by whether anyone has to think about them.

Two things to check against your actual situation: the specifics in paragraph three (three secret stores, the six-week gap, the 2023 wiki) are placeholders — swapping in your real numbers is what makes this section land instead of read as generic. And the "leaving the road is allowed" stance is a real policy commitment; if leadership actually intends the paved road to be mandatory, that paragraph needs rewriting rather than softening.
