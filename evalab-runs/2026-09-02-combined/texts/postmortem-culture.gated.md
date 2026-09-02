Let's stop asking who broke it

Last month's outage review took forty minutes, and about thirty of those went to establishing whose deploy it was. We found out. It didn't help. The config path that swallowed the error is still there, and nobody wrote it down, because writing it down would have meant naming a person again.

That's the real cost of doing it this way. Not hurt feelings, though there are those too. The cost is information. People who expect to be judged report less, report later, and report the version of events that makes them look reasonable. You can't fix a system when all you're shown is the sanitized picture of it. Blameless postmortems aren't about being nice. The premise is that a competent engineer did what seemed correct given the information and tools in front of them at the time. If that produced an outage, the interesting question is what made the wrong action look right. Missing alert? Staging that doesn't match prod? A runbook three refactors stale? Those are fixable. "Sam should have been more careful" is not, and we've written some version of it four times this year.

So, three rules. The writeup names systems and timelines, never individuals. The person closest to the incident writes it and gets thanked publicly for doing so. Every postmortem ends with action items that have owners and dates, and we check them at the next one.

I'll run the first one. Give me the next Sev 2.
