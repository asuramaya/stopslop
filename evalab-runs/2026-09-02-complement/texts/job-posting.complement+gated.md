**Senior Backend Engineer**

Chicago or remote (US time zones)
$185,000–$225,000 + equity

We move money. About 40,000 businesses run payroll, vendor payments, and reconciliation through our platform, and roughly $9B settles across it each year. When our ledger service is wrong, someone's rent check bounces. That constraint shapes most of what we build.

You'd join the payments core team, eight engineers who own the ledger, the settlement engine, and the integrations with three card networks and about a dozen banking partners. Over the next year we're splitting the settlement engine out of the monolith, moving reconciliation from nightly batch to streaming, and rebuilding the retry logic around ACH returns, which currently causes more pages than anything else we run.

Our stack is Go and Postgres, with Kafka between services, deployed on AWS through Terraform. We're pragmatic about tools. Two services are still Python, and they work fine.

What we're looking for:

- Six or more years writing backend systems in production, some of it on services where correctness matters more than throughput
- Real experience with distributed systems failure modes: idempotency, exactly-once delivery problems, partial failures
- Strong SQL and a working understanding of transaction isolation
- Comfort with on-call. We run a shared rotation, roughly one week in eight

Payments experience helps but isn't required. Several of our best engineers came from healthcare and logistics.

We work in two-week cycles, write design docs before large changes, and don't estimate tickets. Engineers talk directly to the compliance and operations teams, and you'll spend time understanding NACHA rules whether you want to or not.

Our interview is a call with the hiring manager, a systems design conversation, a debugging session on real code, and a team conversation. Four hours total, no take-home.
