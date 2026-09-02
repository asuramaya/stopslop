**Proposal: one quarter of engineering time for debt paydown**

I'm asking for the team's next quarter to go to internal work instead of roadmap features.

The case is arithmetic, not aesthetics. Over the last two quarters our median time from ticket to merged fix has gone from [X] days to [Y]. Nothing about the team changed. What changed is that four of our services now share a config layer nobody owns, our test suite takes [N] minutes and fails intermittently often enough that people re-run it by reflex, and two of the three highest-traffic endpoints still route through code we forked off a vendor SDK in 2023 and never reconciled. Every feature we ship pays a tax to all three.

The plan for the quarter is narrow on purpose. Consolidate the config layer behind one owner and one interface. Get the suite under [N/3] minutes and quarantine the flaky tests rather than tolerating them. Retire the SDK fork. We're not rewriting anything, and we're not touching the parts of the system that work.

By the end of the quarter I'd expect feature lead time back where it was, plus headroom, and an on-call rotation that stops spending its nights on the same three alerts.

The cost is real. Whatever is on the roadmap for Q4 slips by roughly a quarter, and we should tell the people who depend on it now rather than in October. My argument is that the slip is happening either way, just spread across four quarters instead of one, and paid at a worse rate.

Happy to bring the supporting numbers to whichever review you'd prefer.
