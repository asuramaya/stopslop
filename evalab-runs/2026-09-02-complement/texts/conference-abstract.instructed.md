Breaking up the monolith without breaking the business

Three years ago our order system was a single Rails application with 400,000 lines of code and a 90-minute test suite. Today it is eleven services. The path between those two states was longer and messier than any architecture diagram suggested, and about a third of the extractions were mistakes we later reversed.

This talk walks through what actually happened. I will cover how we picked the first service to extract (billing, chosen because its data had the fewest foreign keys pointing into it), the strangler-fig pattern we used to route traffic incrementally, and the eight months we spent running duplicate writes to two databases while we built confidence in the new path.

I will also spend real time on the costs. Our p99 latency rose 40ms once network hops replaced function calls. On-call load doubled before it improved. Two teams ended up owning services they never wanted, and we had to redraw team boundaries twice.

You will leave with a decision framework for judging whether a given piece of your system is worth extracting at all, plus concrete tests for when the answer is no. Aimed at engineers and tech leads who have already been told to do this and want to do it with fewer scars.
