Assuming a generic app name — swap "Marginal" for yours.

---

# Dark mode ships today

Dark mode is live on web, iOS, and Android. Open Settings, then Appearance, and choose Dark, Light, or Match system.

This took us three months longer than planned, and the reason is boring: our first build was a color inversion. It passed review and fell apart in real notes. Pasted screenshots glowed. Code blocks turned into neon. Anything a user had highlighted in yellow became unreadable against the new background.

So we rebuilt it from the text up. Body text is now #E8E8E6 on #16161A rather than white on black, because pure white on pure black makes letters bloom for a lot of readers, especially at small sizes late at night. Every highlight color, tag chip, and syntax token was re-picked to clear WCAG AA contrast against the dark surface. The yellow highlight is now amber. It looks different from the light-mode version on purpose.

Match system follows your OS. If you would rather not hand that decision to your phone, there is a schedule option that flips at sunset and sunrise based on your location, or at times you set.

Three things are not done yet. Exported PDFs still render light, as does printing. Public share links follow the reader's system setting rather than yours, which surprised a few beta testers who expected their note to look the way they left it. Attachment previews from third-party viewers stay light until those viewers add support.

Update from the App Store, Play Store, or reload the web app. Bugs go to support@marginal.app.
