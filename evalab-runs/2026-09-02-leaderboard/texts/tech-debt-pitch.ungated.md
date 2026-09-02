**Proposal: Dedicate Q4 engineering capacity to debt reduction**

**To:** Engineering leadership
**From:** [Your name]
**Ask:** One quarter of one team's time (roughly 25% of total engineering capacity for Q4)

We are paying for our deferred maintenance every sprint, and the bill is going up.

Three numbers make the case. Our median PR now sits 4.2 days in review, up from 1.8 a year ago, mostly because reviewers cannot tell what a change touches. On-call pages have doubled, and the top three sources are all in code we flagged as fragile in 2024 and never revisited. New hires take about seven weeks to their first independent deploy; two years ago it was three.

None of that is a mystery. It is the compounding cost of shipping around problems instead of through them.

What I am asking for is one quarter, one team, and a fixed scope: retire the duplicate auth paths, break up the two services that account for most of our incidents, and replace the test harness that everyone works around. Not a rewrite. No new platform. Just the work we have been listing in retros and then not doing.

What we get back is measurable, and I will measure it: review latency, page volume, and time-to-first-deploy, reported monthly against today's baseline. If those numbers have not moved by end of quarter, we stop and you have my write-up on why.

The cost of saying no is not zero. It is another quarter of the same numbers, worse.

Happy to walk through the scope in detail whenever it is useful.
