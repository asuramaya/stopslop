248 words, clean through the repo's own `slopwatch` gate.

---

## The three-hour outage nobody could explain

Checkout was failing for about 4% of users. Not all of them. Four percent. The dashboards were green: CPU fine, memory fine, and the error rate at the API gateway had crept from 0.1% to 0.4% without tripping anything, because the alert threshold was set at 1%.

It took three engineers most of an afternoon to find it. A connection pool in the payments service, sized at 20 back in 2019 and never revisited, saturating whenever a nightly batch job overlapped with the European morning rush.

Here is the part worth sitting with. Every piece of information needed to diagnose that in ninety seconds already existed inside the running system. It simply wasn't reachable. The pool exposed a gauge; nothing scraped it. The failing requests carried a trace ID; nothing joined that ID to the payments logs. The system was talking. No one had wired up the ears.

That gap, between what your software knows about itself and what you can actually ask it, is what observability means. Monitoring answers the questions you thought of in advance. Observability is what you have left when the question is new, which during an incident it always is.

Most teams treat this as a purchase. Pick the vendor, ship the agent, tick the box. But instrumenting a system is a design activity, and it belongs next to the code, made by the people who know which failure modes are plausible and which are fantasy.

---

The opening leans on one invented incident as the hook — swap in a real postmortem from your own team if you have one, since the specifics (4%, pool of 20, the 1% threshold) are what make it land, and real numbers land harder than plausible ones.
