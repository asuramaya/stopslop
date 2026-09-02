# Dark mode is here

Dark mode shipped today for all Notekeep accounts, on web, iOS, and Android.

You turn it on in Settings under Appearance. Three options: Light, Dark, and Match System. Match System follows your OS setting, so your notes go dark at sunset if your phone does.

We took longer than we wanted to on this one. The first build was a straight color inversion, and it looked wrong: code blocks lost their syntax highlighting contrast, highlighted text turned muddy, and images with white backgrounds glared out of the page. So we rebuilt it. The dark palette uses a slightly warm near-black (#16161a) instead of pure black, which cuts the halo effect around white text on OLED screens. Every highlight color got a second variant tuned for the dark background. Images and embedded PDFs now sit on a neutral card rather than a white one.

A few details you might not notice right away:

Syntax highlighting in code blocks switches to a separate dark theme rather than reusing the light one at lower brightness.

Exported PDFs stay light regardless of your app theme, since that's what people print.

Shared note links respect the reader's theme, not the author's.

If you use a screen reader or high-contrast settings, dark mode inherits your system contrast preferences instead of overriding them. We tested against WCAG AA for text and interactive elements; the audit notes are in our accessibility docs.

Dark mode is available now on version 4.2 and later. Update from your app store, or reload the web app.

Found something that looks off? Reply to this post or write to support@notekeep.app. We're still tuning the highlight palette and want the reports.
