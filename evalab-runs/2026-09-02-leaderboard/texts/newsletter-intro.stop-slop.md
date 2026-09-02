Priya spent four days in August rewriting the billing retry logic. The first version shipped in 2021 against a deadline, and since then seven of us added a special case around the loop at its center rather than open it. She opened it. The rewrite deleted 400 lines and closed two bugs that had been sitting in the backlog since March.

We asked the team this month what code they steer around. The answers came back fast, which tells you people have been keeping a private list. Session handling came up four times. The deploy script came up five. One engineer wrote "the file I do not name" and we knew which file.

So this issue collects what we found. Marcus writes about the session refactor and why he split it into three pull requests instead of one. Dana walks through the deploy script rewrite, including the two hours she lost to a hardcoded staging hostname from 2019. We also print the full list of what the team named, with owners next to eleven of the twenty items and blanks next to the rest.

Read the blanks as an invitation. If you have been avoiding one of them, tell Dana and we will put your name there.
