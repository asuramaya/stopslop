# TLS certificate rotation runbook for a load balancer

**Scope:** one public-facing LB listener on port 443.

## 1. Detect approaching expiry

- Check the live endpoint:
  `echo | openssl s_client -connect lb.example.com:443 -servername lb.example.com 2>/dev/null | openssl x509 -noout -dates -subject`
- Rotate when `notAfter` is under 30 days away. The monitoring check `tls_cert_days_remaining` alerts at 30 and pages at 7.
- Confirm which listener and which cert ID the LB uses before you touch anything; a listener can reference a cert that is not the one you tested.

## 2. Request and install the replacement

1. Generate a new key and CSR (2048-bit RSA or P-256), keeping the same CN and every SAN currently in use. Missing a SAN is the most common outage in this procedure.
2. Submit the CSR to the CA. Retrieve the leaf and the intermediate chain.
3. Upload leaf + chain + key to the cert store as a **new** cert ID. Do not overwrite the old one; it is your rollback.
4. Point the listener at the new cert ID. Leave the old cert uploaded.

## 3. Verify

- Re-run the `s_client` command above from outside the network. Check the new `notAfter`, the subject, and every SAN.
- Run `openssl s_client -connect ... -showcerts` and confirm it returns both the leaf and the intermediate, so you know the chain resolves.
- Test each LB node individually if the pool is not yet fully converged.
- Watch TLS handshake error rate and 5xx for 15 minutes.

## 4. Roll back

Repoint the listener to the old cert ID. This takes effect in seconds and needs no redeploy. Re-verify with `s_client`, then investigate before retrying.
