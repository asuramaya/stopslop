Here's the opening (~240 words):

---

Every engineering team already has observability. Most have the bad kind: a dashboard someone built in 2022, four Slack channels of alerts nobody reads, and one senior engineer who happens to know that checkout timeouts usually mean Redis.

That last one is the real problem. When the knowledge of how a system fails lives in a single person's head, your mean time to recovery is that person's calendar availability. The system is legible to them and opaque to everyone else. Then they take a two-week holiday, or leave.

The useful definition of observability is narrow. Can you answer a question about your system's behavior that you did not think to ask in advance? Monitoring handles the questions you wrote down ahead of time. CPU over 80 percent. Error rate above 1 percent. Those work fine until the outage is novel, and every outage worth writing a postmortem about is novel.

The payoff shows up in incidents first, because a team that can follow one slow request across seven services stops guessing. But the bigger return comes between incidents. When an engineer can ask what the p99 looks like for customers on the new pricing plan and get an answer in a minute, the conversation about whether to ship changes shape. You argue from traces instead of instinct.

This is a claim about how teams work, not about vendors. The tooling matters less than whether anyone can interrogate production without filing a ticket.

---

I ran it through this repo's own `slopwatch` ruleset — passes the live gate with no blocking issues.
