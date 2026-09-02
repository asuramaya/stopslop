We Broke the Monolith. Then We Broke Everything Else.

Three years ago our Rails app was 400,000 lines and one deploy button. Now it's 60 services, and I want to tell you honestly which parts of that were worth it.

This talk is a field report, not a sales pitch. I'll walk through the four extractions we did first — billing, search, notifications, and the one we had to roll back after eleven days — and what each one cost in engineer-months. You'll see the dashboards from the week our p99 latency tripled because a service mesh retry policy turned a single slow query into a thundering herd.

Some things got better. Deploy frequency went from weekly to about 40 times a day, and the payments team stopped waiting on anyone. Local development got worse, on-call got worse, and any bug that crosses three network hops got much worse than either.

I'll cover the decisions I'd repeat (extract along team boundaries, not domain diagrams; keep one database until it actually hurts) and the ones I regret (starting with the hardest service to prove it was possible).

If you're staring at a monolith and a roadmap that says "microservices," come find out what you're signing up for.
