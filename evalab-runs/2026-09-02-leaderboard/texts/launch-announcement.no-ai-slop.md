# Dark mode is here

Dark mode ships today in version 3.2 for iOS, Android, web, and desktop.

We built it because of the support tickets. For two years, the most common feature request was some version of "please, my eyes, it's 1am." We counted 4,300 of them. The second most common was about tables, which is a different post.

Turn it on in Settings → Appearance. You get three options: Light, Dark, and Match System. Match System follows your OS setting, so your notes go dark when the rest of your phone does at sunset.

A few things we sweated:

Text is off-white (#E8E8E8), not pure white. Pure white on a dark background produces halation, where letters appear to glow and bleed at the edges. Off-white reads better in a dark room, especially if you have astigmatism.

Your highlight colors still work. We remapped all six to darker variants so a yellow highlight doesn't turn into a flashlight. Notes you highlighted in 2019 will look right.

Code blocks, tables, and images keep their contrast ratios. Everything meets WCAG AA, and most of the interface meets AAA.

Images with transparent backgrounds were the hard part. A logo saved as a transparent PNG with black text used to vanish. We now detect near-black transparent images and add a subtle light backing behind them.

Dark mode is free for all users, including the free tier.

If something looks wrong, especially in a note with unusual formatting, send us a screenshot at support@example.com. We read every one.
