**Title: We Split the Monolith Twice, and Only the Second One Worked**

Our first attempt at microservices gave us eleven services, a distributed transaction we didn't know we'd written, and a deploy pipeline nobody could explain. We rolled most of it back. The second attempt took longer to start and finished in half the time.

This talk is about what changed in between. Not the tooling: we kept the same orchestrator, the same language, mostly the same team. What changed was the order of operations. We stopped drawing boundaries on a whiteboard and started finding them in the data, tracing which tables were actually written together and which were only joined for a report someone ran once a quarter. We extracted the seams that were already there instead of the ones the org chart implied.

I'll walk through three extractions in detail, including one we abandoned mid-flight and why that was the right call. You'll see the strangler-fig routing layer we used, the two months we spent running old and new paths in parallel against production traffic, and the migration we deliberately never finished.

If you're staring at a monolith and a mandate, come get the version with the failures left in.

*(Swap in your own service counts and timeline; the structure holds.)*
