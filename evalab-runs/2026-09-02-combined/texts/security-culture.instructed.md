# Security is not the security team's job

We have four people on the security team and about three hundred engineers. Do the arithmetic and the current model falls apart: every design doc, every dependency bump, every new S3 bucket eventually queues behind four calendars. The queue is currently eleven days deep. That is not a staffing problem we can hire our way out of, and it is not a sign that those four are slow.

Here is what changes this quarter.

Threat modeling moves to the team writing the feature. You know where the data goes and who touches it. The security team is publishing a one-page template with four questions; fill it in during design, not after. If the answers get uncomfortable, that is when you page them, and they will show up with real time to think instead of a rubber stamp two days before launch.

Dependency review moves into CI. Nothing to remember, nothing to schedule.

We are also killing the security sign-off gate for anything that does not touch auth, payments, or PII. That gate caught two real issues in the last eighteen months and delayed roughly ninety launches. The trade is deliberate: fewer checkpoints, more people who can spot the problem in the first place.

The part that takes actual work is the training, and it will be dull. Two hours, quarterly, on the things that keep showing up in our own incidents. Not generic OWASP slides. Our incidents, our code, with names taken out.

If this works, the security team stops being a queue and starts being the people you consult when something is genuinely hard. That is the only version of this that scales.
