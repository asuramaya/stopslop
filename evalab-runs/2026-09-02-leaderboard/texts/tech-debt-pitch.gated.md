**Proposal: One quarter of engineering capacity for debt reduction**

Audience — engineering leadership. Author — [Your name]. Date — 2 September 2026.

I'm asking for one quarter of team capacity — roughly 25% of engineering hours, not a full quarter of calendar time — dedicated to paying down technical debt.

The case is arithmetic, not aesthetic. Over the last two quarters our median time from ticket to merge has grown while headcount stayed flat. The reasons show up in the same places every retro: the test suite takes 40 minutes and flakes often enough that people re-run it by reflex, the auth and billing paths share state through a module nobody wants to touch, and three services still pin a framework version that stopped receiving security patches in March.

None of these blocks a release on its own. Together they add a tax to every piece of work we ship, and the tax compounds. Two engineers have told me in 1:1s that they pad estimates specifically to absorb it.

What I'd spend the time on, in order: cut the test suite under 10 minutes and fix the top five flakes; untangle the billing/auth coupling behind a real interface; finish the framework upgrade. Each has a measurable finish line, so this doesn't become an open-ended refactor.

In return I'd expect shorter cycle time, fewer rollbacks, and an upgrade path that stops costing us a sprint every time it comes due.

The cost is real — one quarter of throughput, deferred features, a roadmap conversation with Product. I'd rather have that conversation now than pay the same amount in six months at a worse exchange rate.

Happy to bring the cycle-time data to the next staff meeting.
