# Local-first sync

Your notes now write to the device first and go up to the server whenever a connection is available.

Every note lives in a local database on your device, so typing lands there straight away. You can write on a plane. When the app sees a connection, it pushes what changed and pulls in anything your other devices wrote while you were away. The status line tells you when the last sync finished, and how many notes are still waiting.

Editing the same note on two offline devices produces a conflict. We do not pick a winner. Both versions are kept, and the note opens with them side by side, the lines that differ marked, so you choose what stays. The version you drop stays in the note's history for thirty days.

Local-first sync is on by default in version 3.4, on iOS, Android and desktop. The web app follows next month.

That's 156 words. I cut the paragraph on the old read-only banner, as I flagged last time — the "most common complaint" line and the before/after contrast are gone, and one sentence about writing on a plane carries what's left of it. The conflict paragraph lost the reassurance that nothing is discarded while you decide, and the history note is now a bare fact rather than a consolation. The Safari reason for the web app delay is gone too; the delay itself stays.

Clean from the slopwatch gate (`lint_text`, no blocking issues). Version 3.4, the platform list, the web-app timing and the thirty-day window remain invented placeholders.
