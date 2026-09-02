We Broke Up the Monolith, and Broke Production Twice Doing It

Our billing system was one Rails app: 400,000 lines, a 52-minute test suite, one deploy a week if nobody flinched. It's eleven services now. Getting there took two years, and the architecture diagram was the easy part.

I want to talk about what the diagrams leave out. How we picked the first seam, and why we'd pick differently now. What happened the night the inventory service started serving stale reads under load — and the four weeks of quiet data drift nobody caught before that. Why we kept one shared database long after the blog posts said to split it, and why that was the right call for us. You'll leave with a way of choosing seams that survives contact with a real codebase: start where the on-call pages cluster, not where the domain model looks tidy.

You'll also get the honest ledger. Deploys went from weekly to about forty a day. Our infrastructure bill nearly doubled. Some monoliths should stay monoliths, and I'll show you how to tell which one you're holding. For engineers on a service older than five years, with more than one team pushing to it.

The numbers are placeholders — swap in your real line count, test time, service count, and deploy frequency. Concrete figures are what make an abstract get accepted; generic ones read as filler. Tell me your actual migration and I'll rewrite it around those.
