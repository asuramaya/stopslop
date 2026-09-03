Our team spent three days at the conference last week, and the sessions on retrieval pipelines were worth the trip alone.

The infrastructure talks confirmed something we suspected: most teams still run embeddings and reranking as separate, loosely coupled steps, and most of the failures happen at that seam. One speaker from a mid-size search company walked through a postmortem where a reranker silently drifted out of sync with an updated embedding model for six weeks before anyone noticed. The fix was a version-pinning check in CI, not a smarter model. That story landed harder than anything about model architecture.

We also picked up a concrete technique for evaluation: instead of a single aggregate accuracy score, one team scores each query against the specific failure mode it's meant to catch (missing document, wrong ranking, stale index) and tracks those separately. We're going to try this on our own eval set this month.

The panel on agent reliability was less useful. Three companies described their production setups, and each answer to "how do you handle failures" boiled down to retries and logging, which we already do. We left that session with fewer notes than any other.

The hallway conversations mattered more than the scheduled talks. Two engineers from a company we don't compete with walked us through their approach to chunking long documents, and it directly answered a question we've had open for two months.

Next step: we're prototyping the version-pinning check this week, and Priya is writing up the failure-mode eval breakdown for the team wiki.
