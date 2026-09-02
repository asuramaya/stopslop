# Runbook: Rotate the TLS Certificate on a Load Balancer

## 1. Find a certificate near expiry

1. Read the current expiry date. Run `echo | openssl s_client -connect lb.example.com:443 2>/dev/null | openssl x509 -noout -enddate -fingerprint`.
2. Compare that date to today's date.
3. The monitor sends an alert at 30 days and again at 7 days.
4. If fewer than 30 days remain, do this procedure.

## 2. Request the replacement

1. On the bastion host, make a new private key and a certificate request (CSR).
2. Send the CSR to the certificate authority. Do not send the private key.
3. When the authority returns the certificate, put the certificate and the intermediate chain into one file.

## 3. Install the replacement

1. Copy the current certificate, chain, and key to `/etc/ssl/backup/`. Record the old fingerprint.
2. Write the new files to `/etc/ssl/certs/` and `/etc/ssl/private/`.
3. Set the key permissions to 0600.
4. Test the configuration with `nginx -t`.
5. Reload the load balancer. Do not restart it. A reload keeps the open connections.
6. Do one node first. Wait 5 minutes before you do the other nodes.

## 4. Verify the change

1. Run the openssl command again against each node.
2. Confirm the new expiry date and the new fingerprint.
3. Send a test request through the public address.
4. Watch the TLS error rate and the 5xx rate for 10 minutes.

## 5. Roll back

1. If the error rate increases, roll back immediately.
2. Copy the backup files into place.
3. Test the configuration and reload the node.
4. Confirm the old fingerprint returns.
5. Record the failure and tell the certificate authority.
