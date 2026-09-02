Our billing system took eleven minutes to boot and forty minutes to test. Two engineers understood the deploy script. In March 2023 we started pulling that Rails monolith into services, and nineteen months later we run twenty-three of them.

I will walk you through the extractions in the order we did them, including the two we reversed. The first service we carved out was the one with the cleanest interface, which turned out to be the wrong criterion. It also had the least traffic, so we learned nothing about latency until we moved payments a year later and took the site down for six minutes.

You will see the seam layer we wrote to route calls between old and new code, the database views that let two services read one table while we untangled ownership, and the three months we spent on tracing before we split anything. You will also see our bill: infrastructure cost rose 60 percent, on-call pages doubled for two quarters, and a feature that used to touch one repo now touches four.

Bring a monolith you are considering splitting. I will tell you which parts of ours we would leave alone if we started over, and how we decide now.
