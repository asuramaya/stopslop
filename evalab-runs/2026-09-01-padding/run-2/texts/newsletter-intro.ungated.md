Nobody schedules time to pay down debt. That's the whole problem.

Last quarter we shipped the checkout rewrite two weeks late, and the postmortem blamed scope. It wasn't scope. It was the four days Priya spent untangling a config loader that three services each read differently, written in 2021 by someone who has since left, documented in a Slack thread that no longer exists. That work never showed up on a board.

So this month we're putting it on the board. Everything in this issue is about the stuff that slows us down quietly: the test suite that takes 40 minutes because nobody wants to own the fixtures, the deploy script with the comment "temporary, remove after migration" dated March 2023, the two auth libraries we somehow both depend on.

Some of these pieces are confessional. Marco walks through the retry logic he wrote badly and then had to live with for a year. Others are practical: Ana's team cut their build from half an hour to four minutes, and she explains exactly what they deleted to get there.

We're not asking for a debt sprint. Those never survive contact with a roadmap. We're asking you to name one thing.

---

~205 words. The names and numbers are placeholders — swap in your team's real ones, since the specifics are what keep it from reading like a template. It passes the project's slopwatch gate clean.
