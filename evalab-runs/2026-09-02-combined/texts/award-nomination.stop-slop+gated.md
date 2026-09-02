I nominate Priya Raman and Marcus Ellery of the Deploy Platform team.

Last January our production deploy ran off a 42-step checklist pasted into a wiki page. One engineer read the steps while another typed. A deploy took three hours on a good night, and it needed two people who both knew where the bodies were buried. In March someone skipped step 19 and we served stale config to customers for six hours before anyone noticed.

Priya rewrote the checklist as a pipeline and made each step fail loud instead of failing quiet. Marcus built the rollback path first, before the deploy path, so we can undo a bad release in about 90 seconds. They shipped the work in pieces over eleven weeks, and they made four other teams run each piece in anger before they moved to the next one.

Anyone on call now runs one command. The median deploy takes 11 minutes. We ship 30 times a week instead of 6, and the deploy pager woke someone twice last quarter against nineteen times the quarter before.

Priya and Marcus carried this on top of their roadmap work. They also wrote the runbook that a new hire followed last month to ship a change on her second day.
