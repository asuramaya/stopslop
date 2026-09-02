**Security work belongs on your team's board**

Last quarter the security team reviewed 340 pull requests and filed 61 findings. There are four of us. The math stopped working around March, and the review queue is now nine days deep. So we're changing how this runs.

Starting Monday, every team owns the security of what it ships. In practice:

- Each team names a security point of contact. Roughly two hours a week: run the threat model for new services, triage Dependabot alerts for your repos, and be the person we page when something in your area looks wrong.
- Threat models move into design review. If your design doc touches auth, payments, or customer data, it needs a section on what an attacker gets when this goes wrong. Template is in the handbook under Design Review.
- We're publishing our review checklist, the same one we've been running by hand. If your team can work through it, we don't need to be in the loop before merge.

We keep incident response, pen test coordination, anything that needs a specialist, and office hours Tuesdays 2-4.

We're not adding a gate. Nothing new blocks your deploy. If your point of contact is on vacation and an alert sits for three days, nobody gets a talking-to. This works better when you do it because it makes your service harder to break into, not because a dashboard turned red.

First session for points of contact is Thursday at 10, 45 minutes, and we'll walk through the checklist together. Questions in #security.
