This API lets you manage calendar bookings for your application. Think of it as a mailbox where your app sends requests (like "book Tuesday at 2 PM") and receives back a confirmation with all the details.

REST API means your app sends messages using the web. JSON is the format we use—a simple text style that both your app and our service can read. Calendar data stays timezone-aware, so a 2 PM booking always means 2 PM in your location, wherever our servers sit. Your app checks what times are free on a given day, picks one for a customer, and books it. Later, your app can change or cancel that booking. If two customers try to grab the same slot at the exact same instant, our system stops the conflict—one booking goes through and the other gets an error message explaining why.

Every response includes the full booking details, error codes, and messages to explain what went wrong.

Authentication

Authenticate all requests using a bearer token in the Authorization header. Include your API key as `Authorization: Bearer YOUR_API_KEY`. You can generate or rotate API keys from your account settings. Each key remains valid until you revoke it or create a new one. Requests without a valid token receive a 401 Unauthorized response.

Rate limits

Our service enforces rate limits to ensure fair access for all users. Standard accounts allow 1,000 requests per minute. If you exceed this limit, the API returns a 429 Too Many Requests response. The response includes a Retry-After header telling you how long to wait before trying again. Check your account settings to see your current rate limit and request a higher tier if your application needs it.
