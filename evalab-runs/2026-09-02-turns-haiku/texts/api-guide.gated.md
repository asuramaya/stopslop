The Calendar Bookings API lets you manage time-based reservations programmatically. Think of it as a way to automate scheduling—instead of manually managing bookings, you can let software handle it for you.

An API is like a communication channel between your application and our booking system. You send a request (like "create a booking for tomorrow at 2pm"), and the system sends back a response (like "booking confirmed"). REST just means we follow a standard format for these conversations—no special knowledge required to understand how it works.

You can create bookings with custom time slots, check which times are available to avoid double-bookings, change existing reservations, and cancel bookings. The system can automatically notify people when their booking changes, and it organizes results into pages so you're not overwhelmed by too much data at once.

Every request needs an API key—a password-like token that proves you're allowed to access your bookings. Add it to your request, and the system trusts that it's you. Get your key from your account dashboard. Keep it as a secret that you don't share, don't put in websites, and don't expose in your code. If you're building a website, store the key safely on your server and have your server make the requests instead of doing it directly from someone's browser.

The API enforces rate limits to keep the service stable for everyone. Your plan includes a maximum number of requests per minute—if you exceed this, the API will temporarily reject requests with a "too many requests" error. Design your application to space out requests or batch operations when possible. If you consistently hit rate limits, you can upgrade your plan for higher allowances.

This guide explains everything step-by-step, with examples in common programming languages and a safe testing environment to practice before going live.
