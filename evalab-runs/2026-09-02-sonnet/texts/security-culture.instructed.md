Security is not one team's job. It's everyone's, because the people who write the code are the ones who best understand where it can break.

Most incidents don't start with a zero-day. They start with a default password left in place, a permission granted too broadly, or a dependency nobody checked before adding it. Engineers make these calls dozens of times a week, usually without a security review anywhere nearby. That's the gap we're closing.

Here's what changes. Every team now runs a threat model before shipping a new service, not after. Security review moves into the same PR process as everything else, instead of a separate ticket that gets filed and forgotten. And we're building a short list of the mistakes that caused our last five incidents, so people can check their own code against real failures instead of guessing.

This works only if security stays boring and specific. If you write backend code, know what your service exposes and who can reach it. If you write frontend code, know what user input you're trusting. If you manage infrastructure, know who has access to what, and why.

Security engineering keeps its role: setting standards, running audits, responding when something breaks. What changes is where the first line of defense sits. It sits with whoever wrote the code, because they're already there.

Start this week. Pick one thing you own and ask what happens if it's misused. Write down what you find, and pass it to security review before you ship it.
