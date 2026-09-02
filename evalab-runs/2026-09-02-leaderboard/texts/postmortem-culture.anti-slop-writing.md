**We should stop asking who broke it**

The March 4 checkout outage. Remember the follow-up meeting? Forty minutes of people explaining why the config change wasn't their fault, and about nine minutes on the actual failure, which was that staging hasn't matched prod since we split the VPCs back in January. We fixed nothing that day. We just learned whose calendar to avoid.

That's what happens when a postmortem has a defendant. People optimize for looking innocent, so you get the shortest defensible story instead of the messy true one, and the messy true one is the only version worth writing down.

Blameless doesn't mean nobody's accountable. That's the objection I keep seeing in Slack, so let's kill it now. Accountability lives in the action items and in who owns them, with dates. What we give up is hunting for a person to pin it on, when the real finding is that a tired engineer at 11pm pushed a change no reviewer questioned and no gate caught.

Google's SRE book argues this better than I can, and Etsy has run postmortems this way since roughly 2012. Neither shop is soft.

What I'd change about the review itself: no names in the doc, use roles instead. A facilitator who wasn't on call for that incident. Timeline built from logs before anyone talks. And one standing question near the end, which is what made the wrong action look reasonable at the time.

Cheap experiment. Run it on the next Sev2, keep the old format for anything customer-facing if that feels safer, then compare action items six weeks out.

I'll draft the template unless someone objects by Friday.
