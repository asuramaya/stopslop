**Proposal: Dedicate Q4 engineering capacity to technical debt**

**The ask:** Hold the team to in-flight commitments only for one quarter. No new feature scope. Everything else goes to debt.

**Why now.** Three things have gotten measurably worse. Our median PR now takes [X] days from open to merge, up from [Y] a year ago, mostly waiting on a test suite that fails intermittently. On-call pages have roughly doubled, and [Z]% of them trace back to the same two services we keep patching instead of fixing. New engineers take about [N] weeks to ship anything of consequence, because the paths through the checkout code are undocumented and largely untested.

None of this shows up as a missed deadline. It shows up as everything taking longer than it should, which is harder to see and harder to argue about. That's why I'm asking for it as a block of time rather than as 20% carved off each sprint. We tried the 20% version last year. It lost to whatever was urgent, every time.

**What we'd do.** Split the quarter roughly in three: stabilize the test suite and cut CI time; consolidate the two services that generate most of our pages; pay off the checkout module, with tests, so it stops being a single-person dependency.

**What you get back.** Faster merges, fewer pages, and a real estimate on the platform work planned for next year. Right now any estimate I give you for that work is a guess.

**The cost.** One quarter of feature velocity, deliberately, instead of the same amount lost invisibly over the next four.

I left the metrics as placeholders since I don't have your actual numbers. Fill those in before sending — a proposal like this lives or dies on them.
