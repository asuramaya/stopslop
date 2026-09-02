Breaking up a nine-year-old monolith: three services we extracted, one we put back

Our billing system started as a single Rails application in 2016 and grew to roughly 400,000 lines before anyone could no longer hold it in their head. In 2024 we began pulling it apart. Eighteen months later we run seven services instead of one, and I can tell you which of those extractions paid for themselves and which cost us a quarter of engineering time for no measurable return.

The talk follows four extractions in order. Payments came out first and was the easy case: a clean data boundary, an obvious owner, an existing queue. Notifications went smoothly for the same reasons. The pricing engine was harder, because two teams disagreed about who owned the rules table, and we spent longer negotiating the schema than writing the service. The fourth extraction, user preferences, we reverted after six months; I will show the latency traces that convinced us.

Along the way we changed how we handle distributed transactions twice, replaced our first attempt at a shared client library, and learned that our deployment pipeline was the real constraint rather than the code.

You will leave with a checklist for deciding whether a given piece of a monolith is worth extracting yet, and the specific failure modes we hit at each step.
