**To:** Priya, Marcus
**Subject:** Q4 request, six engineers on debt paydown

I'm asking for the platform team's full Q4, six engineers, on technical debt instead of roadmap work.

The numbers make the case better than I can. In Q2 we shipped 11 of the 19 items we committed to. All eight misses touched the billing service, where one deploy runs 40 minutes and fails on the first attempt about a third of the time. Ken and Dana now lose most of a day each week to babysitting those deploys. Our on-call pages doubled between January and June, and Sam traced 60% of them to the retry logic we wrote in 2021 for a traffic pattern we stopped seeing two years ago.

Two pieces of work would clear most of that. First, we split the billing deploy pipeline so each of the four modules ships on its own. Second, we replace the retry layer with the queue-based design Dana prototyped in March and ran against shadow traffic for two weeks without a page.

The price is real. We drop the merchant dashboard refresh and the two smaller integrations from Q4. I'd ship them in Q1, and I expect them to move faster once a deploy costs 5 minutes.

If you'd rather defer, I want to name what I think Q1 looks like: eight more slipped items, and Sam and Dana spending Fridays in the deploy channel.

I'd like your answer by September 15 so I can plan staffing.
