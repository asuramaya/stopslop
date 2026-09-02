We ran the review of the March 4 checkout outage last Thursday. Twenty minutes in, someone asked who pushed the config change. The room went quiet. Dana answered, apologized twice, and said almost nothing for the remaining forty minutes. We left with one action item: add a second approver to that repo.

That meeting cost eight engineers an hour and produced a rule nobody will remember by June. The real material was in Dana's head and we scared it out of her. She had noticed the staging environment drifting from production three weeks earlier. She mentioned it in a thread that died. She pushed the config on a Friday because the ticket had been open since January and her manager kept asking about it.

I want us to run these reviews without asking who. Ask what the person saw, what they believed at the time, and what the system told them. Write the timeline before anyone assigns fault. Publish it where the whole engineering org can read it.

Two objections come up. People worry that dropping blame drops accountability. Accountability lives in the fixes we commit to and ship, not in whether someone felt bad in a conference room. Others worry that reviews turn into therapy. Give the facilitator a timeline template and a hard stop, and they won't.

I'll facilitate the next three myself. I'll write the template this week and share it Monday. If we run four of these and learn nothing we couldn't have learned by asking who broke it, I'll drop the argument and say so in this channel.
