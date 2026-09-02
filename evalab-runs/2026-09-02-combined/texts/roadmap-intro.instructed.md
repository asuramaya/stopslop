# Roadmap

We publish this roadmap because the alternative is worse: you find out what we're building when it lands, and by then the design is fixed. Most of what follows came from support tickets, GitHub issues, and the handful of customers who email us directly when something breaks at 2am.

Three things shape the next two quarters. First, build times. Our p95 cold build is 94 seconds and we think we can get it under 40 by rewriting the dependency resolver. Second, the plugin API, which has grown by accretion since 2023 and now has three ways to register a hook. We're deprecating two of them, with a twelve-month migration window and a codemod. Third, self-hosting, which about a fifth of you have asked for and none of you have been able to do.

What isn't here matters too. We're not adding a hosted database this year. We're not shipping an AI assistant into the editor.

Dates are estimates. Items move, and when they do we update this page and note the change in the changelog rather than quietly editing the entry. Anything marked "exploring" may never ship at all.
