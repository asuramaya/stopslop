## Vision

Two years out, a new service goes from empty repo to production traffic in an afternoon. That's the target. We clocked the current number in March: eleven working days, averaged over the six services Payments and Fulfillment stood up last quarter, and most of that time went to copying config nobody understands out of a service nobody owns. Nine of those eleven days were spent waiting. Waiting on a CI template, or on someone in SRE with the permissions to click approve.

So the bet is simple. We move about a quarter of engineering capacity onto shared infrastructure through 2027 and we hold it there, including the quarters when the roadmap screams. That last part is the hard bit. Platform work loses every argument against a dated customer commitment, which is why it never gets done, and why the allocation is written down here instead of relitigated every planning cycle.

What we're not doing: building a golden path that forbids leaving it. Teams with genuinely strange requirements get to stay strange. They pay for it in their own maintenance time, out in the open, rather than in six months of shared review meetings.

Is 25% the right number? Probably not. I'd rather be wrong about the size of the bet than keep making no bet at all, which is roughly what the last three years looked like. We revisit in November, and the two numbers that decide it are deployment lead time and on-call page volume per service. Everything else is commentary.
