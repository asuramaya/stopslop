A runbook, procedural style. Not written to a file — say the word if you want it saved somewhere.

---

# Runbook: Rotate the TLS certificate on the load balancer

## 1. Detect approaching expiry

Check the expiry date from outside the fleet:

```
echo | openssl s_client -connect lb.example.com:443 -servername lb.example.com 2>/dev/null \
  | openssl x509 -noout -enddate -subject
```

Rotate when fewer than 30 days remain. The monitoring alert `tls_cert_days_remaining < 30` fires the same condition. If the alert is silent and the date is near, the probe is broken — fix the probe first.

## 2. Request the replacement

1. Make a key and a CSR. Use the same subject and all SAN entries from the current certificate.
2. Send the CSR to the CA. Do not send the private key.
3. When the CA returns the certificate, put the leaf and the intermediates into one file, leaf first.
4. Confirm that the key and the certificate agree:
   `openssl x509 -noout -modulus -in new.crt | openssl md5` must equal the same command on `new.key`.

## 3. Install

1. Copy the old certificate and key to a dated backup directory on each load balancer node.
2. Write the new pair with mode 0600, owner `lb`.
3. Test the config: `nginx -t` (or the equivalent for your balancer).
4. Reload one node. Do not restart. Wait for its health check to pass before you touch the next node.

## 4. Verify

Repeat the step 1 command against each node's address. The new expiry date and the full chain must appear. Load the site in a browser and confirm no warning.

## 5. Roll back

Copy the backup pair over the new files, run the config test, and reload. Roll back node by node, in the same order.
