# Senior backend engineer

Location: hybrid, three days a week in our Chicago office. Salary: $185,000–$215,000 plus equity.

We process about 400,000 payments a day for small businesses that get paid on invoices. The backend is Go and Python on Postgres, with Kafka between the ledger and everything downstream. Most of it was written in 2019 by four people, two of whom still work here.

You would join the ledger team, six engineers who own double-entry accounting, reconciliation against bank files, and the settlement scheduler. The current problem: reconciliation runs as a nightly batch that takes five hours and fails loudly maybe twice a month, usually because a partner bank changed a file format without telling anyone. We want to move it to a streaming model. That is roughly a year of work and it is the first thing you would be handed.

What we look for: seven or more years writing backend services, and real experience with a system where correctness of money movement mattered. If you have debugged a ledger that drifted by a few cents and had to explain the drift to a compliance officer, we want to talk to you. Go is preferable but we have hired strong Java and C# people who picked it up in a month.

Things you should know before applying: we are on call, one week in six, and the pager does go off at night. We have no formal design doc process, which some engineers find freeing and others find maddening. Code review is slow, averaging about a day and a half.

Apply with a resume and a short note about a system you fixed.
