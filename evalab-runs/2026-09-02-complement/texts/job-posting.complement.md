**Senior Backend Engineer**
Remote (US) or Chicago office · $175,000–$215,000 + equity

We move money for about 40,000 small businesses. Payroll runs, ACH transfers, card issuing. When our systems are down, someone doesn't get paid, so we care a lot about correctness.

The backend team is nine engineers. You'd own services in the payments path: the ledger, the ACH submission pipeline, and the reconciliation jobs that catch what the pipeline gets wrong. Our stack is Python and Go on AWS, Postgres for the ledger, Kafka between services. Recent work includes splitting the monolith's settlement logic into its own service and rebuilding the retry logic for returned ACH entries.

What we're looking for:

- Six or more years writing backend services in production, with real ownership of at least one system handling money or something equally unforgiving
- Strong Postgres skills. You should be comfortable reading a query plan and reasoning about isolation levels
- Experience with distributed systems failure modes: partial writes, duplicate messages, clock skew
- Willingness to be in the on-call rotation (one week in six, and it's usually quiet)

Nice to have: NACHA rules knowledge, experience with double-entry accounting systems, or a background in regulated environments.

The interview is four conversations: a screen with the hiring manager, a debugging session on a real service, a system design discussion, and a chat with two people you'd work alongside. No take-home. We aim to finish within three weeks of the first call.

Benefits are the usual ones: health, dental, vision, 401(k) match at 4%, twenty days off plus holidays, and $2,000 a year for conferences or courses.

We hire people who disagree with us. Bring your questions.
