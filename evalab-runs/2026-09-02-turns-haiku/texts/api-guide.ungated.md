**Introduction**

The Calendar Bookings API is a tool that lets your software talk to a scheduling system. Instead of manually entering appointments, your app can automatically create, update, and view bookings through simple requests.

Think of an API as a waiter in a restaurant. You give it an order (a request), it passes it to the kitchen (the system), and it brings back your food (a response). The Calendar API works the same way—you send a request asking to create a booking or check availability, and it sends back a response with the result.

This guide walks you through everything step by step. We'll show you what requests look like, what responses you'll get back, and how to handle errors. If you're completely new to APIs, that's fine—we explain the concepts as we go and provide copy-paste examples you can try immediately.

**Authentication**

Before your app can talk to the Calendar API, it needs to prove who it is. We use API keys for this—think of it like a password that your app uses to log in. You'll find your key in the dashboard under Account Settings. Never share it or put it in code you upload to GitHub.

To use the key, include it in a `Bearer {api_key}` header with every request. If a request doesn't have a valid key, the API refuses it and sends back an error. If you think someone got your key, go regenerate it right away—the old one stops working immediately.

**Rate Limits**

To keep the service stable for everyone, we limit how many requests you can make in a given time window. Most accounts can make up to 100 requests per minute. If you exceed this limit, the API returns a 429 error message that tells you to slow down. Simply wait a minute and try again. If your app regularly needs more requests, contact support about upgrading to a higher tier.

Throughout this guide, every example shows exactly what to send and what you'll get back. You can follow along and try them yourself.
