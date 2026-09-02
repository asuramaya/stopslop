Subject: let's stop asking who broke it

We had three incidents last quarter. In all three, the review meeting spent more time establishing who typed the command than describing why the command looked safe at the time. That ordering is backwards, and it costs us.

Here is the practical problem. When the outcome of a review is a name, people learn to route around reviews. Details get softened. The engineer closest to the failure, the one who knows exactly which dashboard lied to them, comes in defensive and leaves having said the minimum. We end up with a document that assigns responsibility and explains nothing.

A blameless postmortem changes one rule: we write about the system, not the person. Instead of "Marcus deployed without checking the migration," we write "the deploy path allowed a schema change to ship with no migration check, and the runbook did not mention one." Same facts. The second version has a fix attached to it.

This is not about protecting anyone from consequences. Repeated negligence is a management conversation and stays one. It is about separating that conversation from the technical one, so the technical one can actually happen.

What I want to try, starting with the next incident: a written timeline within 48 hours, a review where the person who was on call walks us through what they believed and when, and action items that are changes to systems rather than promises to be more careful. No attendee list beyond the people who can act on it.

I'll facilitate the first one. If it produces a worse document than what we do now, we drop it.
