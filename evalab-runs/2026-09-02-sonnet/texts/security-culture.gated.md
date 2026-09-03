Security is everyone's job, not just the security team's

Our security team reviews architecture, runs the vulnerability program, and responds when something breaks. They cannot read every pull request, sit in every design discussion, or catch every misconfigured bucket. The people closest to the code and the infrastructure write it and run it, so the decisions that keep us safe mostly get made outside the security team's room.

A few habits matter more than any policy document.

Threat model your own feature before you ship it. Ask what happens if this input is malicious, this token leaks, or this service goes down. You know the feature better than anyone who reviews it later, so you're best placed to spot where it breaks.

Treat a security finding like a bug, not an accusation. If someone flags an issue in your code, fix it — don't defend the original design. Report what looks wrong, even if you're unsure. A false alarm costs a few minutes of someone's time; a real issue left unreported costs a lot more. Nobody here has been criticized for reporting something that turned out to be nothing.

Ask before you skip a control. If a security step slows you down, say so. Sometimes the control is outdated and needs to change. Sometimes it exists because of an incident nobody wants to repeat. Either way, raise it instead of routing around it quietly.

None of this replaces the security team's job. It gives them fewer surprises, earlier signals, and problems caught while they're still cheap to fix.

If you see something that concerns you, say something. That's the whole policy.
