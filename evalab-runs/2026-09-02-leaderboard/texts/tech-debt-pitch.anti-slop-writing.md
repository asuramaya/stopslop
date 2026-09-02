To: Dana, Ravi
From: Hector
Re: giving Q4 to the debt

I'm asking for the whole quarter. Platform team, four people, October through December, with no feature commitments on the board.

The number that convinced me was 41. That's how many of our 118 Sev-2s since March came out of billing-service, and 29 of them touched the same retry path we wrote in 2021, back when we had one payment provider instead of four. Each fix makes the next one worse. Ravi's people already refuse to change that file without a second reviewer. Who's going to want to own it in a year?

Deploys take 52 minutes. Were 11 in 2023. New hires wait roughly three weeks before shipping anything, mostly because nobody ever repaired the local environment after we split the monolith.

The plan isn't fancy. Rip out the retry layer, swap in the provider adapter Sam prototyped back in June, cut the 40 minutes of Selenium down to something honest, and delete the two dead services still sitting in the deploy graph.

I know the cost. Q4 is when sales wants the reporting work, and shoving that into Q1 will irritate people I genuinely like. Granted. But we're already paying for this quarter, in on-call hours and in the four days Marta lost last month to a bug a typed interface catches at compile time.

If a full quarter is more than you can give, I'd take six focused weeks over a year of Fridays. Work like this done at half attention just doesn't stick.
