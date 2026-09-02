Last month we shipped the payments rewrite, and three of you told me the same thing in retro: the code we touched fought back. So this issue is about the parts of our system that slow us down, and what we plan to do about them.

Priya opens with the auth service. She counted 41 call sites for a session helper that two people understand, and she walks through how she cut that to nine without a rewrite. Then Marcus writes about the migration we abandoned in March. He argues we made the right call and shows the numbers behind it.

I want to say something about how we talk about this. Engineers on this team keep apologizing for shortcuts they took under deadlines I set. Stop. We chose speed, we got speed, and now we pay some of it back. That trade was mine to approve and I approved it.

Two asks. First, when you file a debt ticket, name the cost in hours per month rather than calling the code bad. Second, come to the October planning session with one thing you want to fix and a rough estimate. We are reserving 15 percent of next quarter's capacity for this work, and I would rather you spend it than I decide where it goes.
