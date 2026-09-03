Why we should run blameless postmortems

Last month's outage took four hours to diagnose because the person who touched the config first spent the first hour worried about how it would look, not about fixing it. Blame slows down the people with the most relevant information right when speed matters most.

A blameless postmortem separates two questions we currently tangle together: what happened, and who should feel bad about it. Keep the first, drop the second. The engineer who pushed the change, the reviewer who approved it, the on-call who missed the alert made reasonable choices given what they knew at the time, with the tools and information available to them. If the system let a reasonable choice produce a bad outcome, fix the system.

This isn't a pass on accountability. People still own their actions, and repeat negligence still gets addressed directly with the person and their manager, but a review's energy should go to the timeline: the missing alert, the confusing runbook step, the deploy tool that didn't warn anyone. Fix those and the next person avoids the same trap. Google and Etsy adopted this years ago, and their postmortem docs show it: engineers write down exactly what they saw and thought, including their mistakes, because nothing bad happens to them for it.

I'd like us to try this for our next incident review. Happy to draft the template.
