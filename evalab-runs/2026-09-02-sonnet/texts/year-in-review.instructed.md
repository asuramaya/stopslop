This year we shipped fewer features than last year and broke less in production. That trade-off was deliberate.

The migration off the monolith took eight months, three more than we planned. The delay came from data consistency issues we found in March, not from the split itself — two services were writing to the same table without either one knowing. We caught it before it hit customers, but it cost us a quarter of runway on the roadmap.

Incident count dropped from 34 to 11. Most of that came from one change: every deploy now runs against a staging replica of production traffic for fifteen minutes before it goes live. We built this after the November outage, where a schema change passed every test we had and still took checkout down for 40 minutes.

On-call load is down too. The pager fired 60 times in Q1 and 9 times in Q4, and API latency held under 200ms for the past two quarters even as usage grew.

None of this is finished. The service split left us with two auth paths that need to converge, and our test coverage for the payments module is still below where we want it. Both are on the roadmap for Q1.

Thanks to everyone who sat through the March postmortem and the two follow-ups after it. That process is why the next schema change won't take down checkout.
