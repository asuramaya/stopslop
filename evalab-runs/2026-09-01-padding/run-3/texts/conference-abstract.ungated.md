**Cutting Up the Monolith: Two Years, Nine Services, One Regret**

We had a seven-year-old Rails monolith: 400,000 lines, a 90-minute test suite, and a deploy queue where a one-word change waited three hours to ship. The plan was thirty services in eighteen months. We shipped nine in twenty-six, and I'd make the same trade again — with three exceptions I'll walk through.

This is the honest version. How we picked the first seam (billing, and it was the wrong one). Why the strangler-fig pattern holds up beautifully right until two services need the same transaction, and what we did when we hit that wall on day forty. The month we spent on distributed tracing before anything actually needed it, which turned out to be the best month of the project.

I'll put the numbers on screen: deploy frequency, p99 latency, on-call pages, before and after. Some of them got worse. Pages rose 40% in year one and never came all the way back down.

You'll leave knowing which parts of your monolith to leave alone, how to tell a real service boundary from an org chart, and what to say when someone asks for a service mesh in month two.

*(214 words. The specifics — Rails, the line count, nine services, the 40% — are placeholders; swap in your real ones. The abstract only works because of them, so vague substitutes will flatten it.)*
