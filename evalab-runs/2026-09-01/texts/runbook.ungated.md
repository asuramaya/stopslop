A runbook, ~250 words. (Note: this is chat output, not a file, so no stopslop ruleset applies — `ste100` here routes only to `CONTRIBUTING.md`.)

---

## Runbook: rotate the TLS certificate on a load balancer

**1. Detect approaching expiry**

Check the served certificate, not the file on disk:

```
echo | openssl s_client -connect lb.example.com:443 -servername lb.example.com 2>/dev/null \
  | openssl x509 -noout -subject -enddate
```

Rotate at 30 days remaining. Set a monitoring alert at 30, 14, and 7 days so the check does not depend on a person running it.

**2. Request the replacement**

Generate a key and CSR on the host that will hold them:

```
openssl req -new -newkey rsa:2048 -nodes -keyout lb.key -out lb.csr \
  -subj "/CN=lb.example.com"
```

Include every SAN the current certificate carries; compare against `openssl x509 -noout -text` on the old one. Submit the CSR to the CA, then assemble the leaf plus the intermediate chain in that order.

**3. Install**

Copy the old cert and key to a timestamped backup directory first. Install the new pair, set the key to mode 600 and the owner the LB process runs as, then validate the config (`nginx -t`, `haproxy -c -f`) before you reload. Reload, do not restart, so connections drain.

**4. Verify**

Re-run the `s_client` check from step 1 and confirm the new dates and fingerprint. Verify the chain with `-verify_return_error`, and test from outside your network — a missing intermediate often only shows there. Check each LB node behind the VIP individually.

**5. Roll back**

Restore the backed-up cert and key, revalidate the config, reload. Confirm with `s_client` that the old fingerprint is back. Roll back on any chain or handshake error rather than debugging in production.
