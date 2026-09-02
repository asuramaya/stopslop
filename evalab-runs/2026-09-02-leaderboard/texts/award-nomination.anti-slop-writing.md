I'm nominating the Release Engineering group (Priya, Marcus, Dan, and Tomo) for the Q3 Craft Award.

Two years ago a deploy meant a 40-minute window, a checklist in a Google Doc that nobody trusted, and someone staying late to babysit it. I know because I was that someone, twice. In March they started tearing it down. By August we were shipping on merge, with automatic rollback wired to the error budget, and median time from merge to production dropped from 51 minutes to just under four.

What I want to call out isn't the number, though. It's how they got there. They didn't rewrite everything. They spent the first six weeks just watching how teams actually deployed, including the ugly workarounds people had invented, and then built for that instead of for the process on paper. Tomo's migration guide got read by 60+ engineers and generated almost no support tickets. That's rare.

Rollbacks are down. On-call pages during deploys have basically stopped. Two teams that used to ship monthly now ship daily, and neither of them was asked to.

Anyway. Good infrastructure work is invisible when it works, which is exactly why it needs saying out loud sometimes.
