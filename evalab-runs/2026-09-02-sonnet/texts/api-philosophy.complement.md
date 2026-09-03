## Design philosophy

The API mirrors the way you already think about the data: resources map to nouns, HTTP verbs map to actions, and every response returns the object you just created or changed. There's no separate query language to learn and no envelope wrapping every payload in extra metadata you have to strip away.

Every endpoint requires a real network call, so we cache aggressively on our side and set standard `Cache-Control` headers so you can too. Rate limits are generous by default and returned in response headers, not buried in a support ticket you have to file.

Errors carry a specific error code and a message written for the person debugging at 2am, not a generic "something went wrong." A `422` tells you which field failed and why. A `429` tells you when to retry.

Versioning happens through a required `API-Version` header rather than a URL prefix, so a single client can pin to a known version while we ship changes underneath. We don't remove fields or change their meaning within a version; we add new ones.

None of this is exotic. The goal is an API that behaves the way you'd guess it behaves, so you spend your time on your product instead of on our documentation.
