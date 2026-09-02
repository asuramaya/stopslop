Passes the repo's `slopwatch` gate clean. ~255 words:

---

# Dark mode, finally

Dark mode shipped this morning. It's in 3.4, on every platform, and it's on by default if your OS says so.

The delay was boring to live through. Our editor paints Markdown with a syntax theme, and flipping the app chrome dark while the code blocks stayed cream looked like a bug report waiting to happen. So we rebuilt the theme layer instead of bolting a filter on top. Every color in the app now comes from one token file, which is also why we could ship a high-contrast variant in the same release.

Three things you can change:

**Follow system, or don't.** Settings > Appearance has a manual switch and a schedule. The schedule uses your local sunset, not a fixed hour, so it drifts with the season.

**Per-notebook overrides.** Some people keep one notebook full of screenshots and want it light no matter what. Right-click the notebook, pick an appearance, done.

**True black for OLED.** Off by default, because on an LCD it looks like a hole. If you're on a phone, turn it on — we measured about 14% less battery drain over an hour of scrolling on a Pixel 9.

What we didn't do: images and PDFs are untouched. Inverting a photo of a whiteboard makes it unreadable, and we'd rather leave the bright rectangle than guess.

If something looks wrong — a washed-out highlight, unreadable link text — send us a screenshot at support@example.com. Theme bugs are easy to fix and hard to notice.

---

The specifics are placeholders you'll need to swap for real ones: version number, the 14% battery figure, the Pixel 9, the support address, and whether per-notebook overrides and the sunset schedule actually exist. They're what keeps the post from reading as generic, so replace them rather than deleting them.
