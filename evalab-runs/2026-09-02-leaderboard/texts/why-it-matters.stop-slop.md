Your checkout service returned errors to four percent of users for eleven minutes last Tuesday. You heard about it the next morning, from a support ticket.

The dashboards stayed green the whole time. CPU sat at thirty percent, and the health check returned 200 because it never touched the payment gateway. Nobody on the team had built anything that would notice one dependency failing part of the time.

So you guess. An engineer reads the checkout code, forms a theory, adds a log line, and ships it to production to test the theory. Two hours later the team has one more fact and four more theories. You get an answer six hours after the errors stop, and half the team spent the afternoon on it.

Instrumentation changes the shape of that morning. Give every request a trace ID that follows it through the gateway and the retry queue, and record the latency and status of each hop. Now you pull up one failed order, read the trace, and see the payment gateway timing out at three seconds while your client waits five. You answer a question nobody wrote a dashboard for, because the data was already there.

That gap between the two mornings is the whole argument. A team without traces pays for every incident twice, once in downtime and once in the engineering hours spent reconstructing what the servers already knew. The junior engineer who joined in March can debug the checkout path on her second week, without waiting for the person who wrote it in 2023 to come back from vacation.
