Local-first sync is now live in version 3.2.

Until now, editing a note offline meant your changes sat in a local queue that only flushed when you reopened the app. If you closed it on a plane, the queue stayed put, and people lost work that way.

The new version keeps a full local copy of your notebook on the device. That copy is the one you edit; the server holds a mirror. Each change is recorded as a discrete operation rather than a file snapshot, and on reconnect those operations replay in the order you made them.

When two devices edit the same note offline, neither wins by timestamp. The server interleaves the two operation lists by the position each edit targeted. Edits to different paragraphs merge silently. Edits to the same paragraph give you one note with both versions, split by a marker line naming the device and local time. A delete never overrides an edit, so the note stays and the deletion waits for you in the sync panel.

Sync runs in the background. Attachments over 25 MB still wait for a connection; chunked upload for those is not in this release.
