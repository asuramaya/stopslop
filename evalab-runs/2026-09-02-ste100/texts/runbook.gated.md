**Rotate the TLS certificate on a load balancer**

**1. Detect a near expiry**

Run `echo | openssl s_client -connect lb.example.com:443 2>/dev/null | openssl x509 -noout -enddate`.

The threshold is 30 days. If the end date is less than 30 days away, start this procedure. The daily alert job reports the same date at 08:00 UTC.

**2. Request the replacement**

Generate a new private key: `openssl genrsa -out lb-2026.key 2048`.

Generate the request: `openssl req -new -key lb-2026.key -out lb-2026.csr`.

Send only the `.csr` file to the certificate authority. Keep the private key on the bastion host.

When the certificate arrives, verify that it lists every hostname of the old certificate.

**3. Install**

Upload the certificate chain and the key to the load balancer secret store under a new name.

Attach the new secret to the HTTPS listener. Do not delete the old secret.

Reload the load balancer configuration. A reload keeps live connections. A restart drops them.

**4. Verify**

Repeat the command from step 1. The new end date must appear.

Read the serial number with `openssl x509 -noout -serial`. Compare it against the serial of the issued file.

Send 20 requests through each node behind the virtual IP address. Every node must return the new serial.

Watch the TLS handshake error rate for 15 minutes.

**5. Roll back**

If the error rate rises, or if one node returns the old serial, attach the previous secret to the listener. Reload again.

Verify that the previous serial returns on every node.

Delete the old secret after 7 days of clean operation.
