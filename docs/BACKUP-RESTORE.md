# Backup and restore

## What to back up

The persistent `/data` volume contains:

- `app.db` and SQLite WAL files;
- encrypted application settings;
- retained receipt images and PDFs below `receipts/`.
- locally uploaded product images below `product-images/`.

`APP_SECRET_KEY` is not inside the volume. Back it up separately in a password
manager or secrets system. Without the same key, stored provider and connector
credentials cannot be decrypted.

## Consistent backup

Stop the container briefly or use SQLite's online backup command from a trusted
maintenance container. Copying only `app.db` while writes are active can omit
WAL data.

Recommended simple procedure:

1. stop the Vorrio container;
2. archive the complete data volume;
3. start the container;
4. verify the archive and record the application version;
5. store `APP_SECRET_KEY` separately.

## Restore

1. stop the container;
2. restore the complete volume contents and ownership;
3. restore the matching `APP_SECRET_KEY`;
4. start the same or a newer compatible image;
5. verify login, catalog counts, recent receipts and `/api/health`.

Never merge two SQLite copies by file replacement. The Owner ZIP export added
in 0.8.15 provides readable portability but is intentionally not a database
restore format and excludes all authentication/provider/connector secrets.

## Rotate `APP_SECRET_KEY`

Changing the value without migrating encrypted settings makes saved provider
and connector credentials unreadable. Use the bundled offline rotation tool:

1. make a complete volume backup and stop Vorrio;
2. generate a new secret and keep both values in a protected temporary env
   file or secrets manager;
3. run the same Vorrio image as a one-off maintenance container with the data
   volume, the old value as `APP_SECRET_KEY` and the new value as
   `APP_SECRET_KEY_NEW`:

```bash
docker run --rm \
  --volume vorrio_data:/data \
  --env APP_SECRET_KEY \
  --env APP_SECRET_KEY_NEW \
  --entrypoint python \
  vorrio:0.8.26 /app/scripts/rotate_secret.py
```

4. update the normal deployment's `APP_SECRET_KEY` to the new value;
5. start Vorrio and verify login, settings and connectors;
6. remove the old secret only after the verification succeeds.

The tool verifies decryption with the old key before changing anything, creates
`app.db.backup_before_secret_rotation_<timestamp>` in `/data`, re-encrypts the
settings, marks every server-side browser session revoked and writes an audit
event. Changing the signing key also invalidates every signed cookie by design.
If verification fails, stop and restore
the complete backup; never delete the only working old key.

## Release verification

For 0.8.23 the maintainers test a fresh empty volume, first-run setup, family
invitation and role state, passkey/TOTP/recovery schema, recent-auth state,
API-token creation/scope/revocation state, complete stopped-volume archive,
restore into a second empty volume, SQLite
`PRAGMA integrity_check`, restored Owner/session state and login. The procedure uses
synthetic data and the same production image. The automated launch journey also
covers catalog/barcode creation, reviewed receipt intake, stock, budget,
portable export and the operations projection. Destructive erasure tests use a
separate temporary volume. Operators should still test their own backup
destination and retention policy.
