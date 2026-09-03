## Reporting exports slipped again — new date Oct 17

The chunked job cleared the rate limit and passed staging Sept 8. Then we ran it on a real account: exports over 200k rows take 41 minutes, and the vendor expires job tokens at 30. Refreshing mid-run restarts from row zero. Their API, not our code.

So we're doing two things at once. Ticket filed asking them to raise the token TTL (no commitment yet), and Marcus and Dana start on persisting partial results Monday, about three weeks. We can't sit around waiting for the vendor.

I set Sept 26 off a staging run without testing a big account. My call, cost us three weeks.

Thanks to Sam and Priya for covering on-call through the Aug 30 pager storm and the cutover weekend.

Sales knows. I'm calling the two customers today.
