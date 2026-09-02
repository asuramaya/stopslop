### Notes from three days at $CONFERENCE, from the four of us who went

We split up on purpose. Priya took the reliability track, Marco sat in on everything database-shaped, Dani chased the security talks, and I wandered. Each morning we compared notes over bad hotel coffee. Three things came back with us.

Nobody has solved on-call. Six talks promised it, and all six described a rota, a runbook, and a person who is tired. The most honest one came from a payments team who admitted their alert volume fell 60% only after they deleted 400 alerts and rebuilt from four SLOs. That isn't a tool. That's a decision someone had to defend in a meeting, and by their account the meeting was harder than the work.

Postgres is quietly eating the stack. Queues, vector search, job scheduling, feature flags — talk after talk was some team deleting a service and putting the thing in a table instead. Marco counted eleven. We have two candidates in our own architecture diagram.

The AI talks worth attending were about cost rather than capability. The demos were fine and the hallway conversations were better: token bills, evals, and how almost nobody has a regression test for a prompt. We don't either.

Priya is now writing an SLO proposal for Q4. Marco has a spike open on moving the notification queue off SQS. I'm booking a session to work out what "good" means for our summarizer before the next version ships.

Slides worth your time are in #conf-notes. Ask us anything.
