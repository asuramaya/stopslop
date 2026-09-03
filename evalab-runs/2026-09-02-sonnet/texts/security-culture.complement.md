Security is everyone's job here, not just the security team's. That's not a slogan — it's how the on-call rotation actually works, and it's worth saying plainly so new hires don't assume otherwise.

Every engineer who ships code decides, in small ways, how secure that code is. The person who writes a database query decides whether it's parameterized. The person who adds a new API endpoint decides what it checks before it returns data. The person who approves a pull request decides whether those checks got tested. None of that work belongs to a separate team sitting behind a queue.

The security team's job is different: set the defaults, build the tools that catch mistakes early, and handle the incidents that need specialized judgment. They review architecture for new systems and run the audits nobody else has time for. What they can't do is inspect every line of code before it ships. At our size, that was never realistic.

So a few practices matter more than any policy document:

Report anything that looks wrong, even if you're not sure it's a real problem. A false alarm costs an hour. A missed one costs a lot more.

Treat a security fix like any other bug fix — merge it, don't schedule it for "later." Later is where vulnerabilities live the longest.

Ask the security team before you build your own auth, encryption, or session handling. Reinventing these usually means reinventing their mistakes too.

None of this requires a security background. It requires paying attention and asking a colleague when something seems off. That's the whole system, and it works because most of you already do it.
