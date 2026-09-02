# Moving to a new platform next quarter

Starting in Q1, the service you use today will run on a new platform. The migration window opens January 12 and closes February 27.

Here is what changes for you. Your account URL moves from app.oldhost.com to app.newhost.com. Old links redirect for 12 months, so bookmarks and saved reports keep working through February 2027. API endpoints change hosts on the same schedule; the v2 endpoint paths and request formats stay identical, so most integrations need one base-URL edit and nothing else. Single sign-on configurations carry over automatically. If you authenticate with API keys, you will need to reissue them after your account moves, since keys are scoped to the platform they were created on.

Data moves with you: every project, file, and audit record, with history intact. Nothing is deleted, and nothing needs to be exported and reimported.

Each account has a scheduled cutover, and we will email your admins four weeks and then one week ahead with the exact date and a two-hour maintenance window. Reads stay available during that window; writes pause.

Two things worth doing now. Check that your admin contact in account settings is current, because that is where the cutover notices go. And if your firewall allowlists our IP ranges, the new ranges are published at newhost.com/ranges — add them before your cutover date.

We moved because the old platform could not support per-region data residency, which a large share of you have asked for and which the new one handles natively.

Questions go to support@example.com, or your account manager if you have one.
