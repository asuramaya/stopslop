When Something Breaks, We Fix the Process, Not the Person

Last month's outage lasted forty minutes. In the retro, three people admitted they'd noticed the same warning sign days earlier and said nothing, because raising it felt like accusing someone of a mistake before it had even happened. That's the cost of how we currently handle incidents: people protect themselves instead of the system.

I want to propose blameless postmortems as our default process for every incident above a certain severity.

The idea: when something fails, the postmortem asks what conditions let the failure happen, not who caused it. Did the deploy checklist skip a step? Was the alert threshold wrong? Did two teams change the same config without knowing? Named individuals contribute facts and their own account of what they saw, without fear that those facts will end up in a performance review.

This isn't about avoiding accountability. Teams still own their systems, and repeated negligence is a management conversation, not a postmortem topic. The distinction is that postmortems exist to find and close gaps in our systems, and punishing people for honest reports guarantees the next report is dishonest or absent.

The teams that already run blameless reviews here, from the payments incident in March, report finding root causes they wouldn't have surfaced otherwise, because the engineer who typo'd a config volunteered the detail once they knew it wouldn't be used against them.

I'd like us to adopt a standard template: timeline, contributing factors, action items with owners and dates, and no names attached to blame. Happy to draft that template and pilot it on the next incident review.
