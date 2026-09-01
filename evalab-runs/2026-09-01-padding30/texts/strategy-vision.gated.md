## Vision

Two years from now, an engineer who wants to stand up a new service should be able to do it in an afternoon, alone, without filing a ticket against anyone.

We are nowhere near that. A new service today takes roughly three weeks of calendar time, pulls in four teams, and ends with a hand-copied deploy config that nobody fully understands. Most of that time is waiting. The work itself — the part that produces something a customer notices — is maybe two days.

So we are betting on paved road. We spend the next two years turning the paths people walk most often into one, and we accept slower feature delivery in the first two quarters to get it.

Paved road means a default. One way to build a service, one way to deploy it, one way to get metrics and logs out of it, and that way is good enough that going around it feels like extra work rather than freedom. Teams keep the right to go off-road. They just stop being forced onto it by our gaps.

What we are explicitly not building is an internal cloud. We are not going to abstract away Kubernetes, write our own orchestrator, or own a UI that competes with the vendor's. Every platform team that has tried that has ended up maintaining a worse version of something free.

By the end of year two we want three numbers to move: time-to-first-deploy under a day, change failure rate under 10%, and the on-call load for platform-owned components flat while service count doubles.

(Numbers are placeholders — swap in our real baselines before this circulates.)
