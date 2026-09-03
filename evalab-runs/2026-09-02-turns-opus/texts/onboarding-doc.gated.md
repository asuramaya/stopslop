# Welcome to Payments

Run a payment end to end in sandbox during your first week, and be able to explain what happened at each hop. That's the whole goal, and everything below serves it. Start with access. Ask your onboarding buddy for the payments-dev VPN profile, a sandbox merchant account, read access to the ledger replica, and an invite to the payments Discord server. Requests go through the platform team and usually clear in a day, so file them before you start reading. While you wait, skim the service map so the names in those documents mean something when you get to them.

Then read three documents, in this order. The ledger schema note explains why every balance change is two rows and never an update. The idempotency guide explains why every write endpoint requires a client-supplied key. The settlement timeline explains why a payment that looks finished on Monday can still fail on Wednesday. None of them is long, and the third one is the one people wish they had read sooner.

Two rules matter more than the rest. We do not mutate or delete a ledger row; a correction is a new entry that references the old one. And we do not treat a processor callback as truth; we reconcile against the end-of-day file and let that win. Both rules have cost us money when someone forgot them. Your first ticket is small on purpose, normally something in the refund path, where the code is well covered and the blast radius is low. Pair on it with whoever reviews your access requests. Nobody here ships their first payments change alone.

## Who to ask for what

Access, VPN, and anything needing an approval you can't grant yourself goes to your onboarding buddy first. They know which requests the platform team handles and which ones need a manager signature, and they'll save you a day of guessing. Nothing here is a test, so ask early rather than working around a missing permission.

Ledger questions go to the #payments-ledger channel in Discord, where the people who wrote the double-entry schema read. They would rather answer a question than review a migration that got the sign wrong. Processor behaviour goes to #payments-processors, which covers quirks in callbacks, retry semantics, and anything that smells like the other side is misbehaving. Open a thread on your message rather than continuing in the main channel, and put the payment reference and the processor name in the first line; it's the first thing anyone will ask for. For everything else, ask your manager, normally at the weekly one-to-one, but go sooner if the thing is blocking you.

For on-call and anything happening right now in production, page through the payments rotation rather than posting in a channel. Channels are for questions that can wait an hour. If money is moving wrong, it can't wait an hour, and nobody will mind being paged over it. Don't reach for @here as a substitute; it wakes forty people and reaches nobody who can act on what you found.

## The on-call rotation

The rotation is one week long and hands over on Tuesday morning, so nobody inherits a weekend they didn't see coming. You won't be on it for your first two months. Before you join, you shadow a full week: same pages, same channel, no responsibility for the fix. Shadowing is where you learn that most pages are settlement files arriving late, not the system on fire.

Two habits from the people who've done it longest. Write in the incident channel as you go, even when you're unsure, because the person who picks it up after you needs your dead ends as much as your findings. And escalate on a timer rather than on a feeling; if you're thirty minutes in with no theory, wake the secondary. That is what the secondary is for, and the rotation is built assuming you will use it.
