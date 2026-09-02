## Vision

Two years out, an engineer at this company should be able to take a new service from first commit to production in under a week, without learning how deploys, secrets rotation, or on-call routing work. That is the whole ambition. It is a narrow one on purpose.

We are not proposing this because platform teams are in fashion. We are proposing it because we already pay for the platform's absence, just in a form that never shows up on a roadmap. Every team has written its own deploy script. Every team has discovered the same three failure modes in the same order. The median new service takes [N] days to reach production today, and most of that time goes to work that is identical across teams and gets solved slightly differently, slightly wrong, each time.

The end state we want is boring: one paved road that most services take, and a documented, supported way off it for the ones that genuinely need something else. Golden paths, not walls. If a team goes around the platform, that is a bug report about the platform, not a compliance problem.

We are explicitly not aiming to own every deployment, standardize every language choice, or become a gate that product work must pass through. A platform team whose main output is approval has failed.

We will judge this by two numbers, not by adoption counts: time from commit to production for a new service, and hours per quarter each product team spends on infrastructure it did not want to think about. If both fall, the investment worked. If neither does, we should stop.
