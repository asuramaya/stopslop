# Security is not just the security team's job

Right now, if you find something odd — an S3 bucket that looks too open, a dependency you don't recognize, a login flow that skips a check — the default move is to file a ticket for AppSec and move on. That queue is currently 40 tickets deep with a median age of 11 days. We are four people. You are 180.

The math doesn't work, and it was never supposed to. AppSec's job is to build the tools, set the defaults, and handle the hard cases. Deciding whether a new endpoint needs auth is not a hard case. It's a Tuesday decision, and the person making it should be the person writing the endpoint.

Three things change this quarter.

1. Threat modeling moves into design review. If your design doc touches auth, PII, or money, add a section on what an attacker would try. Half a page. AppSec will review the first few with you until it feels routine.

2. Dependency alerts route to the owning team, not to us. You get the alert, you decide: patch, pin, or accept with a written reason.

3. Office hours, Thursdays 2-4pm, no ticket needed. Bring a half-formed worry. "This feels wrong but I can't say why" is a good use of the slot.

What we are not doing: making you responsible for things you can't control. Infrastructure hardening, incident response, vendor review — still ours.

The failure mode I want to avoid is security becoming a checkbox someone else ticks after you've shipped. By then the cheap fix is gone.
