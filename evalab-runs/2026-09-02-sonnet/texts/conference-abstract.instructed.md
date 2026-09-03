Migrating a monolith to microservices usually starts with a deadline and ends with a distributed system nobody fully understands. This talk covers a three-year migration of a payments platform: 40 engineers, one monolith, and the sequence of decisions that determined which services survived contact with production.

The talk opens with the strangler fig pattern applied to a billing module handling 2 million transactions a day, then covers the parts nobody mentions in the pattern diagrams: how to split a shared database when both sides need the same table, how to keep a saga from silently losing state during a partial failure, and how to debug a request that crosses nine services when your only clue is a trace ID.

Three incidents anchor the middle section. A schema migration that locked the orders table for eleven minutes. A retry storm that took down an already-degraded inventory service. A service boundary drawn around org charts instead of data, which cost four months to undo.

The talk closes with the metrics that mattered a year in: deploy frequency up, mean incident duration down, and the one number that got worse — the time it took a new engineer to trace a bug across service boundaries. Attendees leave with a decision framework for when to split a service, and when to leave the monolith alone.
