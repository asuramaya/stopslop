Security is not the security team's job

Last quarter we had three incidents that reached production. None of them were exotic. One was a hardcoded token in a test fixture that shipped to a public repo. One was an S3 bucket someone opened up to debug an upload path and never closed. One was a dependency we pulled in on a Friday without reading what it did.

In all three cases, the security team found the problem after the fact. That is the pattern we want to change. Six people cannot review everything eight squads ship in two weeks, and asking them to try makes them a queue rather than a resource.

Here is what we are asking of every engineer, starting now.

1. Run the pre-commit secret scanner. It is in the template repo and takes about four seconds per commit.
2. Treat any change to IAM policy, bucket permissions, or auth middleware as a change that needs a second reviewer who understands what it does.
3. When you add a dependency, read its install scripts and check when it was last published. If that takes more than ten minutes, ask in #security-help and someone will pair with you.
4. Report anything that looks wrong, including your own mistake. We have never disciplined anyone for a self-reported incident and we are not going to start.

The security team's role shifts toward tooling, threat modeling on new systems, and being available when you are unsure. They will run office hours Tuesdays at 2pm.

If a control we are asking for slows you down in a way that feels pointless, say so. Some of them probably are, and we would rather fix the control than watch people route around it.
