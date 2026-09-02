**We Broke Up the Monolith. Twice.**

Everyone has read the migration post with the tidy architecture diagram. This is the other talk.

Over eighteen months we pulled forty-odd services out of a Rails monolith that had been growing since 2014. The first attempt failed. We split along org-chart lines, ended up with six services all writing to the same Postgres tables, and shipped slower than before — a distributed monolith with worse debugging. The second attempt worked, and the difference wasn't tooling.

I'll walk through what changed: using database write ownership instead of team boundaries to draw the seams, keeping the monolith as system of record two years longer than planned, and the routing layer that let us roll a service back in an afternoon when it went wrong. Which it did, four times.

We'll also cover the bill. P99 latency went up. Our on-call surface tripled. Observability spend doubled before it paid for itself.

You'll leave with a checklist for deciding which parts of your monolith should stay a monolith, and a rough sense of whether the pieces you want to extract are worth the year it takes.

Some services are still in there. That's fine.

*(203 words. The specifics — Rails, 2014, forty services, four rollbacks — are placeholders; swap in your real numbers, since they're what makes an abstract get accepted.)*
