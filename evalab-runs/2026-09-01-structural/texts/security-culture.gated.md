Nobody's coming to save your pull request

Last quarter we merged 340 PRs. Security reviewed 22. Three people acting as a gate at the end of a pipeline that eight teams feed — that math is the whole problem. It doesn't scale. It never did. So we're changing where the work lives. Every team names a security contact. This isn't a new job; it's ownership of the boring stuff: read the dependency alerts for your service, know where your secrets actually live, be the person who gets pinged first when something looks wrong. Rotate quarterly if you like.

Threat modeling moves into design review, where fifteen minutes covers three questions. Who can call this thing. What happens when they lie about who they are. What's inside the blast radius if they get in. Put the answers in the design doc, and treat any question you can't answer as a finding in its own right. We're also publishing the checklist the security team has carried around in their heads for two years. It's in the handbook as of Monday, and if you read it once, most of what they'd catch you'll catch first.

One more thing, and it matters more than the rest. If you shipped the bug, reporting it fast is the good outcome. We've never punished anyone for raising a hand, and we're not starting. The expensive failures aren't the mistakes. They're the six weeks between the mistake and someone admitting it.

Security stops being a department this quarter. It becomes a habit, or it becomes an incident.

Questions in #security-guild.
