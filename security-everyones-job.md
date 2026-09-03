# Security is everyone's job, not just the security team's

Our security team reviews architecture, runs the vulnerability program, and responds when something breaks. They cannot read every pull request, sit in every design discussion, or catch every misconfigured bucket. The people closest to the code and the infrastructure are the ones who write it and run it, so the decisions that keep us safe mostly get made outside the security team's room.

That means a few habits matter more than any policy document.

Threat model your own feature before you ship it. Ask what happens if this input is malicious, this token leaks, or this service goes down. You know the feature better than anyone reviewing it later.

Treat a security finding like a bug, not an accusation. If someone flags an issue in your code, the useful response is a fix, not a defense of the original design.

Report what looks wrong, even if you are unsure. A false alarm costs a few minutes of someone's time. A real issue left unreported costs a lot more. Nobody has ever been criticized here for reporting something that turned out to be nothing.

Ask before you skip a control. If a security step feels like it is slowing you down, say so. Sometimes the control is outdated and should change. Sometimes it exists because of an incident nobody wants to repeat. Either way, the right move is to raise it, not route around it quietly.

None of this replaces the security team's job. It changes what they are working with: fewer surprises, earlier signals, and problems caught while they are still cheap to fix.

If you see something that concerns you, say something. That is the whole policy.
