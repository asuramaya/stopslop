**Title: We Broke Up the Monolith. Twice.**

Everyone tells the same story about monoliths. It got slow, teams stepped on each other, and services fixed it. We tried that in 2023. Eighteen months later we had fourteen services, a distributed transaction we didn't understand, and a p99 that had gotten worse.

This talk is the second attempt, and what we learned between them.

I'll walk through the parts nobody puts in the diagram. How we found real seams by tracing which tables were written together, instead of by drawing boxes on a whiteboard. Why our first split — by team org chart — put a network hop in the middle of the checkout path. What the strangler-fig pattern actually costs when the old code keeps shipping features during the migration. And the two services we merged back, deliberately, after admitting they were one thing.

You'll leave with a way to decide whether a given boundary is worth a network call, a rough estimate of the operational tax per service, and permission to stop at four services if four is enough.

Bring a monolith you're annoyed with. Some of them should stay.

---

Swap the dates, service counts, and the checkout example for yours — the concrete numbers are what make an abstract get accepted, so they should be real.
