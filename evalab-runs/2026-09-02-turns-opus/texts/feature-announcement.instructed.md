Local-first sync is now available in version 3.2.

Until now, editing a note offline meant the app queued your changes and pushed them on reconnect. If you edited the same note on your phone and laptop while both were offline, whichever device reconnected second overwrote the first. People lost work that way, and we heard about it.

The new sync engine tracks changes per paragraph instead of per note. Paragraphs that only one device touched merge without a prompt, so a note edited at the top on your laptop and at the bottom on your phone comes back whole. Where both devices changed the same paragraph, you get a side-by-side view with each version, its device name, and its timestamp. Nothing overwrites until you pick one.

Offline edits sync in under two seconds on reconnect for notebooks up to 5,000 notes. Larger ones take ten to thirty seconds on first sync while the index rebuilds.

Attachments still need a connection. An image added offline uploads when you reconnect, marked as pending until then.

Local-first sync is on by default. Turn it off under Settings, then Sync.
